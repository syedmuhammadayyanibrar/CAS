from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.negotiation_intelligence.planner import DraftPositionDTO
from backend.systems.negotiation_intelligence.counterparty_simulator import CounterpartySimulationResponse
from backend.systems.negotiation_intelligence.strategy_agent import StrategyResponse
from backend.core.logging import get_logger

logger = get_logger("StrategyCritic")


class StrategyCritique(BaseModel):
    is_strategy_viable: bool
    vulnerabilities_found: List[str] = Field(default_factory=list)
    unrealistic_demands: List[str] = Field(default_factory=list)
    critic_counter_recommendations: List[str] = Field(default_factory=list)
    overall_critique_summary: str = ""


class StrategyCritic:
    """
    Adversarial Critic for Negotiation Intelligence.
    Attacks the proposed strategy, identifies unrealistic demands,
    and warns where the strategy risks derailing the deal entirely.
    """

    @staticmethod
    async def critique_strategy(
        draft_positions: List[DraftPositionDTO],
        strategy: StrategyResponse,
        simulation: CounterpartySimulationResponse
    ) -> StrategyCritique:
        context = []
        for p in draft_positions:
            context.append(f"- Position {p.clause_reference}: Desired='{p.desired_outcome}', RedLine='{p.red_line}'")

        prompt = (
            "You are the Strategy Critic in a Negotiation Intelligence System.\n"
            "Your job is to AGGRESSIVELY ATTACK the proposed negotiation strategy.\n"
            "Identify:\n"
            "1. Any unrealistic demands that could lead to deal deadlock.\n"
            "2. Gaps where Customer gives up too much or asks for commercially irrational terms.\n"
            "3. Flaws in the proposed sequence.\n"
            "4. Constructive revisions to make the strategy battle-tested.\n\n"
            f"STRATEGY SEQUENCING: {strategy.suggested_sequence}\n"
            f"PROPOSED POSITIONS:\n" + "\n".join(context)
        )

        result: StrategyCritique = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=StrategyCritique,
            system_instruction="You are a ruthless red-team negotiation critic and deal auditor."
        )

        logger.info(f"Strategy Critic generated critique. Viable: {result.is_strategy_viable}")
        return result
