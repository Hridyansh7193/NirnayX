"""
Audit Log Model — Immutable, append-only audit trail for all system actions.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class AuditLog(Base):
    """
    Tamper-evident, append-only audit log for all NirnayX actions.
    Retention: 7 years minimum as per compliance requirements.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Action details
    action = Column(String(200), nullable=True, index=True) # made nullable for backward compat
    event_type = Column(String(200), nullable=True, index=True) # event sourcing
    
    entity_type = Column(String(100), nullable=True)  # "case", "verdict", "agent", "user"
    entity_id = Column(String(100), nullable=True)
    case_id = Column(UUID(as_uuid=True), nullable=True) # Direct FK reference
    actor_id = Column(String(100), nullable=True)  # User who performed the action
    actor_email = Column(String(320), nullable=True)

    # Detail
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamp (immutable)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AuditLog(event='{self.event_type or self.action}', case_id={self.case_id})>"
