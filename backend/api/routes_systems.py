from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from pydantic import BaseModel

from backend.database.db import get_db
from backend.systems.contract_intelligence.system import contract_intelligence_system
from backend.systems.risk_intelligence.system import risk_intelligence_system
from backend.systems.negotiation_intelligence.system import negotiation_intelligence_system
from backend.systems.compliance_intelligence.system import compliance_intelligence_system
from backend.systems.obligation_intelligence.system import obligation_intelligence_system
from backend.systems.dispute_intelligence.system import dispute_intelligence_system

router = APIRouter(prefix="/systems", tags=["Independent Autonomous Societies"])


class StandaloneContractPayload(BaseModel):
    contract_text: str
    contract_id: Optional[str] = None


class StandaloneNegotiationPayload(BaseModel):
    contract_text: str
    commercial_objective: Optional[str] = "Cap liability at 12 months, eliminate uncapped indemnity, and secure bilateral termination."
    contract_id: Optional[str] = None


class StandaloneCompliancePayload(BaseModel):
    contract_text: str
    policy_path: Optional[str] = None
    contract_id: Optional[str] = None


class StandaloneObligationPayload(BaseModel):
    contract_text: str
    effective_date: Optional[str] = "2026-10-01"
    contract_id: Optional[str] = None


class StandaloneDisputePayload(BaseModel):
    contract_text: str
    party_a: Optional[str] = "Customer"
    party_b: Optional[str] = "Vendor"
    contract_id: Optional[str] = None


# 1. Standalone Contract Intelligence
@router.post("/contract-intelligence/analyze")
async def analyze_contract_standalone(
    payload: StandaloneContractPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    INDEPENDENT OPERATION: SYSTEM 1 — CONTRACT INTELLIGENCE
    Runs Parallel + Verification architecture without requiring Director or other systems.
    """
    graph = await contract_intelligence_system.analyze_contract(
        contract_text=payload.contract_text,
        contract_id=payload.contract_id,
        db_session=db
    )
    return graph.model_dump()


# 2. Standalone Risk Intelligence
@router.post("/risk-intelligence/analyze")
async def analyze_risk_standalone(
    payload: StandaloneContractPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    INDEPENDENT OPERATION: SYSTEM 2 — RISK INTELLIGENCE
    Runs Adversarial Debate architecture (Hunter vs Counterargument vs Assessor) standalone.
    """
    report = await risk_intelligence_system.analyze_risk(
        contract=payload.contract_text,
        contract_id=payload.contract_id,
        db_session=db
    )
    return report.model_dump()


# 3. Standalone Negotiation Intelligence
@router.post("/negotiation-intelligence/analyze")
async def analyze_negotiation_standalone(
    payload: StandaloneNegotiationPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    INDEPENDENT OPERATION: SYSTEM 3 — NEGOTIATION INTELLIGENCE
    Runs Planner + Counterparty Simulator + Critic architecture standalone.
    """
    strategy = await negotiation_intelligence_system.plan_negotiation(
        contract=payload.contract_text,
        objective=payload.commercial_objective or "Protect commercial terms",
        contract_id=payload.contract_id,
        db_session=db
    )
    return strategy.model_dump()


# 4. Standalone Compliance Intelligence
@router.post("/compliance-intelligence/analyze")
async def analyze_compliance_standalone(
    payload: StandaloneCompliancePayload,
    db: AsyncSession = Depends(get_db)
):
    """
    INDEPENDENT OPERATION: SYSTEM 4 — COMPLIANCE INTELLIGENCE
    Runs Retrieval + Rules + Verification architecture standalone.
    """
    report = await compliance_intelligence_system.audit_compliance(
        contract=payload.contract_text,
        policy_path=payload.policy_path,
        contract_id=payload.contract_id,
        db_session=db
    )
    return report.model_dump()


# 5. Standalone Obligation Intelligence
@router.post("/obligation-intelligence/analyze")
async def analyze_obligation_standalone(
    payload: StandaloneObligationPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    INDEPENDENT OPERATION: SYSTEM 5 — OBLIGATION INTELLIGENCE
    Runs Event-Driven Monitoring architecture standalone.
    """
    schedule = await obligation_intelligence_system.register_obligations(
        contract=payload.contract_text,
        contract_id=payload.contract_id,
        effective_date=payload.effective_date or "2026-10-01",
        db_session=db
    )
    return schedule.model_dump()


# 6. Standalone Dispute Intelligence
@router.post("/dispute-intelligence/analyze")
async def analyze_dispute_standalone(
    payload: StandaloneDisputePayload,
    db: AsyncSession = Depends(get_db)
):
    """
    INDEPENDENT OPERATION: SYSTEM 6 — DISPUTE INTELLIGENCE
    Runs Multi-Perspective Simulation + Debate architecture standalone.
    """
    assessment = await dispute_intelligence_system.analyze_disputes(
        contract=payload.contract_text,
        contract_id=payload.contract_id,
        party_a_name=payload.party_a or "Customer",
        party_b_name=payload.party_b or "Vendor",
        db_session=db
    )
    return assessment.model_dump()
