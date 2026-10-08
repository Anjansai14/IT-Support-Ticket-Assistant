"""
REST API endpoints for IT support ticket management (CRUD operations).
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Ticket
from app.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketStatusUpdate,
    TicketResponse,
    TicketStatsResponse,
    TicketCategory,
    TicketPriority,
    SupportTeam,
    TicketStatus
)
from app.services.ai_service import ai_service

logger = logging.getLogger("it-support-ticket-assistant")

router = APIRouter()


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket"
)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a new IT support ticket.
    Validates employee details and issue description, runs automated AI triage,
    and persists the ticket with AI metadata in the database.
    """
    logger.info(f"Creating new ticket for employee: {ticket_in.employee_email}")
    db_ticket = Ticket(
        employee_name=ticket_in.employee_name,
        employee_email=ticket_in.employee_email,
        issue_description=ticket_in.issue_description,
        status=TicketStatus.OPEN.value
    )

    # Perform automated AI triage
    ai_result = ai_service.analyze_ticket(
        employee_name=ticket_in.employee_name,
        employee_email=ticket_in.employee_email,
        issue_description=ticket_in.issue_description,
        allow_fallback=True
    )
    db_ticket.category = ai_result.category.value
    db_ticket.priority = ai_result.priority.value
    db_ticket.assigned_team = ai_result.assigned_team.value
    db_ticket.issue_type = ai_result.issue_type
    db_ticket.ai_summary = ai_result.summary

    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    logger.info(
        f"Ticket #{db_ticket.id} created and triaged successfully as "
        f"[{db_ticket.category} | {db_ticket.priority} | {db_ticket.assigned_team}]."
    )
    return db_ticket


@router.get(
    "",
    response_model=List[TicketResponse],
    summary="Retrieve support tickets"
)
def get_tickets(
    status_filter: Optional[TicketStatus] = Query(None, alias="status", description="Filter by ticket status"),
    category_filter: Optional[TicketCategory] = Query(None, alias="category", description="Filter by category"),
    priority_filter: Optional[TicketPriority] = Query(None, alias="priority", description="Filter by priority"),
    team_filter: Optional[SupportTeam] = Query(None, alias="team", description="Filter by assigned IT support team"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Max tickets to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve tickets with optional filtering by status, category, priority, or team, plus pagination.
    """
    query = db.query(Ticket)

    if status_filter:
        query = query.filter(Ticket.status == status_filter.value)
    if category_filter:
        query = query.filter(Ticket.category == category_filter.value)
    if priority_filter:
        query = query.filter(Ticket.priority == priority_filter.value)
    if team_filter:
        query = query.filter(Ticket.assigned_team == team_filter.value)

    tickets = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()
    return tickets


@router.get(
    "/stats/summary",
    response_model=TicketStatsResponse,
    summary="Get aggregated ticket operations statistics"
)
def get_ticket_statistics(
    db: Session = Depends(get_db)
):
    """
    Retrieve live operational metrics including status counts, priority distribution,
    and team workload breakdowns.
    """
    all_tickets = db.query(Ticket).all()
    total = len(all_tickets)

    by_status = {}
    by_category = {}
    by_team = {}
    by_priority = {}

    for t in all_tickets:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        if t.category:
            by_category[t.category] = by_category.get(t.category, 0) + 1
        if t.assigned_team:
            by_team[t.assigned_team] = by_team.get(t.assigned_team, 0) + 1
        if t.priority:
            by_priority[t.priority] = by_priority.get(t.priority, 0) + 1

    return TicketStatsResponse(
        total_tickets=total,
        open_tickets=by_status.get(TicketStatus.OPEN.value, 0),
        in_progress_tickets=by_status.get(TicketStatus.IN_PROGRESS.value, 0),
        resolved_tickets=by_status.get(TicketStatus.RESOLVED.value, 0),
        closed_tickets=by_status.get(TicketStatus.CLOSED.value, 0),
        critical_tickets=by_priority.get(TicketPriority.CRITICAL.value, 0),
        high_tickets=by_priority.get(TicketPriority.HIGH.value, 0),
        by_category=by_category,
        by_team=by_team,
        by_priority=by_priority
    )


@router.get(
    "/ai/status",
    summary="Check AI integration configuration status"
)
def get_ai_status():
    """
    Check whether the OpenAI service is configured with an active API key.
    """
    return {
        "configured": ai_service.is_configured(),
        "model": ai_service.model
    }


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Retrieve a specific ticket"
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve full details for a single ticket by its unique ID.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID {ticket_id} was not found."
        )
    return ticket


@router.post(
    "/{ticket_id}/analyze",
    response_model=TicketResponse,
    summary="Analyze an existing ticket using AI"
)
def analyze_ticket_endpoint(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """
    Trigger on-demand AI analysis and re-classification for an existing ticket.
    Updates category, priority, summary, issue_type, and assigned_team.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID {ticket_id} was not found."
        )

    ai_result = ai_service.analyze_ticket(
        employee_name=ticket.employee_name,
        employee_email=ticket.employee_email,
        issue_description=ticket.issue_description,
        allow_fallback=True
    )

    ticket.category = ai_result.category.value
    ticket.priority = ai_result.priority.value
    ticket.assigned_team = ai_result.assigned_team.value
    ticket.issue_type = ai_result.issue_type
    ticket.ai_summary = ai_result.summary

    db.commit()
    db.refresh(ticket)
    logger.info(
        f"Ticket #{ticket_id} successfully re-analyzed via AI as "
        f"[{ticket.category} | {ticket.priority} | {ticket.assigned_team}]."
    )
    return ticket


@router.put(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Update a ticket"
)
def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db)
):
    """
    Update details of an existing ticket.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID {ticket_id} was not found."
        )

    update_data = ticket_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(ticket, field):
            setattr(ticket, field, value.value if hasattr(value, "value") else value)

    db.commit()
    db.refresh(ticket)
    logger.info(f"Ticket #{ticket_id} updated successfully.")
    return ticket


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
    summary="Update ticket status"
)
def update_ticket_status(
    ticket_id: int,
    status_update: TicketStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update only the lifecycle status of a ticket (Open, In Progress, Resolved, Closed).
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID {ticket_id} was not found."
        )

    ticket.status = status_update.status.value
    db.commit()
    db.refresh(ticket)
    logger.info(f"Ticket #{ticket_id} status updated to: {ticket.status}")
    return ticket


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a ticket"
)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """
    Permanently delete a ticket by its ID.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID {ticket_id} was not found."
        )

    db.delete(ticket)
    db.commit()
    logger.info(f"Ticket #{ticket_id} deleted successfully.")
    return None
