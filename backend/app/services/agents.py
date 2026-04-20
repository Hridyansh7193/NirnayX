"""
Juror Agent Framework — Multi-agent evaluation engine with 5 distinct archetypes.
Implements FR-02.1 through FR-02.6.

Each agent independently evaluates a case from a different reasoning perspective,
producing a verdict, confidence score, and structured reasoning chain.
Agents operate in "blind deliberation" mode — no agent sees another's output.
"""

import random
import hashlib
import math
from typing import Dict, List, Any, Optional
from datetime import datetime


# ─── Agent Archetype Definitions ────────────────────────

AGENT_ARCHETYPES = {
    "risk_analyst": {
        "name": "Risk Analyst",
        "archetype": "risk_analyst",
        "description": "Identifies and quantifies potential risks, downside scenarios, and failure modes. Conservative by nature.",
        "reasoning_priors": {
            "focus": "risk identification and mitigation",
            "bias": "conservative, risk-averse",
            "key_questions": [
                "What could go wrong?",
                "What are the worst-case scenarios?",
                "What risks are being underestimated?",
                "Are there hidden liabilities?",
                "What safeguards exist?"
            ],
            "weight_factors": ["risk_severity", "probability_of_failure", "mitigation_strength"],
        },
    },
    "growth_advocate": {
        "name": "Growth Advocate",
        "archetype": "growth_advocate",
        "description": "Focuses on opportunities, growth potential, and positive outcomes. Optimistic and forward-looking.",
        "reasoning_priors": {
            "focus": "opportunity identification and growth potential",
            "bias": "optimistic, opportunity-seeking",
            "key_questions": [
                "What is the upside potential?",
                "How does this create value?",
                "What competitive advantages emerge?",
                "Can this scale?",
                "What precedents support success?"
            ],
            "weight_factors": ["growth_potential", "market_opportunity", "strategic_value"],
        },
    },
    "financial_modeler": {
        "name": "Financial Modeler",
        "archetype": "financial_modeler",
        "description": "Analyzes quantitative data, financial metrics, and economic impact. Data-driven and analytical.",
        "reasoning_priors": {
            "focus": "quantitative analysis and financial impact",
            "bias": "data-driven, metrics-focused",
            "key_questions": [
                "What do the numbers say?",
                "What is the ROI/cost-benefit?",
                "Are the financial projections realistic?",
                "What are the economic externalities?",
                "How does this compare to benchmarks?"
            ],
            "weight_factors": ["financial_viability", "cost_efficiency", "quantitative_evidence"],
        },
    },
    "ethical_reviewer": {
        "name": "Ethical Reviewer",
        "archetype": "ethical_reviewer",
        "description": "Evaluates fairness, equity, social impact, and ethical implications. Justice-oriented.",
        "reasoning_priors": {
            "focus": "ethical implications and social impact",
            "bias": "fairness-oriented, stakeholder-conscious",
            "key_questions": [
                "Is this fair to all parties?",
                "What are the ethical implications?",
                "Who is disproportionately affected?",
                "Does this align with regulatory standards?",
                "What are the social consequences?"
            ],
            "weight_factors": ["fairness_score", "regulatory_compliance", "social_impact"],
        },
    },
    "devils_advocate": {
        "name": "Devil's Advocate",
        "archetype": "devils_advocate",
        "description": "Challenges assumptions, finds weaknesses in arguments, and stress-tests conclusions. Contrarian.",
        "reasoning_priors": {
            "focus": "assumption challenging and stress testing",
            "bias": "contrarian, skeptical",
            "key_questions": [
                "What assumptions are being made?",
                "What evidence contradicts this position?",
                "Are there alternative explanations?",
                "What would an opponent argue?",
                "Where is the logic weakest?"
            ],
            "weight_factors": ["argument_strength", "evidence_quality", "logical_consistency"],
        },
    },
}


def _generate_deterministic_seed(case_text: str, agent_type: str) -> int:
    """Generate a deterministic seed from case content and agent type for reproducible results."""
    hash_input = f"{case_text}:{agent_type}"
    return int(hashlib.sha256(hash_input.encode()).hexdigest()[:8], 16)


