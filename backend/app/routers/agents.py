"""
Agents Router — Agent profile management and RL telemetry.
"""

from fastapi import APIRouter
from app.schemas import AgentProfileResponse, RLTelemetry
from app.services.agents import AGENT_ARCHETYPES, get_default_agents
from app.services.rl_engine import rl_engine
from typing import List

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


@router.get("", response_model=List[dict])
async def list_agents():
    """List all available juror agent archetypes."""
    return get_default_agents()


@router.get("/{archetype}")
async def get_agent(archetype: str):
    """Get details of a specific agent archetype."""
    if archetype not in AGENT_ARCHETYPES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Agent archetype '{archetype}' not found")
    config = AGENT_ARCHETYPES[archetype]
    return {
        "name": config["name"],
        "archetype": archetype,
        "description": config["description"],
        "reasoning_priors": config["reasoning_priors"],
    }


@router.get("/rl/telemetry")
async def get_rl_telemetry():
    """
    FR-03.7: Expose RL telemetry data.
    Returns reward curves, convergence metrics, and agent weight history.
    """
    return rl_engine.get_telemetry()


@router.get("/rl/bias-report")
async def get_bias_report():
    """
    Get current bias audit report.
    Checks that no single agent exceeds 35% weight contribution.
    """
    # Get current weights from latest telemetry
    telemetry = rl_engine.get_telemetry()
    if telemetry["agent_weight_history"]:
        latest_weights = telemetry["agent_weight_history"][-1]["weights"]
    else:
        latest_weights = {k: 1.0 for k in AGENT_ARCHETYPES}

    return rl_engine.get_bias_report(latest_weights)
