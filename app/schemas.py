"""
Pydantic schemas for data validation, serialization, and controlled enums.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class TicketCategory(str, Enum):
    """Controlled categories for IT support tickets."""
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    NETWORK = "Network"
    VPN = "VPN"
    EMAIL = "Email"
    PASSWORD = "Password"
    ACCESS_REQUEST = "Access Request"
    SECURITY = "Security"
    PRINTER = "Printer"
    OTHER = "Other"


class TicketPriority(str, Enum):
    """Controlled priority levels for IT support tickets."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class SupportTeam(str, Enum):
    """Controlled IT support assignment teams."""
    HARDWARE_SUPPORT = "Hardware Support"
    SOFTWARE_SUPPORT = "Software Support"
    NETWORK_SUPPORT = "Network Support"
    ACCESS_MANAGEMENT = "Access Management"
    SECURITY_TEAM = "Security Team"
    EMAIL_SUPPORT = "Email Support"
    GENERAL_IT_SUPPORT = "General IT Support"


class TicketStatus(str, Enum):
    """Controlled lifecycle statuses for IT support tickets."""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class AIAnalysisResult(BaseModel):
    """
    Structured model for AI ticket classification and analysis.
    Enforces predictable JSON output from the LLM.
    """
    category: TicketCategory = Field(
        ...,
        description="Classified ticket category"
    )
    priority: TicketPriority = Field(
        ...,
        description="Calculated ticket priority based on business impact"
    )
    summary: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Concise summary of the employee's issue"
    )
    assigned_team: SupportTeam = Field(
        ...,
        description="Recommended IT team to resolve the ticket"
    )
    issue_type: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Specific problem type (e.g., Connectivity, Authentication)"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Classification confidence score between 0.0 and 1.0"
    )


class TicketBase(BaseModel):
    """Shared base fields across ticket creation and updates."""
    employee_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the employee submitting the ticket",
        examples=["Anjan Sai"]
    )
    employee_email: EmailStr = Field(
        ...,
        description="Corporate email address of the employee",
        examples=["anjan@example.com"]
    )
    issue_description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Detailed description of the IT issue",
        examples=["My laptop is not connecting to the company Wi-Fi."]
    )

    @field_validator("employee_name", "issue_description")
    @classmethod
    def strip_and_check_non_empty(cls, value: str) -> str:
        """Ensure string fields are not purely whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or blank whitespace.")
        return cleaned


class TicketCreate(TicketBase):
    """Request schema for creating a new support ticket."""
    pass


class TicketUpdate(BaseModel):
    """Request schema for updating ticket details."""
    employee_name: Optional[str] = Field(None, min_length=2, max_length=100)
    employee_email: Optional[EmailStr] = None
    issue_description: Optional[str] = Field(None, min_length=10, max_length=2000)
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    assigned_team: Optional[SupportTeam] = None
    issue_type: Optional[str] = Field(None, max_length=100)
    status: Optional[TicketStatus] = None

    @field_validator("employee_name", "issue_description")
    @classmethod
    def strip_optional_strings(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("Updated field cannot be empty whitespace.")
            return cleaned
        return value


class TicketStatusUpdate(BaseModel):
    """Request schema specifically for updating ticket lifecycle status."""
    status: TicketStatus = Field(
        ...,
        description="Updated lifecycle status for the ticket",
        examples=[TicketStatus.IN_PROGRESS]
    )


class TicketResponse(TicketBase):
    """Response schema returning full ticket details to API clients."""
    id: int
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    issue_type: Optional[str] = None
    ai_summary: Optional[str] = None
    assigned_team: Optional[SupportTeam] = None
    status: TicketStatus
    created_at: datetime
    updated_at: datetime

    # Enable ORM mode to serialize directly from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)


class TicketStatsResponse(BaseModel):
    """Aggregated operational statistics and metrics for IT support queues."""
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    critical_tickets: int
    high_tickets: int
    by_category: dict[str, int]
    by_team: dict[str, int]
    by_priority: dict[str, int]
