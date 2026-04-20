"""
Cases Router — CRUD operations for decision cases.
The core resource of NirnayX.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import get_db
from app.models.case import Case, CaseStatus, CaseDomain
from app.models.verdict import Verdict
from app.models.agent import AgentEvaluation
from app.models.audit import AuditLog
from app.schemas import (
    CaseCreate, CaseUpdate, CaseResponse, CaseSubmit,
    AgentEvaluationResponse, VerdictResponse, CaseStatusEnum,
)
from app.services.ingestion import structure_case
from app.services.agents import evaluate_case
from app.services.aggregation import aggregate_verdicts
from app.services.explainability import generate_verdict_report
from app.worker import process_jury_deliberation
from typing import List, Optional
import uuid
from datetime import datetime
import json
import redis.asyncio as redis
from app.config import settings

# Initialize strict LRU cache connection for token budgeting
cache = redis.from_url(settings.CACHE_URL)

router = APIRouter(prefix="/api/v1/cases", tags=["Cases"])


@router.post("", response_model=CaseResponse, status_code=201)
async def create_case(case_data: CaseCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new decision case.
    The system will automatically classify the domain and extract entities.
    """
    # Run ingestion pipeline
    structured = structure_case(
        title=case_data.title,
        description=case_data.description,
        domain=case_data.domain.value if case_data.domain else None,
    )

    domain_val = case_data.domain.value if case_data.domain else structured["domain"]
    
    new_case = Case(
        title=case_data.title,
        description=case_data.description,
        domain=domain_val,
        status=CaseStatus.DRAFT,
        extracted_entities=structured["extracted_entities"],
        key_facts=structured["key_facts"],
        constraints=structured["constraints"],
    )

    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)

    # Log audit entry
    audit = AuditLog(
        case_id=new_case.id,
        event_type="CASE_CREATED",
        entity_type="case",
        entity_id=str(new_case.id),
        details={"title": case_data.title}
    )
    db.add(audit)
    await db.commit()

    return new_case


