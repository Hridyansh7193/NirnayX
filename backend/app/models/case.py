"""
Case Model — Core entity representing a decision case submitted for jury evaluation.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class CaseStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    EVALUATED = "evaluated"
    VERDICT_READY = "verdict_ready"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CaseDomain(str, enum.Enum):
    LEGAL = "legal"
    HR = "hr"
    BUSINESS = "business"
    HEALTHCARE = "healthcare"
    POLICY = "policy"
    CUSTOM = "custom"


class Case(Base):
    """A decision case submitted to NirnayX for multi-agent jury evaluation."""
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True) # made nullable=True initially to preserve existing test cases
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)
    domain = Column(SQLEnum(CaseDomain), nullable=False, default=CaseDomain.BUSINESS)
    status = Column(SQLEnum(CaseStatus), nullable=False, default=CaseStatus.DRAFT)

    # Structured data extracted from case
    extracted_entities = Column(JSON, nullable=True)
    key_facts = Column(JSON, nullable=True)
    constraints = Column(JSON, nullable=True)
    s3_facts_pointer = Column(String(500), nullable=True)

    # Metadata
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    version = Column(Integer, default=1)
    parent_case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    is_simulation = Column(Integer, default=0)  # 0 = real, 1 = what-if simulation

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    evaluated_at = Column(DateTime, nullable=True)

    # Relationships
    attachments = relationship("CaseAttachment", back_populates="case", cascade="all, delete-orphan")
    evaluations = relationship("AgentEvaluation", back_populates="case", cascade="all, delete-orphan")
    verdict = relationship("Verdict", back_populates="case", uselist=False, cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="case", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="cases")

    def __repr__(self):
        return f"<Case(id={self.id}, title='{self.title}', domain={self.domain}, status={self.status})>"


class CaseAttachment(Base):
    """File attachments associated with a case (PDFs, documents, etc.)."""
    __tablename__ = "case_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    storage_path = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="attachments")
