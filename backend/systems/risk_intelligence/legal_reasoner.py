from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.systems.risk_intelligence.hunter import RawRiskFindingDTO
from backend.core.logging import get_logger

logger = get_logger("LegalReasoner")


class StructuredLegalRiskDTO(BaseModel):
    clause_reference: str
    clause_title: str
    exposed_party: str
    legal_doctrine_or_exposure: str
    consequence_scenario: str
    why_dangerous: str
    preliminary_severity: str


class LegalReasonerResponse(BaseModel):
    reasoned_risks: List[StructuredLegalRiskDTO] = Field(default_factory=list)


class LegalReasoner:
    """
    Second agent in the Adversarial Debate pipeline.
    Deepens the Risk Hunter's findings by articulating rigorous legal doctrines,
    causal chains, and concrete damage scenarios.
    """

    @staticmethod
    async def reason_risks(raw_risks: List[RawRiskFindingDTO], contract_text: str) -> List[StructuredLegalRiskDTO]:
        risks_summary = "\n".join([
            f"- Ref: {r.clause_reference} | Title: {r.clause_title} | Concern: {r.initial_concern} | Quote: '{r.verbatim_quote}'"
            for r in raw_risks
        ])

        prompt = (
            "You are the Legal Reasoner agent in an Adversarial Risk Intelligence System.\n"
            "Review the preliminary risks discovered by the Risk Hunter and develop formal legal risk cases for each.\n"
            "For each risk, specify:\n"
            "- Who is exposed (Customer, Vendor, Both)\n"
            "- The legal doctrine or risk category\n"
            "- The concrete worst-case consequence scenario\n"
            "- Why the term is dangerous in practice\n"
            "- Preliminary severity (LOW, MEDIUM, HIGH, CRITICAL)\n\n"
            f"PRELIMINARY RISKS DETECTED:\n{risks_summary}\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text[:4000])

        result: LegalReasonerResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=LegalReasonerResponse,
            system_instruction="You are a senior corporate counsel specializing in commercial liability and contract disputes."
        )

        logger.info(f"Legal Reasoner structured {len(result.reasoned_risks)} formal risk arguments.")
        return result.reasoned_risks
