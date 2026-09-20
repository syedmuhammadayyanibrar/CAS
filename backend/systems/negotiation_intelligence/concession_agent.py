from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.negotiation_intelligence.planner import DraftPositionDTO
from backend.systems.negotiation_intelligence.counterparty_simulator import CounterpartySimulationResponse
from backend.core.logging import get_logger

logger = get_logger("ConcessionAgent")


class ConcessionPackageDTO(BaseModel):
    clause_reference: str
    proposed_concession: str  # What Customer can concede
    cost_to_customer: str  # LOW, MEDIUM, HIGH
    value_to_vendor: str  # LOW, MEDIUM, HIGH
    trade_off_clause: str  # Which customer priority this concession unlocks


class ConcessionResponse(BaseModel):
    concessions: List[ConcessionPackageDTO] = Field(default_factory=list)


class ConcessionAgent:
    """
    Agent responsible for designing asymmetric concessions:
    items of low cost to our organization but high perceived value to the counterparty.
    """

    @staticmethod
    async def design_concessions(
        draft_positions: List[DraftPositionDTO],
        simulation: CounterpartySimulationResponse
    ) -> List[ConcessionPackageDTO]:
        context = []
        for p in draft_positions:
            rebuttal = next((r for r in simulation.rebuttals if r.clause_reference == p.clause_reference), None)
            pushback = rebuttal.vendor_pushback_argument if rebuttal else "Standard pushback"
            context.append(f"Position: {p.clause_reference} ({p.clause_title}) | Vendor Pushback: {pushback}")

        prompt = (
            "You are the Concession Agent in a Negotiation Intelligence System.\n"
            "Given the counterparty's simulated pushbacks, design calculated concession packages.\n"
            "Identify concessions that Customer can offer that cost Customer very little but provide significant "
            "value or assurance to Vendor (e.g., agreeing to prompt payment discount, offering a multi-year commitment in exchange for mutual liability caps, or providing a co-marketing quote).\n\n"
            f"OPPOSITION POINTS:\n" + "\n".join(context)
        )

        result: ConcessionResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=ConcessionResponse,
            system_instruction="You are an expert game-theoretic concession planner."
        )

        logger.info(f"Concession Agent planned {len(result.concessions)} strategic concessions.")
        return result.concessions