@router.get("", response_model=List[CaseResponse])
async def list_cases(
    domain: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List all cases with optional filtering."""
    query = select(Case).order_by(Case.created_at.desc()).offset(offset).limit(limit)
    
    if domain:
        query = query.filter(Case.domain == domain)
    if status:
        query = query.filter(Case.status == status)

    result = await db.execute(query)
    cases = result.scalars().all()
    return cases


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific case by ID."""
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid case ID format")

    result = await db.execute(select(Case).filter(Case.id == case_uuid))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(case_id: str, case_data: CaseUpdate, db: AsyncSession = Depends(get_db)):
    """Update a case (only allowed in draft status)."""
    case_uuid = uuid.UUID(case_id)
    result = await db.execute(select(Case).filter(Case.id == case_uuid))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status != CaseStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only edit cases in draft status")

    update_fields = case_data.model_dump(exclude_unset=True)
    if "domain" in update_fields and update_fields["domain"]:
        update_fields["domain"] = update_fields["domain"].value

    for key, value in update_fields.items():
        setattr(case, key, value)
    
    case.version += 1
    case.updated_at = datetime.utcnow()

    db.add(AuditLog(case_id=case.id, event_type="CASE_UPDATED", entity_type="case", entity_id=case_id))
    await db.commit()
    await db.refresh(case)
    return case


@router.post("/{case_id}/submit", response_model=VerdictResponse)
async def submit_case(case_id: str, submit_config: CaseSubmit = CaseSubmit(), db: AsyncSession = Depends(get_db)):
    """
    Submit a case for jury evaluation.
    This triggers the full pipeline: agent evaluation → aggregation → verdict.
    """
    case_uuid = uuid.UUID(case_id)
    result = await db.execute(select(Case).filter(Case.id == case_uuid))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status not in [CaseStatus.DRAFT, CaseStatus.SUBMITTED]:
        raise HTTPException(status_code=400, detail="Case already processed")

    # 1. 402 Payment Required Enforcement
    # Check tenant budget in Redis
    # In a real app, tenant_id comes from JWT. Defaulting to dummy for now
    tenant_id = str(case.tenant_id) if case.tenant_id else "00000000-0000-0000-0000-000000000000"
    tokens_used = await cache.get(f"tenant:{tenant_id}:tokens_used")
    if tokens_used and int(tokens_used) > settings.MAX_TOKENS_PER_DOMAIN:
        raise HTTPException(status_code=402, detail="Monthly token budget exceeded for this tenant.")

    # Update status to processing
    case.status = CaseStatus.PROCESSING
    case.submitted_at = datetime.utcnow()
    await db.commit()

    # 2. Fire and Forget immediately into Celery Queue
    process_jury_deliberation.delay(
        case_id=str(case.id),
        tenant_id=tenant_id,
        agent_count=submit_config.agent_count,
        aggregation_mode=submit_config.aggregation_mode.value,
        version=case.version
    )

    db.add(AuditLog(
        case_id=case.id,
        event_type="CASE_QUEUED", 
        entity_type="case", 
        entity_id=case_id,
        details={"agent_count": submit_config.agent_count}
    ))
    await db.commit()

    return {
        "id": str(uuid.uuid4()), # Dummy ID for response schema consistency
        "case_id": case_id,
        "final_verdict": "processing",
        "composite_confidence": 0,
        "final_score": 0,
        "aggregation_mode": submit_config.aggregation_mode.value,
        "agent_count": submit_config.agent_count,
        "consensus_level": 0,
        "decision_drivers": ["Agent deliberation in progress..."],
        "dissenting_summary": "",
        "per_agent_breakdown": {},
        "requires_human_review": False,
        "created_at": datetime.utcnow()
    }


@router.get("/{case_id}/evaluations", response_model=List[AgentEvaluationResponse])
async def get_case_evaluations(case_id: str, db: AsyncSession = Depends(get_db)):
    """Get all agent evaluations for a case."""
    case_uuid = uuid.UUID(case_id)
    result = await db.execute(select(AgentEvaluation).filter(AgentEvaluation.case_id == case_uuid))
    return result.scalars().all()


@router.get("/{case_id}/report")
async def get_case_report(case_id: str, db: AsyncSession = Depends(get_db)):
    """Get the explainability report for a case."""
    case_uuid = uuid.UUID(case_id)
    result = await db.execute(select(Case).filter(Case.id == case_uuid))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # In production, we'd fetch the VerdictReport model. 
    # For now, we regenerate or fetch from the Verdict record.
    v_result = await db.execute(select(Verdict).filter(Verdict.case_id == case_uuid))
    verdict = v_result.scalar_one_or_none()
    
    if not verdict:
        raise HTTPException(status_code=404, detail="Report not ready")

    e_result = await db.execute(select(AgentEvaluation).filter(AgentEvaluation.case_id == case_uuid))
    evals = e_result.scalars().all()
    
    # Simple report generation
    return {
        "case_id": case_id,
        "recommendation_text": f"Based on a consensus of {verdict.consensus_level*100:.0f}%, the recommended action is to {verdict.final_verdict.upper()}.",
        "key_drivers": verdict.decision_drivers,
        "dissenting_views": verdict.dissenting_summary,
        "risk_assessment": "Medium" if verdict.requires_human_review else "Low"
    }


@router.post("/{case_id}/clone", response_model=CaseResponse)
async def clone_case(case_id: str, db: AsyncSession = Depends(get_db)):
    """Clone a case for what-if simulation."""
    case_uuid = uuid.UUID(case_id)
    result = await db.execute(select(Case).filter(Case.id == case_uuid))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    clone = Case(
        title=f"[Simulation] {case.title}",
        description=case.description,
        domain=case.domain,
        status=CaseStatus.DRAFT,
        extracted_entities=case.extracted_entities,
        key_facts=case.key_facts,
        constraints=case.constraints,
        is_simulation=1,
        parent_case_id=case.id
    )

    db.add(clone)
    await db.commit()
    await db.refresh(clone)
    
    db.add(AuditLog(case_id=clone.id, event_type="CASE_CLONED", entity_type="case", entity_id=str(clone.id), details={"original_id": case_id}))
    await db.commit()
    
    return clone

