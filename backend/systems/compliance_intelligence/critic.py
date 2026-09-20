from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.compliance_intelligence.analyzer import EvaluatedRuleDTO
from backend.core.logging import get_logger

logger = get_logger("ComplianceCritic")


class ComplianceCritiqueResponse(BaseModel):
    is_audit_defensible: bool = True
    critique_notes: str = ""
    disputed_findings: List[str] = Field(default_factory=list)
    confidence_calibration: float = 0.95


class ComplianceCritic:
    """
    Critic Agent for Compliance Intelligence.
    Audits the compliance determinations to ensure they are strictly grounded in policy rules
    and that no hallucinated regulatory standards were introduced.
    """

    @staticmethod
    async def review_audit(
        evaluations: List[EvaluatedRuleDTO],
        policy_name: str
    ) -> ComplianceCritiqueResponse:
        findings_str = "\n".join([
            f"- Rule {e.rule_id}: Status={e.compliance_status}, Reason={e.reason}, Rec={e.recommended_action}"
            for e in evaluations
        ])

        prompt = (
            "You are the Compliance Critic in a Compliance Intelligence System.\n"
            f"Policy: {policy_name}\n\n"
            "Review the compliance determinations below.\n"
            "Check for:\n"
            "1. Did the analyzer introduce any external regulatory assumptions not present in the policy?\n"
            "2. Are all violations genuinely substantiated by the contract quotes?\n"
            "3. Are recommended actions proportional and legally precise?\n\n"
            f"DETERMINATIONS:\n{findings_str}\n"
        )

        result: ComplianceCritiqueResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=ComplianceCritiqueResponse,
            system_instruction="You are a Chief Compliance Officer quality assurance critic."
        )

        logger.info(f"Compliance Critic confirmed audit defensibility: {result.is_audit_defensible}")
        return result
