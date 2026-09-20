from typing import List, Dict
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.systems.risk_intelligence.counterargument import DebatedRiskDTO
from backend.core.logging import get_logger

logger = get_logger("EvidenceVerifier")


class VerifiedEvidenceDTO(BaseModel):
    clause_reference: str
    is_grounded_in_text: bool
    verbatim_text_found: str
    hallucination_detected: bool = False
    citation_confidence: float = 1.0


class EvidenceVerificationResponse(BaseModel):
    verifications: List[VerifiedEvidenceDTO] = Field(default_factory=list)


class EvidenceVerifier:
    """
    Evidence Verification Agent in the Risk Intelligence System.
    Verifies that the contractual text cited in the debate actually exists verbatim
    in the contract document, rejecting hallucinated clauses.
    """

    @staticmethod
    async def verify_evidence(
        debated_risks: List[DebatedRiskDTO],
        contract_text: str
    ) -> Dict[str, VerifiedEvidenceDTO]:
        claims_summary = "\n".join([
            f"- Ref: {r.clause_reference} | Title: {r.clause_title} | Claim: {r.hunter_claim}"
            for r in debated_risks
        ])

        prompt = (
            "You are the Evidence Verifier agent in a Risk Intelligence System.\n"
            "Audit the alleged risk claims against the verbatim contract text.\n"
            "For each clause reference, verify:\n"
            "1. Is the clause actually present in the contract?\n"
            "2. Extract the exact verbatim text.\n"
            "3. Flag any hallucinated text or misquoted terms.\n"
            "4. Provide a citation confidence score (0.0 to 1.0).\n\n"
            f"CLAIMS TO VERIFY:\n{claims_summary}\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text[:4000])

        result: EvidenceVerificationResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=EvidenceVerificationResponse,
            system_instruction="You are a strict textual and evidentiary verification officer."
        )

        lookup = {v.clause_reference: v for v in result.verifications}
        logger.info(f"Evidence Verifier validated {len(lookup)} evidence citations.")
        return lookup
