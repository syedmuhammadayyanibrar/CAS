import uuid
from typing import Optional, Union, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.logging import get_logger
from backend.models.findings import NegotiationStrategy
from backend.models.graph import ContractGraph
from backend.models.cas_message import CASMessage
from backend.events.bus import event_bus
from backend.systems.negotiation_intelligence.planner import NegotiationPlanner
from backend.systems.negotiation_intelligence.strategy_agent import StrategyAgent
from backend.systems.negotiation_intelligence.counterparty_simulator import CounterpartySimulator
from backend.systems.negotiation_intelligence.concession_agent import ConcessionAgent
from backend.systems.negotiation_intelligence.game_theorist import GameTheoreticReasoner
from backend.systems.negotiation_intelligence.critic import StrategyCritic
from backend.systems.negotiation_intelligence.advisor import FinalNegotiationAdvisor
from backend.database.schema import NegotiationStrategyModel

logger = get_logger("NegotiationIntelligenceSystem")


class NegotiationIntelligenceSystem:
    """
    SYSTEM 3 — NEGOTIATION INTELLIGENCE
    Architecture: Planner + Simulator + Critic Architecture
    Helps an organization negotiate contract terms through multi-turn simulation,
    game-theoretic reasoning, and counter-proposal generation.
    Can be executed completely independently.
    """

    @classmethod
    async def plan_negotiation(
        cls,
        contract: Union[str, ContractGraph],
        objective: str = "Protect Customer liability, remove asymmetric indemnity, and secure bilateral termination rights.",
        contract_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> NegotiationStrategy:
        if isinstance(contract, ContractGraph):
            cid = contract.contract_id
            contract_text = "\n\n".join([f"{c.section_number} {c.title}:\n{c.text}" for c in contract.clauses])
        else:
            cid = contract_id or f"CTR-{uuid.uuid4().hex[:8].upper()}"
            contract_text = contract

        logger.info(f"Initiating Negotiation Intelligence planning for {cid} with objective: '{objective}'...")

        # Step 1: Planner
        planner_res = await NegotiationPlanner.plan_initial_positions(contract_text, objective)

        # Step 2: Strategy Agent
        strategy_res = await StrategyAgent.develop_strategy(planner_res.draft_positions, objective)

        # Step 3: Counterparty Simulator (Simulates vendor pushback)
        simulation_res = await CounterpartySimulator.simulate_reactions(planner_res.draft_positions)

        # Step 4: Concession Agent
        concessions = await ConcessionAgent.design_concessions(planner_res.draft_positions, simulation_res)

        # Step 5: Game-Theoretic Reasoner
        game_analysis = await GameTheoreticReasoner.analyze_dynamics(planner_res.draft_positions, simulation_res)

        # Step 6: Strategy Critic (Attacks the proposed strategy)
        critique = await StrategyCritic.critique_strategy(planner_res.draft_positions, strategy_res, simulation_res)

        # Step 7: Final Negotiation Advisor
        final_strategy = await FinalNegotiationAdvisor.formulate_final_strategy(
            contract_id=cid,
            commercial_objective=objective,
            draft_positions=planner_res.draft_positions,
            strategy=strategy_res,
            simulation=simulation_res,
            concessions=concessions,
            critique=critique
        )

        # Step 8: Persist in PostgreSQL
        if db_session:
            db_strat = NegotiationStrategyModel(
                contract_id=cid,
                primary_objective=objective,
                strategy_json=final_strategy.model_dump(mode="json")
            )
            db_session.add(db_strat)
            await db_session.commit()
            logger.info(f"Persisted Negotiation Strategy for {cid} in PostgreSQL.")

        # Step 9: Standardized CASMessage publication
        message = CASMessage.create(
            contract_id=cid,
            source_system="negotiation_intelligence",
            target_system="director",
            event_type="NEGOTIATION_PLANNED",
            payload={
                "contract_id": cid,
                "primary_objective": objective,
                "position_count": len(final_strategy.positions),
                "sequence": final_strategy.negotiation_sequence,
                "requires_human_approval": final_strategy.requires_human_approval,
                "positions": [p.model_dump(mode="json") for p in final_strategy.positions]
            },
            evidence_refs=[p.target_clause_id for p in final_strategy.positions if p.target_clause_id],
            confidence=0.91,
            priority="HIGH"
        )
        await event_bus.publish(message)

        return final_strategy


negotiation_intelligence_system = NegotiationIntelligenceSystem()
