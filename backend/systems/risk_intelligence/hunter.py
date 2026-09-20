from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.core.logging import get_logger

logger = get_logger("RiskHunter")


class RawRiskFindingDTO(BaseModel):
    clause_reference: str
    clause_title: str
    risk_category: str  # LIABILITY, INDEMNITY, TERMINATION, FINANCIAL, IP, OPERATIONAL
    initial_concern: str
    preliminary_severity: str = "HIGH"  # LOW, MEDIUM, HIGH, CRITICAL
    verbatim_quote: str


class RiskHuntResponse(BaseModel):
    raw_risks: List[RawRiskFindingDTO] = Field(default_factory=list)


class RiskHunter:
    """
    First agent in the Adversarial Debate pipeline.
    Hunts aggressively for any clause that could expose the organization to legal,
    financial, or operational risk.
    """

    @staticmethod
    async def hunt_risks(contract_text: str) -> List[RawRiskFindingDTO]:
        prompt = (
            "You are the Risk Hunter agent in an Adversarial Risk Intelligence System.\n"
            "Scan the following contract aggressively to discover all potential risks, exposures, and one-sided terms.\n"
            "Focus on:\n"
            "1. Asymmetric or ultra-low liability caps (e.g. 1 month fees).\n"
            "2. Uncapped or one-sided indemnification obligations.\n"
            "3. Auto-renewal windows with short non-renewal notice periods.\n"
            "4. Conflicting or abrupt termination provisions.\n"
            "5. Broad grants of customer data for vendor model training or derivative works.\n"
            "6. Inadequate or exclusive remedies for SLA downtime.\n"
            "Quote the exact verbatim text for each risk found.\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text)

        result: RiskHuntResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=RiskHuntResponse,
            system_instruction="You are a hawkish commercial risk discovery specialist."
        )

        logger.info(f"Risk Hunter discovered {len(result.raw_risks)} potential risk candidate(s).")
        return result.raw_risks