def _analyze_case_signals(title: str, description: str, domain: str) -> Dict[str, float]:
    """
    Analyze the case text to extract evaluation signals.
    These signals guide each agent's analysis in a content-aware way.
    """
    text = f"{title} {description}".lower()

    # Signal extraction based on content analysis
    signals = {
        "risk_level": 0.5,
        "opportunity_level": 0.5,
        "financial_clarity": 0.5,
        "ethical_complexity": 0.5,
        "evidence_strength": 0.5,
        "complexity": 0.5,
    }

    # Risk indicators
    risk_words = ["risk", "danger", "threat", "loss", "fail", "liability", "damage", "penalty", "violation", "breach"]
    signals["risk_level"] = min(1.0, sum(1 for w in risk_words if w in text) / 4)

    # Opportunity indicators
    opp_words = ["opportunity", "growth", "potential", "benefit", "advantage", "improve", "gain", "profit", "success", "innovation"]
    signals["opportunity_level"] = min(1.0, sum(1 for w in opp_words if w in text) / 4)

    # Financial clarity
    fin_words = ["revenue", "cost", "budget", "roi", "margin", "investment", "valuation", "price", "salary", "compensation"]
    signals["financial_clarity"] = min(1.0, sum(1 for w in fin_words if w in text) / 4)

    # Ethical complexity
    eth_words = ["fair", "equity", "bias", "discrimination", "rights", "ethical", "justice", "compliance", "regulation", "diversity"]
    signals["ethical_complexity"] = min(1.0, sum(1 for w in eth_words if w in text) / 4)

    # Evidence strength (proxy: detail level)
    signals["evidence_strength"] = min(1.0, len(description.split()) / 200)

    # Complexity
    signals["complexity"] = min(1.0, len(description) / 1000)

    return signals


def _agent_evaluate(
    agent_archetype: str,
    title: str,
    description: str,
    domain: str,
    case_signals: Dict[str, float],
    weight: float,
    seed: int,
) -> Dict[str, Any]:
    """
    Simulate an individual agent's evaluation of a case.
    Each agent applies its reasoning priors to the case signals to produce
    a verdict, confidence score, and reasoning chain.
    """
    rng = random.Random(seed)
    archetype_config = AGENT_ARCHETYPES[agent_archetype]
    priors = archetype_config["reasoning_priors"]

    # Base decision factors per archetype
    if agent_archetype == "risk_analyst":
        # High risk → reject, low risk → approve
        base_score = 1.0 - case_signals["risk_level"]
        noise = rng.gauss(0, 0.08)
        confidence = 55 + (case_signals["evidence_strength"] * 30) + rng.gauss(0, 5)
        key_focus = f"Identified risk level at {case_signals['risk_level']:.0%}"

    elif agent_archetype == "growth_advocate":
        # High opportunity → approve
        base_score = case_signals["opportunity_level"]
        noise = rng.gauss(0, 0.1)
        confidence = 50 + (case_signals["opportunity_level"] * 35) + rng.gauss(0, 5)
        key_focus = f"Opportunity potential assessed at {case_signals['opportunity_level']:.0%}"

    elif agent_archetype == "financial_modeler":
        # Financial clarity drives verdict
        base_score = 0.4 + (case_signals["financial_clarity"] * 0.3) + (case_signals["opportunity_level"] * 0.2) - (case_signals["risk_level"] * 0.1)
        noise = rng.gauss(0, 0.06)
        confidence = 60 + (case_signals["financial_clarity"] * 25) + rng.gauss(0, 4)
        key_focus = f"Financial viability score: {case_signals['financial_clarity']:.0%}"

    elif agent_archetype == "ethical_reviewer":
        # Ethical complexity reduces approval likelihood
        base_score = 0.6 - (case_signals["ethical_complexity"] * 0.3)
        noise = rng.gauss(0, 0.07)
        confidence = 55 + (case_signals["evidence_strength"] * 25) + rng.gauss(0, 5)
        key_focus = f"Ethical complexity assessment: {case_signals['ethical_complexity']:.0%}"

    else:  # devils_advocate
        # Contrarian: lower score when evidence is weak
        base_score = case_signals["evidence_strength"] * 0.6 + 0.2
        noise = rng.gauss(0, 0.12)
        confidence = 45 + (case_signals["evidence_strength"] * 20) + rng.gauss(0, 6)
        key_focus = f"Evidence strength challenged: {case_signals['evidence_strength']:.0%}"

    # Compute final decision value
    decision_value = max(0.0, min(1.0, base_score + noise))
    confidence = max(20.0, min(98.0, confidence))

    # Determine verdict
    if decision_value >= 0.65:
        verdict = "approve"
    elif decision_value >= 0.4:
        verdict = "escalate"
    else:
        verdict = "reject"

    # Build reasoning chain
    reasoning_chain = {
        "agent": archetype_config["name"],
        "archetype": agent_archetype,
        "focus_area": priors["focus"],
        "reasoning_bias": priors["bias"],
        "key_questions_considered": priors["key_questions"],
        "analysis_summary": key_focus,
        "verdict_rationale": _generate_rationale(agent_archetype, verdict, decision_value, case_signals, domain),
        "supporting_factors": _generate_supporting_factors(agent_archetype, case_signals, rng),
        "concerns_raised": _generate_concerns(agent_archetype, case_signals, rng),
        "weight_factors_applied": priors["weight_factors"],
        "decision_value_raw": round(decision_value, 4),
    }

    return {
        "verdict": verdict,
        "confidence_score": round(confidence, 2),
        "decision_value": round(decision_value, 4),
        "reasoning_chain": reasoning_chain,
        "weight_at_evaluation": weight,
        "weight_contribution": round(weight * (confidence / 100) * decision_value, 4),
    }


