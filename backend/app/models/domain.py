"""
Domain Profile Model — Configurable domain-specific settings for different verticals.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class DomainProfile(Base):
    """
    Domain configuration profiles for different industry verticals.
    Each domain can have custom agent personas, reward functions, and aggregation modes.
    """
    __tablename__ = "domain_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    domain_key = Column(String(50), nullable=False, unique=True)  # "legal", "hr", "healthcare"
    description = Column(Text, nullable=True)

    # Configuration
    agent_personas = Column(JSON, nullable=True)  # Custom agent configs for this domain
    reward_function = Column(JSON, nullable=True)  # Reward function parameters
    aggregation_mode = Column(String(50), default="weighted_voting")
    agent_count = Column(Integer, default=5)

    # Guardrails
    requires_human_review = Column(Integer, default=0)
    max_weight_per_agent = Column(Float, default=0.35)  # No agent > 35% weight
    disclaimer_text = Column(Text, nullable=True)

    # Status
    is_active = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DomainProfile(name='{self.name}', domain_key='{self.domain_key}')>"
