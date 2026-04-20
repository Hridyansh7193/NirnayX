from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models.case import Case
from app.models.verdict import Verdict
from app.models.feedback import Feedback
from app.models.agent import AgentEvaluation
from app.models.audit import AuditLog
from app.schemas import DashboardStats, AuditLogResponse
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get comprehensive dashboard statistics using SQL aggregation."""
    
    # 1. Basic Stats
    case_count = await db.scalar(select(func.count(Case.id)))
    verdict_count = await db.scalar(select(func.count(Verdict.id)))
    feedback_count = await db.scalar(select(func.count(Feedback.id)))
    
    # 2. Case Distributions
    status_res = await db.execute(select(Case.status, func.count(Case.id)).group_by(Case.status))
    cases_by_status = {s.value: count for s, count in status_res.all()}
    
    domain_res = await db.execute(select(Case.domain, func.count(Case.id)).group_by(Case.domain))
    cases_by_domain = {d.value: count for d, count in domain_res.all()}

    # 3. Verdict Metrics
    v_metrics = await db.execute(
        select(
            func.avg(Verdict.composite_confidence),
            func.avg(Verdict.consensus_level),
            func.sum(Verdict.human_override_applied)
        )
    )
    avg_conf, avg_consensus, overrides = v_metrics.fetchone()

    # 4. Feedback Metrics
    avg_rating = await db.scalar(select(func.avg(Feedback.outcome_rating)))

    # 5. Agent Performance
    agent_perf_res = await db.execute(
        select(
            AgentEvaluation.agent_name,
            func.count(AgentEvaluation.id),
            func.avg(AgentEvaluation.confidence_score)
        ).group_by(AgentEvaluation.agent_name)
    )
    
    agent_performance = []
    for name, count, avg_c in agent_perf_res.all():
        agent_performance.append({
            "agent_name": name,
            "total_evaluations": count,
            "average_confidence": round(float(avg_c or 0), 2),
            "verdict_distribution": {} # Simplified for now
        })

    return {
        "total_cases": case_count or 0,
        "cases_by_status": cases_by_status,
        "cases_by_domain": cases_by_domain,
        "average_confidence": round(float(avg_conf or 0), 2),
        "average_consensus": round(float(avg_consensus or 0), 4),
        "total_verdicts": verdict_count or 0,
        "human_overrides": int(overrides or 0),
        "total_feedback": feedback_count or 0,
        "average_rating": round(float(avg_rating or 0), 2),
        "agent_performance": agent_performance,
    }


@router.get("/audit-logs")
async def get_audit_log_entries(
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get audit log entries from the database."""
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "NirnayX API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }

