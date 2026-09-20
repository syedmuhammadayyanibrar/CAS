from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.core.logging import get_logger

logger = get_logger("NegotiationPlanner")


class DraftPositionDTO(BaseModel):
    clause_reference: str
    clause_title: str
    desired_outcome: str
    acceptable_outcome: str
    red_line: str  # Absolute deal-breaker threshold
    proposed_counter_clause: str


class PlannerResponse(BaseModel):
    draft_positions: List[DraftPositionDTO] = Field(default_factory=list)
    initial_agenda: List[str] = Field(default_factory=list)


class NegotiationPlanner:
    """
    First agent in the Planner + Simulator + Critic pipeline.
    Establishes target positions, fallback compromises, and red lines based on commercial objectives.
    """

    @staticmethod
    async def plan_initial_positions(contract_text: str, commercial_objective: str) -> PlannerResponse:
        prompt = (
            "You are the Negotiation Planner agent in a Negotiation Intelligence System.\n"
            f"Commercial Objective: {commercial_objective}\n\n"
            "Review the contract and develop target negotiation positions for the most problematic clauses.\n"
            "For each targeted clause, identify:\n"
            "- clause_reference & clause_title\n"
            "- desired_outcome (ideal commercial term)\n"
            "- acceptable_outcome (realistic compromise)\n"
            "- red_line (non-negotiable boundary; deal-breaker threshold)\n"
            "- proposed_counter_clause (exact redline text replacement)\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text[:4000])

        result: PlannerResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=PlannerResponse,
            system_instruction="You are an elite commercial contract negotiation planner."
        )

        logger.info(f"Negotiation Planner established {len(result.draft_positions)} draft positions.")
        return result
