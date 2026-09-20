from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.negotiation_intelligence.planner import DraftPositionDTO
from backend.core.logging import get_logger

logger = get_logger("CounterpartySimulator")


class SimulatedRebuttalDTO(BaseModel):
    clause_reference: str
    vendor_acceptance_probability: float  # 0.0 to 1.0
    vendor_pushback_argument: str
    expected_counter_demand: str
    likely_compromise_zone: str


class CounterpartySimulationResponse(BaseModel):
    rebuttals: List[SimulatedRebuttalDTO] = Field(default_factory=list)
    vendor_overall_stance: str = "RESISTANT"  # COOPERATIVE, RESISTANT, AGGRESSIVE


class CounterpartySimulator:
    """
    CRITICAL SIMULATION AGENT in Negotiation Intelligence.
    Adopts the persona and economic incentives of the opposing counterparty (e.g. SaaS Vendor).
    Simulates realistic counterparty reactions, pushbacks, and counter-demands.
    """

    @staticmethod
    async def simulate_reactions(
        draft_positions: List[DraftPositionDTO],
        vendor_name: str = "Vendor"
    ) -> CounterpartySimulationResponse:
        proposals_str = "\n".join([
            f"- Clause: {p.clause_reference} ({p.clause_title})\n"
            f"  Customer Demand: {p.desired_outcome}\n"
            f"  Proposed Redline: {p.proposed_counter_clause}\n"
            for p in draft_positions
        ])

        prompt = (
            f"You are the Counterparty Simulator adopting the persona of General Counsel for {vendor_name}.\n"
            "Your objective is to fiercely defend your company's margins, risk profile, and standard terms.\n"
            "For each proposed customer redline:\n"
            "1. State your likely acceptance probability (0.0 to 1.0).\n"
            "2. Give your realistic pushback argument (e.g., 'Our reinsurance policy prohibits uncapped caps', '12 months exceeds standard tiers').\n"
            "3. State your expected counter-demand or reciprocal condition.\n"
            "4. Identify the likely compromise zone where both parties might settle.\n\n"
            f"CUSTOMER REDLINE DEMANDS:\n{proposals_str}\n"
        )

        result: CounterpartySimulationResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=CounterpartySimulationResponse,
            system_instruction=f"You are the tough lead commercial negotiator representing {vendor_name}."
        )

        logger.info(f"Counterparty Simulator generated {len(result.rebuttals)} simulated vendor reactions.")
        return result
