"""
Agent Model — Juror agent profiles and their per-case evaluations.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class AgentProfile(Base):
    """
    A juror agent archetype definition.
    Each agent has a reasoning persona, a base weight, and domain-specific configuration.
    """
    __tablename__ = "agent_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    archetype = Column(String(200), nullable=False)  # e.g., "Risk Analyst", "Ethical Reviewer"
    description = Column(Text, nullable=True)
    reasoning_priors = Column(JSON, nullable=True)  # Configurable reasoning biases/focus areas
    base_weight = Column(Float, default=1.0)
    current_weight = Column(Float, default=1.0)
    domain = Column(String(100), nullable=True)  # Domain specialization

    # RL-tracked metrics
    total_evaluations = Column(Integer, default=0)
    accuracy_score = Column(Float, default=0.5)  # Running accuracy
    weight_history = Column(JSON, default=list)  # Historical weight changes

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    evaluations = relationship("AgentEvaluation", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AgentProfile(name='{self.name}', archetype='{self.archetype}', weight={self.current_weight})>"


class AgentEvaluation(Base):
    """
    A single agent's evaluation of a specific case.
    Contains the agent's verdict, confidence score, and reasoning chain.
    """
    __tablename__ = "agent_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False)

    # Agent's output
    verdict = Column(String(50), nullable=False)  # "approve", "reject", "escalate", "defer"
    confidence_score = Column(Float, nullable=False)  # 0-100
    decision_value = Column(Float, nullable=False)  # Numeric decision value for aggregation
    reasoning_chain = Column(JSON, nullable=False)  # Structured reasoning steps

    # Weight at time of evaluation (snapshot)
    weight_at_evaluation = Column(Float, nullable=False)
    weight_contribution = Column(Float, nullable=True)  # Computed: weight * confidence * decision_value

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="evaluations")
    agent = relationship("AgentProfile", back_populates="evaluations")

    def __repr__(self):
        return f"<AgentEvaluation(agent={self.agent_id}, verdict='{self.verdict}', confidence={self.confidence_score})>"
