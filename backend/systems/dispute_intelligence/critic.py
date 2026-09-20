from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.dispute_intelligence.conflict_simulator import SimulatedClashDTO
from backend.core.logging import get_logger

logger = get_logger("DisputeCritic")


class DisputeCritiqueResponse(BaseModel):
    are_scenarios_realistic: bool = True
    critique_notes: str = ""
    overstated_disputes: List[str] = Field(default_factory=list)
    overall_dispute_index: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CATASTROPHIC


class DisputeCritic:
    """
    Critic Agent for Dispute Intelligence.
    Audits the generated dispute scenarios to ensure they are plausible in real business practice
    and filters out far-fetched or overstated legal hypothetical traps.
    """

    @staticmethod
    async def critique_disputes(clashes: List[SimulatedClashDTO]) -> DisputeCritiqueResponse:
        clashes_str = "\n".join([
            f"- Ref: {c.clause_reference} | Trigger: {c.crisis_trigger} | Narrative: {c.dispute_narrative[:150]}"
            for c in clashes
        ])

        prompt = (
            "You are the Dispute Critic in a Dispute Intelligence System.\n"
            "Audit the simulated dispute scenarios below for commercial credibility and realism.\n"
            "1. Are these plausible scenarios that arise in real commercial practice?\n"
            "2. Are any scenarios overstated or hyperbolic?\n"
            "3. Assess the overall contractual dispute risk index (LOW, MEDIUM, HIGH, CATASTROPHIC).\n\n"
            f"SIMULATED SCENARIOS:\n{clashes_str}\n"
        )

        result: DisputeCritiqueResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=DisputeCritiqueResponse,
            system_instruction="You are a seasoned commercial dispute auditor evaluating scenario realism."
        )

        logger.info(f"Dispute Critic validated scenarios. Overall Index: {result.overall_dispute_index}")
        return result
