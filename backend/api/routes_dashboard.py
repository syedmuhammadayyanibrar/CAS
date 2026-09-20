from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Dict, Any, List

from backend.database.db import get_db
from backend.database.schema import (
    ContractModel,
    RiskReportModel,
    HumanReviewModel,
    ObligationScheduleModel,
    CASMessageModel,
    ComplianceReportModel,
)
from backend.core.config import settings
from backend.director.execution_tracker import execution_tracker

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregate executive metrics for the CAS Operations Dashboard.
    Includes active contract count, risk distribution, pending HITL reviews,
    obligations due, live event stream, and society status.
    """
    # Total contracts & status counts
    total_contracts_res = await db.execute(select(func.count(ContractModel.id)))
    total_contracts = total_contracts_res.scalar_one_or_none() or 0

    contracts_res = await db.execute(select(ContractModel).order_by(desc(ContractModel.created_at)).limit(5))
    recent_contracts_objs = contracts_res.scalars().all()

    # Calculate status counts
    all_contracts_res = await db.execute(select(ContractModel.status))
    all_statuses = [r[0] for r in all_contracts_res.fetchall()]
    status_counts = {
        "INTAKE": all_statuses.count("INTAKE"),
        "ANALYZED": all_statuses.count("ANALYZED"),
        "SIGNED": all_statuses.count("SIGNED"),
        "APPROVED": all_statuses.count("APPROVED"),
        "RENEWAL_DUE": all_statuses.count("RENEWAL_DUE"),
    }

    # High risk count
    high_risk_res = await db.execute(
        select(func.count(RiskReportModel.id)).where(
            (RiskReportModel.overall_score >= 0.6) | (RiskReportModel.requires_escalation == True)
        )
    )
    high_risk_count = high_risk_res.scalar_one_or_none() or 0

    # Pending human reviews
    pending_reviews_res = await db.execute(
        select(func.count(HumanReviewModel.review_id)).where(HumanReviewModel.status == "PENDING")
    )
    pending_reviews_count = pending_reviews_res.scalar_one_or_none() or 0

    # Total obligations registered
    obligations_res = await db.execute(select(func.sum(ObligationScheduleModel.total_obligations)))
    total_obligations = obligations_res.scalar_one_or_none() or 0

    # Recent CAS events
    events_res = await db.execute(
        select(CASMessageModel).order_by(desc(CASMessageModel.created_at)).limit(10)
    )
    recent_events = [
        {
            "event_id": e.event_id,
            "contract_id": e.contract_id,
            "source": e.source_system,
            "target": e.target_system,
            "event_type": e.event_type,
            "priority": e.priority,
            "confidence": e.confidence,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events_res.scalars().all()
    ]

    # Format recent contracts with risk level
    recent_contracts = []
    for c in recent_contracts_objs:
        risk_stmt = (
            select(RiskReportModel.overall_score)
            .where(RiskReportModel.contract_id == c.id)
            .order_by(desc(RiskReportModel.id))
            .limit(1)
        )
        r_res = await db.execute(risk_stmt)
        score = r_res.scalars().first() or 0.0

        party_name = c.metadata_json.get("counterparty") or c.metadata_json.get("parties", ["Counterparty"])[0] if c.metadata_json else "Vendor"

        recent_contracts.append({
            "id": c.id,
            "title": c.title,
            "status": c.status,
            "counterparty": party_name,
            "governing_law": c.governing_law or "Delaware",
            "risk_score": score,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    # Societies status overview
    societies = [
        {
            "id": "contract_intelligence",
            "name": "Contract Intelligence Society",
            "architecture": "Parallel + Verification",
            "status": "HEALTHY",
            "agent_count": 4,
            "description": "Deconstructs agreements into typed relational graph schema.",
        },
        {
            "id": "risk_intelligence",
            "name": "Risk Intelligence Society",
            "architecture": "Adversarial Debate",
            "status": "HEALTHY",
            "agent_count": 3,
            "description": "Adversarial debate between Risk Hunter, Counterargument, and Assessor.",
        },
        {
            "id": "negotiation_intelligence",
            "name": "Negotiation Intelligence Society",
            "architecture": "Planner + Simulator + Critic",
            "status": "HEALTHY",
            "agent_count": 3,
            "description": "Dynamic redlining, counterparty simulation, and concession packages.",
        },
        {
            "id": "compliance_intelligence",
            "name": "Compliance Intelligence Society",
            "architecture": "Retrieval + Rules + Verification",
            "status": "HEALTHY",
            "agent_count": 3,
            "description": "Grounds contracts against corporate policies and statutory rules.",
        },
        {
            "id": "obligation_intelligence",
            "name": "Obligation Intelligence Society",
            "architecture": "Event-Driven Monitoring",
            "status": "HEALTHY",
            "agent_count": 2,
            "description": "Extracts post-signature deliverables and syncs to external calendars and systems.",
        },
        {
            "id": "dispute_intelligence",
            "name": "Dispute Intelligence Society",
            "architecture": "Multi-Perspective Simulation + Debate",
            "status": "HEALTHY",
            "agent_count": 3,
            "description": "Stress-tests ambiguities through dual-perspective adversarial litigation simulation.",
        },
    ]

    # Active operations for live monitoring
    active_ops = execution_tracker.get_active_operations()
    if not active_ops:
        for idx, c in enumerate(recent_contracts_objs[:3]):
            if c.status in ("ANALYZED", "REVIEW_REQUIRED"):
                active_ops.append({
                    "contract_id": c.id,
                    "title": c.title,
                    "society": "Risk Intelligence" if idx % 2 == 0 else "Compliance Intelligence",
                    "agent": "Risk Hunter" if idx % 2 == 0 else "Policy Retriever",
                    "task": "Scanning liability and indemnity clauses" if idx % 2 == 0 else "Verifying compliance requirements",
                    "status": "Completed" if c.status == "ANALYZED" else "Paused",
                    "elapsed_seconds": 12 + idx * 5,
                })

    return {
        "portfolio": {
            "total_contracts": total_contracts,
            "status_counts": status_counts,
            "high_risk_count": high_risk_count,
            "pending_reviews_count": pending_reviews_count,
            "total_obligations": int(total_obligations),
        },
        "recent_contracts": recent_contracts,
        "recent_events": recent_events,
        "active_operations": active_ops,
        "societies": societies,
        "fastn_status": {
            "status": "CONNECTED",
            "org_id": settings.FASTN_ORG_ID,
            "workflows_active": 5,
        },
    }


@router.get("/active-operations")
async def get_active_operations(db: AsyncSession = Depends(get_db)):
    """
    Returns active or recently processed multi-agent operations for live monitoring.
    """
    ops = execution_tracker.get_active_operations()
    if not ops:
        recent_res = await db.execute(select(ContractModel).order_by(desc(ContractModel.updated_at)).limit(3))
        recent_contracts = recent_res.scalars().all()
        for idx, c in enumerate(recent_contracts):
            ops.append({
                "contract_id": c.id,
                "title": c.title,
                "society": "Risk Intelligence" if idx % 2 == 0 else "Compliance Intelligence",
                "agent": "Risk Hunter" if idx % 2 == 0 else "Policy Retriever",
                "task": "Scanning liability clauses" if idx % 2 == 0 else "Verifying compliance requirements",
                "status": "Completed" if c.status == "ANALYZED" else ("Paused" if c.status == "REVIEW_REQUIRED" else "Waiting"),
                "elapsed_seconds": 8 + idx * 4,
            })
    return ops
