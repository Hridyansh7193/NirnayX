"""
Pydantic Schemas — Request/Response models for all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ─── Enums ─────────────────────────────────────────────

class CaseDomainEnum(str, Enum):
    LEGAL = "legal"
    HR = "hr"
    BUSINESS = "business"
    HEALTHCARE = "healthcare"
    POLICY = "policy"
    CUSTOM = "custom"


class CaseStatusEnum(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    EVALUATED = "evaluated"
    VERDICT_READY = "verdict_ready"
    CLOSED = "closed"
    ARCHIVED = "archived"


class AggregationModeEnum(str, Enum):
    WEIGHTED_VOTING = "weighted_voting"
    CONFIDENCE_WEIGHTED_AVERAGE = "confidence_weighted_average"
    SUPERMAJORITY_THRESHOLD = "supermajority_threshold"


class VerdictEnum(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    DEFER = "defer"


# ─── User Schemas ──────────────────────────────────────

class UserCreate(BaseModel):
    email: str = Field(..., max_length=320)
    full_name: str = Field(..., max_length=200)
    password: str = Field(..., min_length=8)
    role: str = "analyst"
    organization: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    organization: Optional[str]
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─── Case Schemas ──────────────────────────────────────

class CaseCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: str = Field(..., min_length=10)
    domain: CaseDomainEnum = CaseDomainEnum.BUSINESS
    extracted_entities: Optional[Dict[str, Any]] = None
    key_facts: Optional[List[str]] = None
    constraints: Optional[List[str]] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[CaseDomainEnum] = None
    extracted_entities: Optional[Dict[str, Any]] = None
    key_facts: Optional[List[str]] = None
    constraints: Optional[List[str]] = None


class CaseResponse(BaseModel):
    id: UUID
    title: str
    description: str
    domain: str
    status: str
    extracted_entities: Optional[Dict[str, Any]]
    key_facts: Optional[Any]
    constraints: Optional[Any]
    owner_id: Optional[UUID]
    version: int
    is_simulation: int
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    evaluated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CaseSubmit(BaseModel):
    """Submit a case for jury evaluation."""
    agent_count: int = Field(default=5, ge=3, le=15)
    aggregation_mode: AggregationModeEnum = AggregationModeEnum.WEIGHTED_VOTING


# ─── Agent Schemas ─────────────────────────────────────

class AgentProfileResponse(BaseModel):
    id: UUID
    name: str
    archetype: str
    description: Optional[str]
    base_weight: float
    current_weight: float
    domain: Optional[str]
    total_evaluations: int
    accuracy_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class AgentEvaluationResponse(BaseModel):
    id: UUID
    case_id: UUID
    agent_id: UUID
    verdict: str
    confidence_score: float
    decision_value: float
    reasoning_chain: Any
    weight_at_evaluation: float
    weight_contribution: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Verdict Schemas ───────────────────────────────────

class VerdictResponse(BaseModel):
    id: UUID
    case_id: UUID
    final_verdict: str
    composite_confidence: float
    final_score: float
    aggregation_mode: str
    agent_count: int
    consensus_level: float
    decision_drivers: Optional[Any]
    dissenting_summary: Optional[Any]
    per_agent_breakdown: Optional[Any]
    requires_human_review: int
    human_override_applied: int
    override_justification: Optional[str]
    override_verdict: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class HumanOverrideRequest(BaseModel):
    """Request to override a system verdict."""
    action: str = Field(..., pattern="^(accept|reject|modify)$")
    override_verdict: Optional[VerdictEnum] = None
    justification: str = Field(..., min_length=50)


# ─── Feedback Schemas ──────────────────────────────────

class FeedbackCreate(BaseModel):
    case_id: UUID
    outcome_rating: int = Field(..., ge=1, le=5)
    outcome_notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: UUID
    case_id: UUID
    outcome_rating: int
    outcome_notes: Optional[str]
    rl_processed: int
    reward_signal: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Domain Profile Schemas ────────────────────────────

class DomainProfileCreate(BaseModel):
    name: str = Field(..., max_length=200)
    domain_key: str = Field(..., max_length=50)
    description: Optional[str] = None
    aggregation_mode: AggregationModeEnum = AggregationModeEnum.WEIGHTED_VOTING
    agent_count: int = Field(default=5, ge=3, le=15)
    requires_human_review: int = 0
    disclaimer_text: Optional[str] = None


class DomainProfileResponse(BaseModel):
    id: UUID
    name: str
    domain_key: str
    description: Optional[str]
    aggregation_mode: str
    agent_count: int
    requires_human_review: int
    max_weight_per_agent: float
    disclaimer_text: Optional[str]
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Audit Log Schemas ─────────────────────────────────

class AuditLogResponse(BaseModel):
    id: UUID
    action: str
    entity_type: str
    entity_id: Optional[str]
    actor_id: Optional[str]
    actor_email: Optional[str]
    details: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Dashboard / Analytics ─────────────────────────────

class DashboardStats(BaseModel):
    total_cases: int
    cases_by_status: Dict[str, int]
    cases_by_domain: Dict[str, int]
    average_confidence: float
    average_consensus: float
    total_verdicts: int
    human_overrides: int
    total_feedback: int
    average_rating: float
    agent_performance: List[Dict[str, Any]]


class RLTelemetry(BaseModel):
    """RL engine telemetry data."""
    total_feedback_cycles: int
    reward_curve: List[Dict[str, float]]
    agent_weight_history: List[Dict[str, Any]]
    convergence_status: str
    last_update: Optional[datetime]
