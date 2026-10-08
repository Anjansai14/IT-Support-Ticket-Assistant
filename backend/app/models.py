"""
SQLAlchemy ORM models for database persistence.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class Ticket(Base):
    """
    Ticket database model representing employee IT support requests
    and their automated AI triage metadata.
    """
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_name = Column(String(100), nullable=False)
    employee_email = Column(String(255), nullable=False, index=True)
    issue_description = Column(Text, nullable=False)

    # Fields populated or updated by AI analysis / support engineers
    category = Column(String(50), nullable=True, index=True)
    priority = Column(String(20), nullable=True, index=True)
    issue_type = Column(String(100), nullable=True)
    ai_summary = Column(Text, nullable=True)
    assigned_team = Column(String(50), nullable=True, index=True)

    # Ticket lifecycle state
    status = Column(String(20), nullable=False, default="Open", index=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Ticket(id={self.id}, employee='{self.employee_name}', "
            f"category='{self.category}', priority='{self.priority}', status='{self.status}')>"
        )
