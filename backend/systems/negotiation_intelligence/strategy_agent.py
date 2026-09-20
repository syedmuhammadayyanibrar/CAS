from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.negotiation_intelligence.planner import DraftPositionDTO
from backend.core.logging import get_logger

logger = get_logger("StrategyAgent")


class StrategizedPositionDTO(BaseModel):
    clause_reference: str
    clause_title: str
    leverage_point: str
    negotiation_priority: int  # 1 = highest priority
    opening_argument: str


class StrategyResponse(BaseModel):
    strategized_positions: List[StrategizedPositionDTO] = Field(default_factory=list)
    suggested_sequence: List[str] = Field(default_factory=list)
    tactical_framing: str = ""


class StrategyAgent:
    """
    Second agent in the Negotiation pipeline.
    Determines negotiation sequencing, leverage points, and tactical opening arguments.
    """

    @staticmethod
    async def develop_strategy(
        draft_positions: List[DraftPositionDTO],
        commercial_objective: str
    ) -> StrategyResponse:
        positions_str = "\n".join([
            f"- [{p.clause_reference}] {p.clause_title}: Target='{p.desired_outcome}', RedLine='{p.red_line}'"
            for p in draft_positions
        ])

        prompt = (
            "You are the Strategy Agent in a Negotiation Intelligence System.\n"
            f"Objective: {commercial_objective}\n\n"
            "Formulate the negotiation tactics and sequencing for these positions.\n"
            "For each position:\n"
            "- Identify the strongest leverage point (e.g. annual contract value, competitor alternatives, market standard)\n"
            "- Assign negotiation_priority (1 to 5)\n"
            "- Draft a persuasive opening argument\n"
            "- Propose the optimal negotiation sequence across all clauses\n\n"
            f"TARGET POSITIONS:\n{positions_str}\n"
        )

        result: StrategyResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=StrategyResponse,
            system_instruction="You are a master commercial negotiator and tactical strategist."
        )

        logger.info(f"Strategy Agent prepared tactical framing and sequencing for {len(result.strategized_positions)} positions.")
        return result
