import uuid
from typing import Optional, Union, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.logging import get_logger
from backend.models.findings import DisputeAssessment, DisputeScenario
from backend.models.graph import ContractGraph
from backend.models.cas_message import CASMessage
from backend.events.bus import event_bus
from backend.systems.dispute_intelligence.ambiguity_detector import AmbiguityDetector
from backend.systems.dispute_intelligence.party_a_interpreter import PartyAInterpreter
from backend.systems.dispute_intelligence.party_b_interpreter import PartyBInterpreter
from backend.systems.dispute_intelligence.conflict_simulator import ConflictSimulator
from backend.systems.dispute_intelligence.resolution_strategist import ResolutionStrategist
from backend.systems.dispute_intelligence.critic import DisputeCritic
from backend.database.schema import DisputeAssessmentModel

logger = get_logger("DisputeIntelligenceSystem")


class DisputeIntelligenceSystem:
    """
    SYSTEM 6 — DISPUTE INTELLIGENCE
    Architecture: Multi-Perspective Simulation + Debate Architecture
    Identifies clauses and situations likely to produce legal disputes by modeling opposing
    adversarial interpretations (Party A vs. Party B) and projecting crisis scenarios.
    Can be run completely independently.
    """

    @classmethod
    async def analyze_disputes(
        cls,
        contract: Union[str, ContractGraph],
        contract_id: Optional[str] = None,
        party_a_name: str = "Customer",
        party_b_name: str = "Vendor",
        db_session: Optional[AsyncSession] = None,
    ) -> DisputeAssessment:
        if isinstance(contract, ContractGraph):
            cid = contract.contract_id
            contract_text = "\n\n".join([f"{c.section_number} {c.title}:\n{c.text}" for c in contract.clauses])
            if contract.parties:
                party_a_name = contract.parties[0].name
                party_b_name = contract.parties[1].name if len(contract.parties) > 1 else "Counterparty"
        else:
            cid = contract_id or f"CTR-{uuid.uuid4().hex[:8].upper()}"
            contract_text = contract

        logger.info(f"Initiating Dispute Intelligence analysis for {cid} ({party_a_name} vs. {party_b_name})...")

        # Step 1: Detect Ambiguities & Discretionary Clauses
        ambiguities = await AmbiguityDetector.detect_ambiguities(contract_text)

        # Step 2: Opposing Party Interpretations
        party_a_task = PartyAInterpreter.interpret_clauses(ambiguities, party_a_name)
        party_b_task = PartyBInterpreter.interpret_clauses(ambiguities, party_b_name)

        import asyncio
        party_a_lookup, party_b_lookup = await asyncio.gather(party_a_task, party_b_task)

        # Step 3: Conflict Simulator (Clashes of opposing interpretations)
        clashes = await ConflictSimulator.simulate_conflicts(ambiguities, party_a_lookup, party_b_lookup)

        # Step 4: Resolution Strategist Playbook
        resolution_res = await ResolutionStrategist.develop_playbook(clashes)

        # Step 5: Dispute Critic
        critique = await DisputeCritic.critique_disputes(clashes)

        # Step 6: Assemble DisputeAssessment
        scenarios: List[DisputeScenario] = []
        for idx, c in enumerate(clashes):
            matching_ambiguity = next((a for a in ambiguities if a.clause_reference == c.clause_reference), None)
            clause_text = matching_ambiguity.clause_text if matching_ambiguity else c.clause_reference
            amb_type = matching_ambiguity.ambiguity_type if matching_ambiguity else "VAGUE_STANDARD"

            scenarios.append(DisputeScenario(
                scenario_id=f"DSP-{idx+1:03d}",
                clause_id=c.clause_reference,
                clause_text=clause_text,
                ambiguity_type=amb_type,
                party_a_interpretation=party_a_lookup.get(c.clause_reference, "Customer perspective"),
                party_b_interpretation=party_b_lookup.get(c.clause_reference, "Vendor perspective"),
                simulated_dispute_narrative=c.dispute_narrative,
                likelihood=c.likelihood,
                severity=c.severity,
                resolution_strategy=c.resolution_playbook
            ))

        assessment = DisputeAssessment(
            contract_id=cid,
            scenarios=scenarios,
            overall_dispute_risk=critique.overall_dispute_index,
            critic_evaluation=critique.critique_notes,
            recommended_clarifications=[r.proposed_definitional_fix for r in resolution_res.recommendations]
        )

        # Step 7: Persist in PostgreSQL
        if db_session:
            db_disp = DisputeAssessmentModel(
                contract_id=cid,
                overall_dispute_risk=assessment.overall_dispute_risk,
                assessment_json=assessment.model_dump(mode="json")
            )
            db_session.add(db_disp)
            await db_session.commit()
            logger.info(f"Persisted Dispute Assessment for {cid} in PostgreSQL.")

        # Step 8: Standardized CASMessage publication
        message = CASMessage.create(
            contract_id=cid,
            source_system="dispute_intelligence",
            target_system="director",
            event_type="DISPUTE_SIMULATED",
            payload={
                "contract_id": cid,
                "overall_dispute_risk": assessment.overall_dispute_risk,
                "scenario_count": len(scenarios),
                "top_scenarios": [s.model_dump(mode="json") for s in scenarios[:2]]
            },
            evidence_refs=[s.clause_id for s in scenarios if s.clause_id],
            confidence=0.90,
            priority="HIGH" if assessment.overall_dispute_risk in ("HIGH", "CATASTROPHIC") else "MEDIUM"
        )
        await event_bus.publish(message)

        return assessment


dispute_intelligence_system = DisputeIntelligenceSystem()
