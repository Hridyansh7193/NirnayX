from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.feedback import Feedback
from app.models.case import Case, CaseStatus
from app.models.agent import AgentEvaluation
from app.models.audit import AuditLog
from app.schemas import FeedbackCreate, FeedbackResponse
from app.services.rl_engine import rl_engine
from typing import List
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(feedback_data: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    """
    Submit outcome feedback for a closed case.
    This triggers the RL engine to update agent weights.
    """
    case_uuid = uuid.UUID(str(feedback_data.case_id))
    result = await db.execute(select(Case).filter(Case.id == case_uuid))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Fetch evaluations from DB
    eval_result = await db.execute(select(AgentEvaluation).filter(AgentEvaluation.case_id == case_uuid))
    evaluations = eval_result.scalars().all()
    
    # Simple conversion to dict for RL engine (prototype phase)
    eval_dicts = [
        {
            "archetype": ev.archetype,
            "verdict": ev.verdict,
            "confidence_score": ev.confidence_score,
            "weight_at_evaluation": ev.weight_at_evaluation
        } for ev in evaluations
    ]

    # Compute reward signal
    reward_signal = rl_engine.compute_reward_signal(
        outcome_rating=feedback_data.outcome_rating,
        agent_evaluations=eval_dicts,
    )

    # Update agent weights via RL engine
    current_weights = {ev.archetype: ev.weight_at_evaluation for ev in evaluations}
    
    updated_weights, update_details = rl_engine.update_weights(
        current_weights=current_weights,
        agent_evaluations=eval_dicts,
        reward_signal=reward_signal,
        domain=case.domain.value if hasattr(case.domain, 'value') else case.domain,
    )

    # Store feedback
    feedback_record = Feedback(
        case_id=case.id,
        outcome_rating=feedback_data.outcome_rating,
        outcome_notes=feedback_data.outcome_notes,
        rl_processed=1,
        reward_signal=reward_signal,
        weight_updates_applied=update_details
    )
    db.add(feedback_record)

    # Update case status to closed
    case.status = CaseStatus.CLOSED

    # Audit log
    db.add(AuditLog(
        action="feedback_submitted", 
        entity_type="feedback", 
        entity_id=str(case.id),
        details={
            "rating": feedback_data.outcome_rating,
            "reward_signal": reward_signal,
        },
    ))

    await db.commit()
    await db.refresh(feedback_record)
    return feedback_record


@router.get("", response_model=List[FeedbackResponse])
async def list_feedback(db: AsyncSession = Depends(get_db)):
    """List all feedback entries from the database."""
    query = select(Feedback).order_by(Feedback.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

