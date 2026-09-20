from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class HumanReviewRequest(BaseModel):
    """
    Human-In-The-Loop review request.
    Explains WHY review is required, WHAT agents concluded, WHERE they disagreed,
    WHAT evidence supports each, and WHAT action is being requested.
    """
    review_id: str = Field(default_factory=lambda: f"REV-{uuid.uuid4().hex[:8].upper()}")
    contract_id: str
    trigger_source: str  # e.g., "RISK_INTELLIGENCE", "DIRECTOR_CONFLICT_RESOLVER"
    reason_for_review: str
    agent_conclusions: Dict[str, str] = Field(
        default_factory=dict,
        description="System/Agent -> conclusion summary"
    )
    disagreement_matrix: Optional[str] = None
    evidence_citations: List[str] = Field(default_factory=list)
    action_requested: str  # e.g., "Approve proposed indemnity cap exception", "Resolve Risk vs Negotiation clash"
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, MODIFIED
    reviewer_id: Optional[str] = None
    decision_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None


class HumanDecision(BaseModel):
    review_id: str
    decision: str  # APPROVE, REJECT, MODIFY
    reviewer_id: str
    decision_notes: str
    override_instructions: Optional[str] = None
