from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.verdict import Verdict
from app.models.case import Case, CaseStatus
from app.models.audit import AuditLog
from app.schemas import VerdictResponse, HumanOverrideRequest
from datetime import datetime
from typing import List
import uuid

router = APIRouter(prefix="/api/v1/verdicts", tags=["Verdicts"])


@router.get("", response_model=List[VerdictResponse])
async def list_verdicts(db: AsyncSession = Depends(get_db)):
    """List all verdicts from the database."""
    query = select(Verdict).order_by(Verdict.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{case_id}", response_model=VerdictResponse)
async def get_verdict(case_id: str, db: AsyncSession = Depends(get_db)):
    """Get the verdict for a specific case."""
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid case ID format")

    result = await db.execute(select(Verdict).filter(Verdict.case_id == case_uuid))
    verdict = result.scalar_one_or_none()
    
    if not verdict:
        raise HTTPException(status_code=404, detail="Verdict not found for this case")
    return verdict


@router.post("/{case_id}/override", response_model=VerdictResponse)
async def human_override(case_id: str, override_req: HumanOverrideRequest, db: AsyncSession = Depends(get_db)):
    """
    Apply a human override to a system verdict.
    FR-09.1: Human reviewers can override, accept, or reject any system verdict.
    FR-09.3: All overrides logged with reviewer identity and timestamp.
    """
    case_uuid = uuid.UUID(case_id)
    result = await db.execute(select(Verdict).filter(Verdict.case_id == case_uuid))
    verdict = result.scalar_one_or_none()
    
    if not verdict:
        raise HTTPException(status_code=404, detail="Verdict not found")

    # Apply override
    verdict.human_override_applied = 1
    verdict.override_justification = override_req.justification
    verdict.updated_at = datetime.utcnow()

    if override_req.action == "accept":
        pass
    elif override_req.action == "reject":
        verdict.override_verdict = "rejected_by_reviewer"
    elif override_req.action == "modify" and override_req.override_verdict:
        verdict.override_verdict = override_req.override_verdict.value
        verdict.final_verdict = override_req.override_verdict.value

    # Update case status to closed
    res_case = await db.execute(select(Case).filter(Case.id == case_uuid))
    case = res_case.scalar_one_or_none()
    if case:
        case.status = CaseStatus.CLOSED

    # Audit log
    db.add(AuditLog(
        action="verdict_overridden", 
        entity_type="verdict", 
        entity_id=case_id,
        details={
            "action": override_req.action,
            "justification": override_req.justification,
            "override_verdict": override_req.override_verdict.value if override_req.override_verdict else None,
        },
    ))

    await db.commit()
    await db.refresh(verdict)
    return verdict

