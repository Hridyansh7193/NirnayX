"""
Feedback Model — User-submitted outcome ratings that feed the RL engine.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Feedback(Base):
    """
    Outcome feedback submitted by users after a case verdict has been implemented.
    This data feeds back into the RL engine as reward signals.
    """
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Feedback data
    outcome_rating = Column(Integer, nullable=False)  # 1-5 scale
    outcome_notes = Column(Text, nullable=True)
    outcome_accuracy = Column(Float, nullable=True)  # 0-1, how accurate was the verdict

    # RL processing status
    rl_processed = Column(Integer, default=0)
    reward_signal = Column(Float, nullable=True)
    weight_updates_applied = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="feedback")
