from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from backend.database.db import get_db
from backend.database.schema import CASMessageModel, AuditEventModel, HumanReviewModel, CASMemoryModel
from backend.memory.cas_memory import cas_memory

from datetime import datetime, timezone
from pydantic import BaseModel
from backend.database.schema import ContractModel
from backend.memory.feedback_loops import feedback_loops
from backend.models.hitl import HumanDecision

router = APIRouter(tags=["Audit & Observability"])


class ResolveReviewRequest(BaseModel):
    decision: str  # "APPROVE", "REJECT", "REQUEST_REDLINE"
    reviewer_id: Optional[str] = "general_counsel@acme.com"
    decision_notes: Optional[str] = "Approved after legal risk review."


@router.get("/events")
async def list_cas_events(
    contract_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves chronological CASMessage event log across all societies."""
    stmt = select(CASMessageModel)
    if contract_id:
        stmt = stmt.where(CASMessageModel.contract_id == contract_id)
    stmt = stmt.order_by(CASMessageModel.created_at.desc()).limit(limit)

    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "event_id": r.event_id,
            "contract_id": r.contract_id,
            "source": r.source_system,
            "target": r.target_system,
            "event_type": r.event_type,
            "priority": r.priority,
            "confidence": r.confidence,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in records
    ]


@router.get("/audit")
async def list_audit_trail(
    contract_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves immutable audit trail of agent operations and director decisions."""
    stmt = select(AuditEventModel)
    if contract_id:
        stmt = stmt.where(AuditEventModel.contract_id == contract_id)
    stmt = stmt.order_by(AuditEventModel.timestamp.desc()).limit(limit)

    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "audit_id": r.audit_id,
            "contract_id": r.contract_id,
            "source": r.society_or_source,
            "action": r.action,
            "details": r.details_json,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None
        }
        for r in records
    ]


@router.get("/reviews")
async def list_human_reviews(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists pending or completed Human-In-The-Loop review requests."""
    stmt = select(HumanReviewModel)
    if status:
        stmt = stmt.where(HumanReviewModel.status == status)
    stmt = stmt.order_by(HumanReviewModel.created_at.desc())

    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "review_id": r.review_id,
            "contract_id": r.contract_id,
            "reason": r.reason,
            "status": r.status,
            "reviewer_id": r.reviewer_id,
            "decision_notes": r.decision_notes,
            "review_data": r.review_json,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None
        }
        for r in records
    ]


@router.post("/reviews/{review_id}/resolve")
async def resolve_human_review(
    review_id: str,
    req: ResolveReviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """Resolves a pending Human-In-The-Loop review, updates the contract, and logs to CAS memory."""
    review = await db.get(HumanReviewModel, review_id)
    if not review:
        raise HTTPException(status_code=404, detail=f"Review {review_id} not found")

    review.status = req.decision
    review.reviewer_id = req.reviewer_id
    review.decision_notes = req.decision_notes
    review.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    decision = HumanDecision(
        review_id=review_id,
        decision=req.decision,
        reviewer_id=req.reviewer_id or "reviewer",
        decision_notes=req.decision_notes or ""
    )
    await feedback_loops.record_human_decision(db, review.contract_id, decision)

    contract = await db.get(ContractModel, review.contract_id)
    if contract:
        if req.decision == "APPROVE":
            contract.status = "APPROVED"
        elif req.decision == "REJECT":
            contract.status = "REJECTED"
        elif req.decision == "REQUEST_REDLINE":
            contract.status = "REDLINING"
        await db.commit()

    return {
        "status": "RESOLVED",
        "review_id": review_id,
        "decision": req.decision,
        "contract_id": review.contract_id
    }


@router.get("/memory")
async def search_memory(
    tags: Optional[str] = Query(None, description="Comma-separated tags (e.g. indemnity,delaware,dispute)"),
    memory_type: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Queries persistent PostgreSQL CAS memory for historical precedents."""
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        memories = await cas_memory.retrieve_relevant_memories(
            session=db,
            tags=tag_list,
            memory_type=memory_type,
            limit=limit
        )
        return {"query_tags": tag_list, "results_count": len(memories), "memories": memories}
    else:
        # Return recent memories from CASMemoryModel
        stmt = select(CASMemoryModel).order_by(CASMemoryModel.created_at.desc()).limit(limit)
        if memory_type:
            stmt = stmt.where(CASMemoryModel.memory_type == memory_type)
        res = await db.execute(stmt)
        records = res.scalars().all()
        memories = [
            {
                "id": r.id,
                "memory_type": r.memory_type,
                "reference_id": r.reference_id,
                "title": r.title,
                "content": r.content_json,
                "context_tags": r.context_tags,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
        return {"query_tags": [], "results_count": len(memories), "memories": memories}
