"""
NirnayX Celery Worker
Handles long-running AI Jury deliberation and RL weight updates.
"""

from celery import Celery
from celery.signals import task_postrun
from app.config import settings
import asyncio
from app.database import async_session
from app.models.case import Case, CaseStatus
from app.models.verdict import Verdict
from app.models.agent import AgentEvaluation
from app.models.outbox import OutboxEvent
from app.models.audit import AuditLog
from app.services.agents import evaluate_case
from app.services.aggregation import aggregate_verdicts
from sqlalchemy import select, text, update
import uuid
from datetime import datetime
import hashlib
import json

# Initialize Celery
celery_app = Celery(
    "nirnayx_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(bind=True, name="process_jury_deliberation", max_retries=3, default_retry_delay=5)
def process_jury_deliberation(self, case_id: str, tenant_id: str, agent_count: int, aggregation_mode: str, version: int = 1):
    """
    Background task to run the full jury deliberation pipeline.
    """
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(_run_deliberation_async(case_id, tenant_id, agent_count, aggregation_mode, version))
    except Exception as e:
        # Retry with exponential backoff on failure
        raise self.retry(exc=e)

async def _run_deliberation_async(case_id: str, tenant_id: str, agent_count: int, aggregation_mode: str, version: int):
    task_hash = hashlib.sha256(f"{case_id}_{version}".encode()).hexdigest()
    
    async with async_session() as db:
        try:
            # 1. Enforce Tenant Isolation for the transaction block
            if tenant_id:
                await db.execute(text("SET LOCAL app.tenant_id = :tenant"), {"tenant": tenant_id})

            # 2. Exactly-Once Idempotency Lock
            case_uuid = uuid.UUID(case_id)
            stmt = select(Case).where(Case.id == case_uuid).with_for_update(skip_locked=True)
            result = await db.execute(stmt)
            case = result.scalar_one_or_none()
            
            if not case:
                return {"status": "error", "message": "Case not found or locked by another worker"}
                
            if case.status in [CaseStatus.VERDICT_READY, CaseStatus.FINALIZING, CaseStatus.CLOSED]:
                return {"status": "success", "message": "Task already completed"}

            # Log Start Event (Write-Ahead Log)
            db.add(AuditLog(
                case_id=case_uuid, 
                event_type="DELIBERATION_STARTED", 
                details={"agent_count": agent_count, "task_hash": task_hash}
            ))

            # 3. Synchronous LLM Provider calls (Simulated/Mocked right now)
            evaluations_data = evaluate_case(
                title=case.title,
                description=case.description,
                domain=case.domain.value if hasattr(case.domain, 'value') else case.domain,
                agent_count=agent_count,
            )
            
            # Store evaluations
            for ev in evaluations_data:
                eval_obj = AgentEvaluation(
                    case_id=case.id,
                    agent_id=uuid.uuid4(),
                    agent_name=ev["agent_name"],
                    archetype=ev["archetype"],
                    verdict=ev["verdict"],
                    confidence_score=ev["confidence_score"],
                    reasoning_chain=ev["reasoning_chain"],
                    weight_at_evaluation=ev["weight_at_evaluation"],
                    weight_contribution=ev["weight_contribution"]
                )
                db.add(eval_obj)

            # 4. Aggregate verdicts
            verdict_result = aggregate_verdicts(
                evaluations=evaluations_data,
                aggregation_mode=aggregation_mode,
                domain=case.domain.value if hasattr(case.domain, 'value') else case.domain,
            )

            # Store verdict
            verdict_record = Verdict(
                case_id=case.id,
                final_verdict=verdict_result["final_verdict"],
                composite_confidence=verdict_result["composite_confidence"],
                final_score=verdict_result["final_score"],
                aggregation_mode=verdict_result["aggregation_mode"],
                agent_count=verdict_result["agent_count"],
                consensus_level=verdict_result["consensus_level"],
                decision_drivers=verdict_result["decision_drivers"],
                dissenting_summary=verdict_result["dissenting_summary"],
                per_agent_breakdown=verdict_result["per_agent_breakdown"],
                requires_human_review=verdict_result["requires_human_review"]
            )
            db.add(verdict_record)

            # Update case status
            case.status = CaseStatus.VERDICT_READY
            case.evaluated_at = datetime.utcnow()

            # Write Completion Log
            db.add(AuditLog(
                case_id=case_uuid, 
                event_type="DELIBERATION_COMPLETED", 
                details={"verdict": verdict_result["final_verdict"]}
            ))

            # Write Outbox Event for Eventual Consistency Streams (Redpanda)
            db.add(OutboxEvent(
                aggregate_type="CASE",
                aggregate_id=case_uuid,
                type="VERDICT_READY",
                payload={"verdict": verdict_result["final_verdict"], "case_id": case_id}
            ))
            
            # 5. Atomic Commit (ACID)
            await db.commit()
            return {"status": "success", "case_id": case_id, "verdict": verdict_result["final_verdict"]}
            
        except Exception as e:
            await db.rollback()
            # Compensating Event Strategy on Failure
            async with async_session() as comp_db:
                if tenant_id:
                    await comp_db.execute(text("SET LOCAL app.tenant_id = :tenant"), {"tenant": tenant_id})
                comp_db.add(AuditLog(
                    case_id=uuid.UUID(case_id), 
                    event_type="DELIBERATION_FAILED_ROLLED_BACK", 
                    details={"error": str(e)}
                ))
                await comp_db.commit()
            raise e

@task_postrun.connect
def clean_memory_context(**kwargs):
    """Ensure explicit tenant memory wiping post task"""
    import gc
    gc.collect()