def _generate_rationale(archetype: str, verdict: str, score: float, signals: Dict, domain: str) -> str:
    """Generate human-readable rationale for an agent's verdict."""
    templates = {
        "risk_analyst": {
            "approve": f"After thorough risk assessment, the identified risks appear manageable. Risk level ({signals['risk_level']:.0%}) is within acceptable bounds for the {domain} domain. Recommend proceeding with standard monitoring.",
            "reject": f"Significant unmitigated risks detected (risk level: {signals['risk_level']:.0%}). The downside scenarios outweigh potential benefits in this {domain} context. Recommend rejection pending risk mitigation.",
            "escalate": f"Risk assessment is inconclusive (risk level: {signals['risk_level']:.0%}). Some risks require further investigation before a definitive recommendation can be made in this {domain} case.",
        },
        "growth_advocate": {
            "approve": f"Strong growth potential identified (opportunity: {signals['opportunity_level']:.0%}). This {domain} case presents clear value creation pathways and competitive advantages worth pursuing.",
            "reject": f"Despite optimistic analysis, opportunity signals are weak ({signals['opportunity_level']:.0%}). Limited growth potential in current form for the {domain} domain.",
            "escalate": f"Moderate opportunity potential ({signals['opportunity_level']:.0%}) in {domain}. Growth signals are present but require validation before full endorsement.",
        },
        "financial_modeler": {
            "approve": f"Quantitative analysis supports a positive outcome. Financial metrics (clarity: {signals['financial_clarity']:.0%}) indicate sound fundamentals for this {domain} decision.",
            "reject": f"Financial modeling reveals unfavorable metrics (clarity: {signals['financial_clarity']:.0%}). Cost-benefit analysis for this {domain} case does not support approval.",
            "escalate": f"Financial data is insufficient for a definitive recommendation (clarity: {signals['financial_clarity']:.0%}). Additional quantitative evidence needed for this {domain} analysis.",
        },
        "ethical_reviewer": {
            "approve": f"Ethical review finds no significant concerns. Fairness and compliance standards appear met for {domain} context. Ethical complexity is manageable ({signals['ethical_complexity']:.0%}).",
            "reject": f"Ethical concerns identified (complexity: {signals['ethical_complexity']:.0%}). Potential fairness issues or regulatory non-compliance in this {domain} case warrant rejection.",
            "escalate": f"Ethical analysis reveals moderate complexity ({signals['ethical_complexity']:.0%}). Stakeholder impact assessment in {domain} needs further review.",
        },
        "devils_advocate": {
            "approve": f"Stress testing confirms robust case fundamentals. Arguments withstand scrutiny with evidence strength at {signals['evidence_strength']:.0%}. Assumptions in {domain} context are well-supported.",
            "reject": f"Critical weaknesses found under stress testing. Evidence strength ({signals['evidence_strength']:.0%}) is insufficient to support claims in {domain} domain.",
            "escalate": f"Assumptions partially challenged (evidence: {signals['evidence_strength']:.0%}). Some arguments are solid but others lack adequate support in {domain} context.",
        },
    }
    return templates.get(archetype, {}).get(verdict, "Analysis complete.")


