from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.negotiation_intelligence.planner import DraftPositionDTO
from backend.systems.negotiation_intelligence.strategy_agent import StrategyResponse
from backend.systems.negotiation_intelligence.counterparty_simulator import CounterpartySimulationResponse
from backend.systems.negotiation_intelligence.concession_agent import ConcessionPackageDTO
from backend.systems.negotiation_intelligence.critic import StrategyCritique
from backend.models.findings import NegotiationPosition, NegotiationStrategy
from backend.core.logging import get_logger

logger = get_logger("FinalNegotiationAdvisor")


class RedlineRecommendationDTO(BaseModel):
    clause_reference: str
    final_recommended_redline: str
    rationale: str


class AdvisorSynthesisResponse(BaseModel):
    final_redlines: List[RedlineRecommendationDTO] = Field(default_factory=list)
    executive_strategy_memo: str = ""


class FinalNegotiationAdvisor:
    """
    Final synthesis agent in the Negotiation Intelligence System.
    Reconciles the Planner's targets, the Counterparty pushbacks, the Concession packages,
    and the Critic's objections into a ready-to-execute Negotiation Strategy with exact redlines.
    """

    @staticmethod
    async def formulate_final_strategy(
        contract_id: str,
        commercial_objective: str,
        draft_positions: List[DraftPositionDTO],
        strategy: StrategyResponse,
        simulation: CounterpartySimulationResponse,
        concessions: List[ConcessionPackageDTO],
        critique: StrategyCritique
    ) -> NegotiationStrategy:
        rebuttal_map = {r.clause_reference: r for r in simulation.rebuttals}
        strat_map = {s.clause_reference: s for s in strategy.strategized_positions}
        concession_map = {c.clause_reference: c for c in concessions}

        prompt = (
            "You are the Final Negotiation Advisor in a Negotiation Intelligence System.\n"
            f"Objective: {commercial_objective}\n"
            f"Critic Notes: {critique.overall_critique_summary}\n\n"
            "Produce the final, polished, legally precise counter-proposal redline text for each position below.\n"
            "The redline text must be ready to insert directly into contract markups.\n"
        )
        for p in draft_positions:
            prompt += f"\n- Clause {p.clause_reference}: Target='{p.desired_outcome}', Initial Redline='{p.proposed_counter_clause}'"

        advisor_res: AdvisorSynthesisResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=AdvisorSynthesisResponse,
            system_instruction="You are a Chief Negotiation Officer formulating definitive contract counter-proposals."
        )

        redline_map = {r.clause_reference: r.final_recommended_redline for r in advisor_res.final_redlines}

        positions: List[NegotiationPosition] = []
        for idx, p in enumerate(draft_positions):
            rebuttal = rebuttal_map.get(p.clause_reference)
            strat = strat_map.get(p.clause_reference)
            conc = concession_map.get(p.clause_reference)

            positions.append(NegotiationPosition(
                position_id=f"POS-{idx+1:02d}",
                target_clause_id=p.clause_reference,
                clause_title=p.clause_title,
                desired_outcome=p.desired_outcome,
                acceptable_outcome=p.acceptable_outcome,
                fallback_position=conc.proposed_concession if conc else "Standard bilateral compromise",
                red_line=p.red_line,
                concession=conc.proposed_concession if conc else "None required",
                leverage=strat.leverage_point if strat else "Commercial volume and market benchmarks",
                counter_proposal=redline_map.get(p.clause_reference, p.proposed_counter_clause),
                simulated_counterparty_reaction=rebuttal.vendor_pushback_argument if rebuttal else "Expected initial resistance"
            ))

        strategy_obj = NegotiationStrategy(
            contract_id=contract_id,
            primary_objective=commercial_objective,
            positions=positions,
            negotiation_sequence=strategy.suggested_sequence or [p.clause_reference for p in draft_positions],
            strategy_summary=advisor_res.executive_strategy_memo or "Negotiation strategy finalized across key exposure areas.",
            critic_notes=critique.overall_critique_summary or "Reviewed and addressed adversarial critique.",
            requires_human_approval=True
        )

        logger.info(f"Final Negotiation Advisor produced strategy for {contract_id} with {len(positions)} positions.")
        return strategy_obj
