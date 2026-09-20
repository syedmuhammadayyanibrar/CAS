from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class MeshEventType(str, Enum):
    CONTRACT_INTAKE = "CONTRACT_INTAKE"
    CONTRACT_PARSED = "CONTRACT_PARSED"
    RISK_EVALUATED = "RISK_EVALUATED"
    RISK_ESCALATED = "RISK_ESCALATED"
    COMPLIANCE_CHECKED = "COMPLIANCE_CHECKED"
    NEGOTIATION_PLANNED = "NEGOTIATION_PLANNED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    CONTRACT_SIGNED = "CONTRACT_SIGNED"
    OBLIGATION_TICK = "OBLIGATION_TICK"
    RENEWAL_WARNING = "RENEWAL_WINDOW_OPEN"
    DISPUTE_SIMULATED = "DISPUTE_SIMULATED"
    HUMAN_DECISION_RECEIVED = "HUMAN_DECISION_RECEIVED"


class FastnWebhookPayload(BaseModel):
    contractId: Optional[str] = None
    documentName: Optional[str] = "contract.pdf"
    content: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = "fastn_webhook"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    audit_id: str
    contract_id: Optional[str] = None
    society_or_source: str
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
