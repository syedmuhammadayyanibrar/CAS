from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.systems.risk_intelligence.legal_reasoner import StructuredLegalRiskDTO
from backend.core.logging import get_logger

logger = get_logger("CounterargumentAgent")


class DebatedRiskDTO(BaseModel):
    clause_reference: str
    clause_title: str
    hunter_claim: str
    counterargument: str  # Actively produced rebuttal
    counterargument_strength: str = "MODERATE"  # WEAK, MODERATE, STRONG
    mitigating_factors: str
    is_risk_weakened_or_disproven: bool = False
    rebuttal_notes: str


class CounterargumentResponse(BaseModel):
    debated_risks: List[DebatedRiskDTO] = Field(default_factory=list)


class CounterargumentAgent:
    """
    CRITICAL ADVERSARIAL AGENT in the Risk Intelligence System.
    Must actively attempt to disprove, weaken, or challenge the detected risk.
    Argues industry norms, statutory constraints, context in other sections,
    and business reality to prevent false alarms and exaggerated severities.
    """

    @staticmethod
    async def attack_risks(
        reasoned_risks: List[StructuredLegalRiskDTO],
        contract_text: str
    ) -> List[DebatedRiskDTO]:
        risks_case = "\n".join([
            f"- Clause: {r.clause_reference} ({r.clause_title})\n"
            f"  Exposed: {r.exposed_party} | Severity: {r.preliminary_severity}\n"
            f"  Argument: {r.why_dangerous}\n"
            f"  Consequence: {r.consequence_scenario}\n"
            for r in reasoned_risks
        ])

        prompt = (
            "You are the Counterargument Agent in an Adversarial Risk Intelligence System.\n"
            "Your explicit mandate is to ADVERSARIALLY ATTACK AND WEAKEN every risk finding presented.\n"
            "Do NOT merely agree with the Hunter. You must actively defend the contract terms or find mitigating points.\n"
            "For each risk:\n"
            "1. Produce the strongest plausible counter-argument (e.g. standard market practice, statutory limitations, "
            "reciprocal business considerations, low commercial probability).\n"
            "2. Identify any mitigating factors in the text or business relationship.\n"
            "3. Assess your counter-argument strength (WEAK, MODERATE, STRONG).\n"
            "4. Decide whether the alleged risk is significantly weakened or disproven.\n\n"
            f"ALLEGED RISKS TO ATTACK:\n{risks_case}\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text[:4000])

        result: CounterargumentResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=CounterargumentResponse,
            system_instruction="You are a formidable defense counsel and commercial negotiator attacking risk allegations."
        )

        logger.info(f"Counterargument Agent attacked {len(result.debated_risks)} risk findings.")
        return result.debated_risks
