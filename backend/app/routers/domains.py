from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.domain import DomainProfile
from app.schemas import DomainProfileCreate, DomainProfileResponse
from typing import List
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1/domains", tags=["Domain Profiles"])


async def init_default_domains(db: AsyncSession):
    """Create default domain profiles if they don't exist."""
    defaults = [
        {
            "name": "Legal & Judicial",
            "domain_key": "legal",
            "description": "Pre-trial verdict simulation, case analysis, and legal risk assessment.",
            "aggregation_mode": "supermajority_threshold",
            "agent_count": 5,
            "requires_human_review": 1,
            "max_weight_per_agent": 0.35,
            "disclaimer_text": "All verdicts are advisory only. Mandatory human review required for any verdict influencing liberty or sentencing.",
        },
        {
            "name": "Human Resources",
            "domain_key": "hr",
            "description": "Structured candidate evaluation, hiring decisions, and performance review analysis.",
            "aggregation_mode": "weighted_voting",
            "agent_count": 5,
            "requires_human_review": 1,
            "max_weight_per_agent": 0.35,
            "disclaimer_text": "Final hiring decisions require human approval. Automated rejection prohibited without human review.",
        },
        {
            "name": "Business Strategy",
            "domain_key": "business",
            "description": "Investment analysis, market entry decisions, M&A evaluation, and strategic planning.",
            "aggregation_mode": "weighted_voting",
            "agent_count": 5,
            "requires_human_review": 0,
            "max_weight_per_agent": 0.35,
            "disclaimer_text": None,
        },
        {
            "name": "Healthcare",
            "domain_key": "healthcare",
            "description": "Diagnostic support, treatment planning, and clinical decision assistance.",
            "aggregation_mode": "supermajority_threshold",
            "agent_count": 7,
            "requires_human_review": 1,
            "max_weight_per_agent": 0.30,
            "disclaimer_text": "Clinical decisions require sign-off from licensed practitioner. System cannot override physician.",
        },
        {
            "name": "Governance & Policy",
            "domain_key": "policy",
            "description": "Public policy impact simulation and stakeholder sentiment analysis.",
            "aggregation_mode": "confidence_weighted_average",
            "agent_count": 5,
            "requires_human_review": 0,
            "max_weight_per_agent": 0.35,
            "disclaimer_text": "Outputs include uncertainty quantification. No autonomous policy enforcement.",
        },
    ]

    for d in defaults:
        result = await db.execute(select(DomainProfile).filter(DomainProfile.domain_key == d["domain_key"]))
        if not result.scalar_one_or_none():
            db.add(DomainProfile(**d))
    await db.commit()


@router.get("", response_model=List[DomainProfileResponse])
async def list_domains(db: AsyncSession = Depends(get_db)):
    """List all domain profiles."""
    result = await db.execute(select(DomainProfile).filter(DomainProfile.is_active == 1))
    domains = result.scalars().all()
    
    # If no domains exist, seed them (first run)
    if not domains:
        await init_default_domains(db)
        result = await db.execute(select(DomainProfile).filter(DomainProfile.is_active == 1))
        domains = result.scalars().all()
        
    return domains


@router.get("/{domain_key}", response_model=DomainProfileResponse)
async def get_domain(domain_key: str, db: AsyncSession = Depends(get_db)):
    """Get a specific domain profile by key."""
    result = await db.execute(select(DomainProfile).filter(DomainProfile.domain_key == domain_key))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail=f"Domain '{domain_key}' not found")
    return domain


@router.post("", response_model=DomainProfileResponse, status_code=201)
async def create_domain(domain_data: DomainProfileCreate, db: AsyncSession = Depends(get_db)):
    """Create a new domain profile."""
    result = await db.execute(select(DomainProfile).filter(DomainProfile.domain_key == domain_data.domain_key))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Domain key already exists")

    new_domain = DomainProfile(
        name=domain_data.name,
        domain_key=domain_data.domain_key,
        description=domain_data.description,
        aggregation_mode=domain_data.aggregation_mode.value,
        agent_count=domain_data.agent_count,
        requires_human_review=domain_data.requires_human_review,
        max_weight_per_agent=0.35,
        disclaimer_text=domain_data.disclaimer_text
    )
    db.add(new_domain)
    await db.commit()
    await db.refresh(new_domain)
    return new_domain

