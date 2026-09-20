from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.dispute_intelligence.conflict_simulator import SimulatedClashDTO
from backend.core.logging import get_logger

logger = get_logger("ResolutionStrategist")


class RecommendedClarificationDTO(BaseModel):
    clause_reference: str
    proposed_definitional_fix: str
    dispute_prevention_impact: str


class ResolutionStrategistResponse(BaseModel):
    recommendations: List[RecommendedClarificationDTO] = Field(default_factory=list)
    mitigation_playbook_summary: str = ""


class ResolutionStrategist:
    """
    Formulates proactive contractual clarifications and dispute-prevention drafting remedies.
    """

    @staticmethod
    async def develop_playbook(clashes: List[SimulatedClashDTO]) -> ResolutionStrategistResponse:
        clashes_str = "\n".join([
            f"- Ref: {c.clause_reference} | Trigger: {c.crisis_trigger} | Severity: {c.severity}"
            for c in clashes
        ])

        prompt = (
            "You are the Resolution Strategist in a Dispute Intelligence System.\n"
            "Review the simulated conflict scenarios below and propose precise drafting amendments "
            "and objective standards that would eliminate the ambiguity and prevent the dispute before execution.\n\n"
            f"CLASH SCENARIOS:\n{clashes_str}\n"
        )

        result: ResolutionStrategistResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=ResolutionStrategistResponse,
            system_instruction="You are an expert dispute resolution and preventive legal drafting strategist."
        )

        logger.info(f"Resolution Strategist formulated {len(result.recommendations)} preventative drafting remedies.")
        return result