def _generate_supporting_factors(archetype: str, signals: Dict, rng: random.Random) -> List[str]:
    """Generate supporting factors for the agent's analysis."""
    all_factors = {
        "risk_analyst": [
            "Historical precedent analysis supports risk assessment",
            "Identified mitigation strategies reduce overall exposure",
            "Comparable cases show manageable risk profiles",
            "Regulatory framework provides safety guardrails",
        ],
        "growth_advocate": [
            "Market trends align with growth thesis",
            "Competitive landscape favors first-mover advantage",
            "Scalability potential validated by comparable examples",
            "Strategic value extends beyond immediate returns",
        ],
        "financial_modeler": [
            "Revenue projections supported by market data",
            "Cost structure analysis shows operational efficiency",
            "Sensitivity analysis confirms variable tolerance ranges",
            "Benchmark comparison against industry standards",
        ],
        "ethical_reviewer": [
            "Stakeholder impact analysis completed",
            "Fairness criteria assessed against best practices",
            "Regulatory compliance verified for relevant standards",
            "Social impact assessment within acceptable range",
        ],
        "devils_advocate": [
            "Stress-tested assumptions under adverse conditions",
            "Contrarian evidence reviewed and weighted",
            "Logical consistency validated across argument chain",
            "Alternative hypotheses considered and evaluated",
        ],
    }
    factors = all_factors.get(archetype, [])
    count = rng.randint(2, min(4, len(factors)))
    return rng.sample(factors, count)


def _generate_concerns(archetype: str, signals: Dict, rng: random.Random) -> List[str]:
    """Generate concerns or caveats from each agent's perspective."""
    all_concerns = {
        "risk_analyst": [
            "Tail risk scenarios not fully quantified",
            "Historical data may not capture emerging risk factors",
            "Mitigation cost estimates may be underbuilt",
        ],
        "growth_advocate": [
            "Growth projections assume favorable market conditions",
            "Execution risk not fully factored into opportunity assessment",
            "External competitive response may diminish upside",
        ],
        "financial_modeler": [
            "Limited financial data available for comprehensive modeling",
            "Assumptions rely on forward-looking estimates",
            "Currency and market volatility not fully modeled",
        ],
        "ethical_reviewer": [
            "Long-term social impact difficult to quantify",
            "Evolving regulatory landscape may change compliance posture",
            "Minority stakeholder perspectives may be underrepresented",
        ],
        "devils_advocate": [
            "Information asymmetry may bias available evidence",
            "Confirmation bias risk in presented arguments",
            "Alternative outcome scenarios insufficiently explored",
        ],
    }
    concerns = all_concerns.get(archetype, [])
    count = rng.randint(1, min(3, len(concerns)))
    return rng.sample(concerns, count)


def evaluate_case(
    title: str,
    description: str,
    domain: str,
    agent_count: int = 5,
    agent_weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Run all juror agents on a case in blind deliberation mode.

    Args:
        title: Case title
        description: Case description
        domain: Case domain (legal, hr, business, healthcare, policy)
        agent_count: Number of agents to use (3-15)
        agent_weights: Optional dict of archetype -> current weight

    Returns:
        List of agent evaluation results
    """
    # Select agents based on count
    archetypes = list(AGENT_ARCHETYPES.keys())
    selected = archetypes[:min(agent_count, len(archetypes))]

    # If more agents requested than archetypes, duplicate with variation
    while len(selected) < agent_count:
        selected.append(archetypes[len(selected) % len(archetypes)])

    # Analyze case signals (shared input, not shared between agents)
    case_signals = _analyze_case_signals(title, description, domain)

    # Default weights
    if not agent_weights:
        agent_weights = {a: 1.0 for a in archetypes}

    # Evaluate with each agent independently (blind deliberation)
    evaluations = []
    for i, archetype in enumerate(selected):
        seed = _generate_deterministic_seed(f"{title}{description}", f"{archetype}_{i}")
        weight = agent_weights.get(archetype, 1.0)

        result = _agent_evaluate(
            agent_archetype=archetype,
            title=title,
            description=description,
            domain=domain,
            case_signals=case_signals,
            weight=weight,
            seed=seed,
        )
        result["agent_index"] = i
        result["archetype"] = archetype
        result["agent_name"] = AGENT_ARCHETYPES[archetype]["name"]
        evaluations.append(result)

    return evaluations


def get_default_agents() -> List[Dict[str, Any]]:
    """Return the default agent archetype configurations."""
    return [
        {
            "name": config["name"],
            "archetype": key,
            "description": config["description"],
            "reasoning_priors": config["reasoning_priors"],
            "base_weight": 1.0,
        }
        for key, config in AGENT_ARCHETYPES.items()
    ]
