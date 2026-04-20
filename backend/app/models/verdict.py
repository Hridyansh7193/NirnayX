"""
Verdict Model — The final aggregated verdict and exportable reports.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Verdict(Base):
    """
    The final aggregated verdict for a case.
    Computed from all agent evaluations via the Aggregation Engine.
    """
    __tablename__ = "verdicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, unique=True)

    # Verdict output
    final_verdict = Column(String(50), nullable=False)  # "approve", "reject", "escalate"
    composite_confidence = Column(Float, nullable=False)  # 0-100
    final_score = Column(Float, nullable=False)  # Σ(weight × confidence × decision_value)

    # Aggregation details
    aggregation_mode = Column(String(50), default="weighted_voting")
    agent_count = Column(Integer, nullable=False)
    consensus_level = Column(Float, nullable=False)  # 0-1, fraction of agents agreeing

    # Breakdown
    decision_drivers = Column(JSON, nullable=True)  # Key factors that drove the decision
    dissenting_summary = Column(JSON, nullable=True)  # Agents who disagreed and why
    per_agent_breakdown = Column(JSON, nullable=True)  # Full per-agent results

    # Flags
    requires_human_review = Column(Integer, default=0)
    human_override_applied = Column(Integer, default=0)
    override_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    override_justification = Column(Text, nullable=True)
    override_verdict = Column(String(50), nullable=True)
    override_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="verdict")
    report = relationship("VerdictReport", back_populates="verdict", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Verdict(case={self.case_id}, verdict='{self.final_verdict}', confidence={self.composite_confidence})>"


class VerdictReport(Base):
    """
    The explainability report generated for a verdict.
    Contains human-readable reasoning chains and exportable content.
    """
    __tablename__ = "verdict_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    verdict_id = Column(UUID(as_uuid=True), ForeignKey("verdicts.id"), nullable=False, unique=True)

    # Report content
    summary = Column(Text, nullable=False)
    detailed_reasoning = Column(JSON, nullable=False)  # Full reasoning chain per agent
    confidence_analysis = Column(JSON, nullable=True)
    recommendation_text = Column(Text, nullable=True)

    # Export tracking
    pdf_generated = Column(Integer, default=0)
    pdf_path = Column(String(1000), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    verdict = relationship("Verdict", back_populates="report")
