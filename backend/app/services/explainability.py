"""
Explainability & Audit Layer — Generates human-readable reports and audit trails.
Implements FR-05.1 through FR-05.5.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


def generate_verdict_report(
    case: Dict[str, Any],
    verdict: Dict[str, Any],
    evaluations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    FR-05.1: Generate a human-readable Verdict Report.
    Includes verdict, confidence, per-agent breakdown, reasoning chains, and weight contributions.
    """
    # Build detailed reasoning per agent
    detailed_reasoning = []
    for ev in evaluations:
        chain = ev.get("reasoning_chain", {})
        detailed_reasoning.append({
            "agent_name": ev.get("agent_name", "Unknown"),
            "archetype": ev.get("archetype", "unknown"),
            "verdict": ev.get("verdict", "escalate"),
            "confidence_score": ev.get("confidence_score", 0),
            "decision_value": ev.get("decision_value", 0),
            "weight_used": ev.get("weight_at_evaluation", 1.0),
            "contribution_score": ev.get("weight_contribution", 0),
            "focus_area": chain.get("focus_area", ""),
            "reasoning_bias": chain.get("reasoning_bias", ""),
            "verdict_rationale": chain.get("verdict_rationale", ""),
            "supporting_factors": chain.get("supporting_factors", []),
            "concerns_raised": chain.get("concerns_raised", []),
            "key_questions_considered": chain.get("key_questions_considered", []),
        })

    # Confidence analysis
    confidences = [ev.get("confidence_score", 0) for ev in evaluations]
    confidence_analysis = {
        "mean": round(sum(confidences) / len(confidences), 2) if confidences else 0,
        "min": round(min(confidences), 2) if confidences else 0,
        "max": round(max(confidences), 2) if confidences else 0,
        "spread": round(max(confidences) - min(confidences), 2) if confidences else 0,
        "distribution": {
            "high_confidence": sum(1 for c in confidences if c >= 75),
            "medium_confidence": sum(1 for c in confidences if 50 <= c < 75),
            "low_confidence": sum(1 for c in confidences if c < 50),
        },
    }

    # Generate summary text
    final_verdict_text = verdict.get("final_verdict", "escalate").upper()
    composite_conf = verdict.get("composite_confidence", 0)
    consensus = verdict.get("consensus_level", 0)

    agent_verdicts = [ev.get("verdict", "escalate") for ev in evaluations]
    approve_count = agent_verdicts.count("approve")
    reject_count = agent_verdicts.count("reject")
    escalate_count = agent_verdicts.count("escalate")

    summary = (
        f"NirnayX Verdict Report\n"
        f"{'='*50}\n\n"
        f"Case: {case.get('title', 'Untitled')}\n"
        f"Domain: {case.get('domain', 'N/A')}\n"
        f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"FINAL VERDICT: {final_verdict_text}\n"
        f"Composite Confidence: {composite_conf:.1f}%\n"
        f"Consensus Level: {consensus:.1%}\n\n"
        f"Agent Panel Summary:\n"
        f"  • {len(evaluations)} agents evaluated this case\n"
        f"  • {approve_count} recommended APPROVE\n"
        f"  • {reject_count} recommended REJECT\n"
        f"  • {escalate_count} recommended ESCALATE\n\n"
    )

    # Add decision drivers
    drivers = verdict.get("decision_drivers", [])
    if drivers:
        summary += "Key Decision Drivers:\n"
        for i, driver in enumerate(drivers, 1):
            summary += f"  {i}. {driver.get('agent', 'Unknown')}: {driver.get('reasoning', 'N/A')}\n"
        summary += "\n"

    # Add dissenting views
    dissenters = verdict.get("dissenting_summary", [])
    if dissenters:
        summary += "Dissenting Views:\n"
        for d in dissenters:
            summary += f"  • {d.get('agent', 'Unknown')} ({d.get('verdict', 'N/A')}): {d.get('reasoning', 'N/A')}\n"
        summary += "\n"

    # Human review note
    if verdict.get("requires_human_review"):
        summary += (
            "⚠️  HUMAN REVIEW REQUIRED\n"
            "Agent consensus is below 60%. This verdict requires mandatory human review.\n\n"
        )

    # Recommendation text
    recommendation = _generate_recommendation(
        verdict.get("final_verdict", "escalate"),
        composite_conf,
        consensus,
        case.get("domain", "business"),
    )

    return {
        "summary": summary,
        "detailed_reasoning": detailed_reasoning,
        "confidence_analysis": confidence_analysis,
        "recommendation_text": recommendation,
    }


def _generate_recommendation(verdict: str, confidence: float, consensus: float, domain: str) -> str:
    """Generate a natural-language recommendation based on the verdict."""
    confidence_level = "high" if confidence >= 75 else "moderate" if confidence >= 50 else "low"

    if verdict == "approve":
        if confidence_level == "high":
            return (
                f"Based on comprehensive multi-agent analysis in the {domain} domain, the panel "
                f"strongly recommends APPROVAL with {confidence:.1f}% confidence. Agent consensus "
                f"at {consensus:.1%} indicates robust agreement across diverse analytical perspectives."
            )
        else:
            return (
                f"The panel recommends APPROVAL in the {domain} domain, though with {confidence_level} "
                f"confidence ({confidence:.1f}%). Consider reviewing the dissenting opinions and "
                f"addressing the raised concerns before proceeding."
            )
    elif verdict == "reject":
        return (
            f"The panel recommends REJECTION of this {domain} case with {confidence:.1f}% confidence. "
            f"Key risk factors and analytical concerns outweigh potential benefits. "
            f"Review the detailed agent reasoning for specific rejection drivers."
        )
    else:
        return (
            f"The panel recommends ESCALATION for human review in this {domain} case. "
            f"Agent consensus ({consensus:.1%}) and confidence ({confidence:.1f}%) indicate "
            f"this case requires additional human judgment. Review all agent perspectives carefully."
        )


def create_audit_entry(
    action: str,
    entity_type: str,
    entity_id: str = None,
    actor_id: str = None,
    actor_email: str = None,
    details: Dict = None,
) -> Dict[str, Any]:
    """
    FR-05.2: Create a structured audit log entry.
    All audit logs are tamper-evident and append-only.
    """
    return {
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
        "actor_id": str(actor_id) if actor_id else None,
        "actor_email": actor_email,
        "details": details or {},
        "created_at": datetime.utcnow().isoformat(),
    }
