from typing import List, Dict
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.systems.compliance_intelligence.analyzer import EvaluatedRuleDTO
from backend.core.logging import get_logger

logger = get_logger("ComplianceEvidenceAgent")


class VerifiedComplianceEvidenceDTO(BaseModel):
    rule_id: str
    is_verbatim_quote_accurate: bool
    citation_text: str
    notes: str


class ComplianceEvidenceResponse(BaseModel):
    verified_evidence: List[VerifiedComplianceEvidenceDTO] = Field(default_factory=list)


class ComplianceEvidenceAgent:
    """
    Evidence Agent for Compliance Intelligence.
    Ensures that every compliance violation or pass finding is backed by verified,
    verbatim contractual citations.
    """

    @staticmethod
    async def verify_compliance_evidence(
        evaluations: List[EvaluatedRuleDTO],
        contract_text: str
    ) -> Dict[str, VerifiedComplianceEvidenceDTO]:
        claims_str = "\n".join([
            f"- Rule: {e.rule_id} | Status: {e.compliance_status} | Cited: '{e.contract_evidence}'"
            for e in evaluations
        ])

        prompt = (
            "You are the Compliance Evidence Agent.\n"
            "Verify that every cited contract quote exists verbatim in the contract text.\n"
            "Flag any misattributions or hallucinations.\n\n"
            f"CITATIONS TO VERIFY:\n{claims_str}\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text[:4000])

        result: ComplianceEvidenceResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=ComplianceEvidenceResponse,
            system_instruction="You are a strict legal citation and text verification auditor."
        )

        lookup = {v.rule_id: v for v in result.verified_evidence}
        logger.info(f"Compliance Evidence Agent verified {len(lookup)} rule citations.")
        return lookup
