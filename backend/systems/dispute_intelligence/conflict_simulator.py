from typing import List, Dict
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.dispute_intelligence.ambiguity_detector import AmbiguousClauseDTO
from backend.core.logging import get_logger

logger = get_logger("ConflictSimulator")


class SimulatedClashDTO(BaseModel):
    clause_reference: str
    crisis_trigger: str  # e.g., Black Friday outage, abrupt contract termination, data leak
    dispute_narrative: str
    likelihood: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    severity: str = "HIGH"      # LOW, MEDIUM, HIGH, CATASTROPHIC
    resolution_playbook: str


class ConflictSimulationResponse(BaseModel):
    clashes: List[SimulatedClashDTO] = Field(default_factory=list)


class ConflictSimulator:
    """
    CRITICAL AGENT in Dispute Intelligence.
    Constructs realistic, high-stakes operational crises where the opposing
    interpretations of Party A and Party B collide into open conflict or litigation.
    """

    @staticmethod
    async def simulate_conflicts(
        ambiguities: List[AmbiguousClauseDTO],
        party_a_lookup: Dict[str, str],
        party_b_lookup: Dict[str, str]
    ) -> List[SimulatedClashDTO]:
        clash_cases = []
        for a in ambiguities:
            p_a = party_a_lookup.get(a.clause_reference, "Customer standard view")
            p_b = party_b_lookup.get(a.clause_reference, "Vendor standard view")
            clash_cases.append(
                f"CLAUSE: {a.clause_reference}\n"
                f"  Text: {a.clause_text}\n"
                f"  Customer Interpretation (Party A): {p_a}\n"
                f"  Vendor Interpretation (Party B): {p_b}\n"
            )

        prompt = (
            "You are the Conflict Simulator in a Dispute Intelligence System.\n"
            "Given the polarized interpretations of Party A (Customer) and Party B (Vendor), construct realistic "
            "business crisis scenarios where these opposing views produce a formal dispute or lawsuit.\n"
            "For each scenario:\n"
            "1. Define the crisis trigger (e.g., peak-season service downtime, sudden termination, customer data used in competitor model).\n"
            "2. Describe the dispute narrative (how each party reacts, claims made, legal threats).\n"
            "3. Assess likelihood (LOW, MEDIUM, HIGH) and severity (LOW, MEDIUM, HIGH, CATASTROPHIC).\n"
            "4. Outline an immediate resolution playbook to defuse the conflict.\n\n"
            f"DISPUTE SEEDS:\n" + "\n".join(clash_cases)
        )

        result: ConflictSimulationResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=ConflictSimulationResponse,
            system_instruction="You are a senior litigation partner and commercial conflict simulator."
        )

        logger.info(f"Conflict Simulator generated {len(result.clashes)} dispute scenarios.")
        return result.clashes
