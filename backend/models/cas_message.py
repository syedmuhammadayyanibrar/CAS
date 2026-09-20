import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class CASMessage(BaseModel):
    """
    Universal society communication protocol envelope.
    Enforces standardized inter-society and Director message passing.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contract_id: str
    source_system: str
    target_system: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    priority: str = Field(default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        contract_id: str,
        source_system: str,
        target_system: str,
        event_type: str,
        payload: dict[str, Any],
        evidence_refs: Optional[List[str]] = None,
        confidence: float = 1.0,
        priority: str = "MEDIUM"
    ) -> "CASMessage":
        return cls(
            contract_id=contract_id,
            source_system=source_system,
            target_system=target_system,
            event_type=event_type,
            payload=payload,
            evidence_refs=evidence_refs or [],
            confidence=confidence,
            priority=priority,
        )
