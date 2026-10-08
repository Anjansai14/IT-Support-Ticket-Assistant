"""
Automated unit and integration tests for IT Support Ticket Assistant.
Includes database isolation, mock OpenAI integration, validation, and full CRUD workflows.
"""
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.schemas import TicketStatus, TicketCategory, TicketPriority, SupportTeam


def test_health_check(client: TestClient):
    """Verify application health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_create_ticket_success(client: TestClient):
    """Verify creating a support ticket with automated triage."""
    payload = {
        "employee_name": "Anjan Sai",
        "employee_email": "anjan@example.com",
        "issue_description": "My laptop cannot connect to the company VPN. I need access to the internal server."
    }
    response = client.post("/tickets", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["employee_name"] == "Anjan Sai"
    assert data["employee_email"] == "anjan@example.com"
    assert data["status"] == TicketStatus.OPEN.value
    assert data["category"] == TicketCategory.VPN.value
    assert data["priority"] == TicketPriority.HIGH.value
    assert data["assigned_team"] == SupportTeam.NETWORK_SUPPORT.value
    assert data["ai_summary"] is not None


def test_get_tickets_list(client: TestClient):
    """Verify retrieving list of tickets with pagination."""
    client.post("/tickets", json={
        "employee_name": "Alice",
        "employee_email": "alice@example.com",
        "issue_description": "My monitor display is flickering and going dark."
    })
    client.post("/tickets", json={
        "employee_name": "Bob",
        "employee_email": "bob@example.com",
        "issue_description": "Cannot connect to the office Wi-Fi network."
    })

    response = client.get("/tickets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_ticket_by_id_success(client: TestClient):
    """Verify retrieving a single ticket by its primary key ID."""
    created = client.post("/tickets", json={
        "employee_name": "Charlie",
        "employee_email": "charlie@example.com",
        "issue_description": "Need access permissions to the internal analytics dashboard."
    }).json()

    ticket_id = created["id"]
    response = client.get(f"/tickets/{ticket_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == ticket_id
    assert data["employee_name"] == "Charlie"


def test_get_ticket_not_found(client: TestClient):
    """Verify requesting a non-existent ticket returns HTTP 404."""
    response = client.get("/tickets/999999")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "HTTP_404"
    assert "not found" in data["detail"].lower()


def test_update_ticket(client: TestClient):
    """Verify updating ticket fields via PUT /tickets/{id}."""
    created = client.post("/tickets", json={
        "employee_name": "David",
        "employee_email": "david@example.com",
        "issue_description": "My keyboard spacebar is jammed."
    }).json()

    ticket_id = created["id"]
    update_payload = {
        "issue_description": "Updated: Spacebar and Enter keys are both completely jammed."
    }
    response = client.put(f"/tickets/{ticket_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert "Enter keys" in data["issue_description"]


def test_update_ticket_status(client: TestClient):
    """Verify dedicated status transition endpoint PATCH /tickets/{id}/status."""
    created = client.post("/tickets", json={
        "employee_name": "Eva",
        "employee_email": "eva@example.com",
        "issue_description": "Password expired and locked out of corporate laptop."
    }).json()

    ticket_id = created["id"]
    response = client.patch(f"/tickets/{ticket_id}/status", json={"status": "In Progress"})
    assert response.status_code == 200
    assert response.json()["status"] == TicketStatus.IN_PROGRESS.value

    # Transition to Resolved
    response = client.patch(f"/tickets/{ticket_id}/status", json={"status": "Resolved"})
    assert response.status_code == 200
    assert response.json()["status"] == TicketStatus.RESOLVED.value


def test_delete_ticket(client: TestClient):
    """Verify deleting a ticket returns HTTP 204 and subsequent queries 404."""
    created = client.post("/tickets", json={
        "employee_name": "Frank",
        "employee_email": "frank@example.com",
        "issue_description": "Temporary test ticket for deletion verification."
    }).json()

    ticket_id = created["id"]
    del_response = client.delete(f"/tickets/{ticket_id}")
    assert del_response.status_code == 204

    # Subsequent GET must return 404
    get_response = client.get(f"/tickets/{ticket_id}")
    assert get_response.status_code == 404


def test_validation_error_invalid_email(client: TestClient):
    """Verify invalid email syntax is rejected with HTTP 422."""
    bad_payload = {
        "employee_name": "Grace",
        "employee_email": "not-a-valid-email",
        "issue_description": "My mouse pointer is jumping uncontrollably."
    }
    response = client.post("/tickets", json=bad_payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert any("email" in err["field"].lower() for err in data["errors"])


def test_validation_error_short_description(client: TestClient):
    """Verify descriptions under 10 characters are rejected with HTTP 422."""
    short_payload = {
        "employee_name": "Grace",
        "employee_email": "grace@example.com",
        "issue_description": "Too short"
    }
    response = client.post("/tickets", json=short_payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert any("issue_description" in err["field"].lower() for err in data["errors"])


def test_team_queue_filtering(client: TestClient):
    """Verify filtering tickets by assigned support team."""
    client.post("/tickets", json={
        "employee_name": "Network User",
        "employee_email": "net@example.com",
        "issue_description": "Office Wi-Fi signal is dropping frequently."
    })
    client.post("/tickets", json={
        "employee_name": "Hardware User",
        "employee_email": "hw@example.com",
        "issue_description": "Docking station is not charging my laptop battery."
    })

    response = client.get("/tickets?team=Network Support")
    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) >= 1
    assert all(t["assigned_team"] == SupportTeam.NETWORK_SUPPORT.value for t in tickets)


def test_operational_statistics(client: TestClient):
    """Verify GET /tickets/stats/summary aggregates live metrics accurately."""
    client.post("/tickets", json={
        "employee_name": "Security User",
        "employee_email": "sec@example.com",
        "issue_description": "Received suspicious phishing email asking for credentials."
    })

    response = client.get("/tickets/stats/summary")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_tickets"] >= 1
    assert "by_team" in stats
    assert "by_category" in stats
    assert "by_priority" in stats


def test_mocked_openai_triage(client: TestClient):
    """
    Test OpenAI integration by mocking the OpenAI client API call.
    Verifies that real network requests are NOT made and LLM JSON output is parsed cleanly.
    """
    mock_llm_json = json.dumps({
        "category": "Security",
        "priority": "Critical",
        "summary": "Urgent cybersecurity incident involving suspected malware on corporate endpoint.",
        "assigned_team": "Security Team",
        "issue_type": "Malware Incident",
        "confidence": 0.98
    })

    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = mock_llm_json
    mock_response.choices = [mock_choice]

    with patch("app.services.ai_service.ai_service.is_configured", return_value=True):
        with patch("app.services.ai_service.ai_service.get_client") as mock_get_client:
            mock_client_instance = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client_instance

            response = client.post("/tickets", json={
                "employee_name": "IT Lead",
                "employee_email": "lead@example.com",
                "issue_description": "Critical malware alert detected on executive machine."
            })

            assert response.status_code == 201
            ticket = response.json()
            assert ticket["category"] == "Security"
            assert ticket["priority"] == "Critical"
            assert ticket["assigned_team"] == "Security Team"
            assert ticket["issue_type"] == "Malware Incident"
            assert "malware" in ticket["ai_summary"].lower()

            # Verify that OpenAI chat completions was called with structured instructions
            mock_client_instance.chat.completions.create.assert_called_once()
