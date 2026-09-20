from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.negotiation_intelligence.planner import DraftPositionDTO
from backend.systems.negotiation_intelligence.counterparty_simulator import CounterpartySimulationResponse
from backend.core.logging import get_logger

logger = get_logger("GameTheoreticReasoner")


class GameTheoreticAnalysis(BaseModel):
    customer_batna: str  # Best alternative to negotiated agreement
    vendor_batna: str
    zopa_summary: str  # Zone of Possible Agreement
    strategic_balance_of_power: str  # CUSTOMER_FAVORED, BALANCED, VENDOR_FAVORED
    walk_away_conditions: List[str] = Field(default_factory=list)


class GameTheoreticReasoner:
    """
    Analyzes bargaining power, BATNA, reservation prices, and Nash equilibrium boundaries.
    """

    @staticmethod
    async def analyze_dynamics(
        draft_positions: List[DraftPositionDTO],
        simulation: CounterpartySimulationResponse,
        contract_value_annual: float = 240000.0
    ) -> GameTheoreticAnalysis:
        prompt = (
            "You are the Game-Theoretic Reasoner in a Negotiation Intelligence System.\n"
            f"Annual Contract Value: ${contract_value_annual:,.2f}\n"
            f"Vendor Stance: {simulation.vendor_overall_stance}\n\n"
            "Analyze the game-theoretic balance of power:\n"
            "1. What is Customer's BATNA if negotiations stall?\n"
            "2. What is Vendor's BATNA (cost of losing customer / pipeline metrics)?\n"
            "3. What is the ZOPA (Zone of Possible Agreement)?\n"
            "4. What are the definitive walk-away conditions?\n"
        )

        result: GameTheoreticAnalysis = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=GameTheoreticAnalysis,
            system_instruction="You are a game theorist and strategic bargaining analyst."
        )

        logger.info(f"Game-Theoretic Reasoner assessed power balance: {result.strategic_balance_of_power}")
        return result
