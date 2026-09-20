from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.core.logging import get_logger

logger = get_logger("ComplianceConflictDetector")


class ClauseConflictDTO(BaseModel):
    clause_a_ref: str
    clause_b_ref: str
    conflict_type: str  # DIRECT_CONTRADICTION, ASYMMETRIC_STANDARD, LATENT_AMBIGUITY
    description: str
    compliance_impact: str


class ConflictDetectionResponse(BaseModel):
    conflicts: List[ClauseConflictDTO] = Field(default_factory=list)
    conflict_notes: str = ""


class ComplianceConflictDetector:
    """
    Detects internal contradictions between different contract clauses
    or conflicts between contract terms and operational policy standards.
    """

    @staticmethod
    async def detect_conflicts(contract_text: str) -> List[ClauseConflictDTO]:
        prompt = (
            "You are the Conflict Detector agent in a Compliance Intelligence System.\n"
            "Analyze the contract to detect internal contradictions, inconsistent deadlines, "
            "or conflicting obligations between different sections (for example, conflicting notice periods for termination "
            "between Section 9.1 and Section 9.3, or conflicting IP rights).\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text[:4000])

        result: ConflictDetectionResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=ConflictDetectionResponse,
            system_instruction="You are an expert contract conflict and inconsistency auditor."
        )

        logger.info(f"Conflict Detector identified {len(result.conflicts)} clause conflict(s).")
        return result.conflicts
