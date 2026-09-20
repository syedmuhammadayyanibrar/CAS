from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Party(BaseModel):
    id: str
    name: str
    role: str  # e.g., "Customer", "Vendor", "Provider", "Licensee"
    jurisdiction: Optional[str] = None
    entity_type: Optional[str] = "Corporation"


class Clause(BaseModel):
    id: str
    section_number: str
    title: str
    text: str
    clause_type: str  # LIABILITY, INDEMNITY, TERMINATION, PAYMENT, CONFIDENTIALITY, IP, SLA, GOVERNING_LAW, RENEWAL, AUDIT, OTHER
    is_unusual: bool = False
    unusual_reason: Optional[str] = None
    summary: Optional[str] = None


class Obligation(BaseModel):
    id: str
    party_name: str
    clause_id: Optional[str] = None
    title: str
    description: str
    obligation_type: str  # PAYMENT, DELIVERABLE, REPORTING, NOTICE, RENEWAL, SERVICE_LEVEL, CONFIDENTIALITY
    frequency: str = "ONE_TIME"  # ONE_TIME, MONTHLY, QUARTERLY, ANNUAL, ON_EVENT
    due_date: Optional[str] = None
    notice_days: Optional[int] = None
    penalty_summary: Optional[str] = None


class Deadline(BaseModel):
    id: str
    obligation_id: Optional[str] = None
    title: str
    due_date: str
    is_critical: bool = False
    reminder_days: int = 14
    description: Optional[str] = None


class ContractGraph(BaseModel):
    """Normalized Contract Knowledge Graph representing the structural contract model."""
    contract_id: str
    title: str
    parties: List[Party] = Field(default_factory=list)
    clauses: List[Clause] = Field(default_factory=list)
    obligations: List[Obligation] = Field(default_factory=list)
    deadlines: List[Deadline] = Field(default_factory=list)
    renewals: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    governing_law: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    raw_character_count: int = 0
