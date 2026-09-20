from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.core.logging import get_logger

logger = get_logger("AmbiguityDetector")


class AmbiguousClauseDTO(BaseModel):
    clause_reference: str
    clause_text: str
    ambiguity_type: str  # VAGUE_STANDARD, CONFLICTING_TERMS, ASYMMETRIC_OBLIGATION, MISSING_DEFINITION, UNILATERAL_DISCRETION
    vague_phrase: str
    risk_of_differing_interpretations: str


class AmbiguityDetectionResponse(BaseModel):
    ambiguities: List[AmbiguousClauseDTO] = Field(default_factory=list)


class AmbiguityDetector:
    """
    Scans the contract for vague standards, conflicting terms, unilateral discretion,
    and missing definitions that create fertile ground for future legal disputes.
    """

    @staticmethod
    async def detect_ambiguities(contract_text: str) -> List[AmbiguousClauseDTO]:
        prompt = (
            "You are the Ambiguity Detector in a Dispute Intelligence System.\n"
            "Analyze the contract text to discover clauses with high potential for legal conflict.\n"
            "Look specifically for:\n"
            "- Vague phrases ('commercially reasonable efforts', 'system stability', 'reasonable care')\n"
            "- Conflicting notice periods (e.g., 30-day cure vs 10-day summary termination)\n"
            "- Unilateral vendor discretion (e.g. price increases up to 15% without consent)\n"
            "- Asymmetric indemnification or liability carveouts\n"
            "- Ambiguous SLA downtime exclusions\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text[:4000])

        result: AmbiguityDetectionResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=AmbiguityDetectionResponse,
            system_instruction="You are a litigator specializing in contractual ambiguity and interpretation disputes."
        )

        logger.info(f"Ambiguity Detector identified {len(result.ambiguities)} dispute-prone clause(s).")
        return result.ambiguities
