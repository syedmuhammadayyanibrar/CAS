from typing import List, Dict, Any
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.models.findings import ObligationItem
from backend.core.logging import get_logger

logger = get_logger("DependencyAnalyzer")


class ObligationDependencyDTO(BaseModel):
    dependent_obligation_id: str
    prerequisite_event_or_obligation: str
    trigger_condition: str


class DependencyAnalysisResponse(BaseModel):
    dependencies: List[ObligationDependencyDTO] = Field(default_factory=list)


class DependencyAnalyzer:
    """
    Analyzes causal dependencies and preconditions between obligations
    (e.g., SLA outage must occur -> claim must be submitted within 10 days).
    """

    @staticmethod
    async def analyze_dependencies(items: List[ObligationItem]) -> List[ObligationDependencyDTO]:
        items_summary = "\n".join([f"- [{i.obligation_id}] {i.party}: {i.title} ({i.type})" for i in items])
        prompt = (
            "You are the Dependency Analyzer in an Obligation Intelligence System.\n"
            "Identify the prerequisite triggers, dependencies, and conditions between these obligations:\n"
            f"{items_summary}\n"
        )

        result: DependencyAnalysisResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=DependencyAnalysisResponse,
            system_instruction="You are a legal and operational workflow dependency analyst."
        )

        logger.info(f"Dependency Analyzer mapped {len(result.dependencies)} obligation dependencies.")
        return result.dependencies
