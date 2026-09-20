from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class ContractLifecycleState(str, Enum):
    INTAKE = "INTAKE"
    ANALYZING = "ANALYZING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NEGOTIATING = "NEGOTIATING"
    APPROVED = "APPROVED"
    SIGNED = "SIGNED"
    ACTIVE_MONITORING = "ACTIVE_MONITORING"
    RENEWAL_WINDOW = "RENEWAL_WINDOW"
    IN_DISPUTE = "IN_DISPUTE"
    COMPLETED = "COMPLETED"


class ContractLifecycleManager:
    """
    Tracks and enforces valid state transitions across the Contract Lifecycle.
    """

    VALID_TRANSITIONS = {
        ContractLifecycleState.INTAKE: [ContractLifecycleState.ANALYZING],
        ContractLifecycleState.ANALYZING: [
            ContractLifecycleState.REVIEW_REQUIRED,
            ContractLifecycleState.NEGOTIATING,
            ContractLifecycleState.APPROVED,
            ContractLifecycleState.SIGNED
        ],
        ContractLifecycleState.REVIEW_REQUIRED: [
            ContractLifecycleState.NEGOTIATING,
            ContractLifecycleState.APPROVED,
            ContractLifecycleState.ANALYZING
        ],
        ContractLifecycleState.NEGOTIATING: [
            ContractLifecycleState.REVIEW_REQUIRED,
            ContractLifecycleState.APPROVED,
            ContractLifecycleState.SIGNED
        ],
        ContractLifecycleState.APPROVED: [ContractLifecycleState.SIGNED],
        ContractLifecycleState.SIGNED: [ContractLifecycleState.ACTIVE_MONITORING],
        ContractLifecycleState.ACTIVE_MONITORING: [
            ContractLifecycleState.RENEWAL_WINDOW,
            ContractLifecycleState.IN_DISPUTE,
            ContractLifecycleState.COMPLETED
        ],
        ContractLifecycleState.RENEWAL_WINDOW: [
            ContractLifecycleState.NEGOTIATING,
            ContractLifecycleState.SIGNED,
            ContractLifecycleState.COMPLETED
        ],
        ContractLifecycleState.IN_DISPUTE: [
            ContractLifecycleState.ACTIVE_MONITORING,
            ContractLifecycleState.COMPLETED
        ],
        ContractLifecycleState.COMPLETED: []
    }

    @classmethod
    def can_transition(cls, current: ContractLifecycleState, target: ContractLifecycleState) -> bool:
        return target in cls.VALID_TRANSITIONS.get(current, [])
