"""
Aggregation & Verdict Engine — Synthesizes all agent outputs into a final weighted verdict.
Implements FR-04.1 through FR-04.5.
"""

from typing import Dict, List, Any, Optional
from app.config import settings


def aggregate_verdicts(
    evaluations: List[Dict[str, Any]],
    aggregation_mode: str = "weighted_voting",
    domain: str = "business",
) -> Dict[str, Any]:
    """
    Aggregate all agent evaluations into a final verdict.

    FR-04.1: Final Score = Σ (Agent Weight × Confidence × Decision Value)
    FR-04.2: Support three aggregation modes
    FR-04.4: Output includes final recommendation, dissenting summary, decision drivers
    FR-04.5: Flag cases where consensus < 60%

    Args:
        evaluations: List of agent evaluation results
        aggregation_mode: One of "weighted_voting", "confidence_weighted_average", "supermajority_threshold"
        domain: Case domain

    Returns:
        Complete verdict result dictionary
    """
    if not evaluations:
        return _empty_verdict()

    if aggregation_mode == "weighted_voting":
        result = _weighted_voting(evaluations)
    elif aggregation_mode == "confidence_weighted_average":
        result = _confidence_weighted_average(evaluations)
    elif aggregation_mode == "supermajority_threshold":
        result = _supermajority_threshold(evaluations)
    else:
        result = _weighted_voting(evaluations)

    # Add common fields
    result["aggregation_mode"] = aggregation_mode
    result["agent_count"] = len(evaluations)
    result["domain"] = domain

    # Compute consensus level
    verdict_counts = {}
    for ev in evaluations:
        v = ev.get("verdict", "escalate")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
    max_agreement = max(verdict_counts.values()) / len(evaluations) if evaluations else 0
    result["consensus_level"] = round(max_agreement, 4)

    # FR-04.5: Flag low consensus for human review
    result["requires_human_review"] = int(
        max_agreement < settings.LOW_CONSENSUS_THRESHOLD
    )

    # Build per-agent breakdown
    result["per_agent_breakdown"] = [
        {
            "agent_name": ev.get("agent_name", "Unknown"),
            "archetype": ev.get("archetype", "unknown"),
            "verdict": ev.get("verdict", "escalate"),
            "confidence": ev.get("confidence_score", 0),
            "decision_value": ev.get("decision_value", 0),
            "weight": ev.get("weight_at_evaluation", 1.0),
            "contribution": ev.get("weight_contribution", 0),
            "reasoning_summary": ev.get("reasoning_chain", {}).get("verdict_rationale", ""),
        }
        for ev in evaluations
    ]

    # Extract decision drivers (top contributing agents)
    sorted_agents = sorted(
        result["per_agent_breakdown"],
        key=lambda x: abs(x["contribution"]),
        reverse=True,
    )
    result["decision_drivers"] = [
        {
            "agent": a["agent_name"],
            "contribution": a["contribution"],
            "verdict": a["verdict"],
            "reasoning": a["reasoning_summary"],
        }
        for a in sorted_agents[:3]
    ]

    # Dissenting agents
    result["dissenting_summary"] = [
        {
            "agent": a["agent_name"],
            "archetype": a["archetype"],
            "verdict": a["verdict"],
            "confidence": a["confidence"],
            "reasoning": a["reasoning_summary"],
        }
        for a in result["per_agent_breakdown"]
        if a["verdict"] != result["final_verdict"]
    ]

    return result


def _weighted_voting(evaluations: List[Dict]) -> Dict[str, Any]:
    """
    FR-04.1: Final Score = Σ (Agent Weight × Confidence × Decision Value)
    Verdict determined by weighted vote majority.
    """
    # Compute weighted votes for each verdict option
    verdict_scores = {"approve": 0.0, "reject": 0.0, "escalate": 0.0}
    total_score = 0.0

    for ev in evaluations:
        weight = ev.get("weight_at_evaluation", 1.0)
        confidence = ev.get("confidence_score", 50.0) / 100.0
        decision_value = ev.get("decision_value", 0.5)
        verdict = ev.get("verdict", "escalate")

        weighted_contribution = weight * confidence * decision_value
        verdict_scores[verdict] = verdict_scores.get(verdict, 0) + weighted_contribution
        total_score += weighted_contribution

    # Final verdict is the one with highest weighted score
    final_verdict = max(verdict_scores, key=verdict_scores.get)

    # Composite confidence: weighted average of all agent confidences
    total_weight = sum(ev.get("weight_at_evaluation", 1.0) for ev in evaluations)
    composite_confidence = sum(
        ev.get("confidence_score", 50.0) * ev.get("weight_at_evaluation", 1.0)
        for ev in evaluations
    ) / total_weight if total_weight > 0 else 50.0

    return {
        "final_verdict": final_verdict,
        "composite_confidence": round(composite_confidence, 2),
        "final_score": round(total_score, 4),
        "verdict_scores": {k: round(v, 4) for k, v in verdict_scores.items()},
    }


def _confidence_weighted_average(evaluations: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate using confidence-weighted average of decision values.
    """
    total_conf_weight = 0.0
    weighted_decision = 0.0

    for ev in evaluations:
        confidence = ev.get("confidence_score", 50.0) / 100.0
        decision_value = ev.get("decision_value", 0.5)
        weight = ev.get("weight_at_evaluation", 1.0)

        conf_weight = confidence * weight
        total_conf_weight += conf_weight
        weighted_decision += conf_weight * decision_value

    avg_decision = weighted_decision / total_conf_weight if total_conf_weight > 0 else 0.5

    if avg_decision >= 0.65:
        final_verdict = "approve"
    elif avg_decision >= 0.4:
        final_verdict = "escalate"
    else:
        final_verdict = "reject"

    composite_confidence = sum(
        ev.get("confidence_score", 50.0) for ev in evaluations
    ) / len(evaluations)

    return {
        "final_verdict": final_verdict,
        "composite_confidence": round(composite_confidence, 2),
        "final_score": round(avg_decision, 4),
        "average_decision_value": round(avg_decision, 4),
    }


def _supermajority_threshold(evaluations: List[Dict], threshold: float = 0.67) -> Dict[str, Any]:
    """
    Require supermajority (67%+) agreement for approve/reject.
    Otherwise escalate for human review.
    """
    verdict_counts = {}
    for ev in evaluations:
        v = ev.get("verdict", "escalate")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    total = len(evaluations)
    final_verdict = "escalate"  # Default if no supermajority

    for verdict, count in verdict_counts.items():
        if count / total >= threshold:
            final_verdict = verdict
            break

    total_score = sum(
        ev.get("weight_at_evaluation", 1.0) * (ev.get("confidence_score", 50.0) / 100.0) * ev.get("decision_value", 0.5)
        for ev in evaluations
    )

    composite_confidence = sum(
        ev.get("confidence_score", 50.0) for ev in evaluations
    ) / len(evaluations)

    return {
        "final_verdict": final_verdict,
        "composite_confidence": round(composite_confidence, 2),
        "final_score": round(total_score, 4),
        "supermajority_threshold": threshold,
        "verdict_distribution": verdict_counts,
    }


def _empty_verdict() -> Dict[str, Any]:
    """Return an empty verdict when no evaluations are provided."""
    return {
        "final_verdict": "escalate",
        "composite_confidence": 0.0,
        "final_score": 0.0,
        "aggregation_mode": "none",
        "agent_count": 0,
        "consensus_level": 0.0,
        "requires_human_review": 1,
        "decision_drivers": [],
        "dissenting_summary": [],
        "per_agent_breakdown": [],
    }
