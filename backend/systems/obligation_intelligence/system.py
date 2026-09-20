import uuid
from typing import Optional, Union, Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.logging import get_logger
from backend.models.findings import ObligationSchedule
from backend.models.graph import ContractGraph
from backend.models.cas_message import CASMessage
from backend.events.bus import event_bus
from backend.systems.obligation_intelligence.extractor import ObligationItemExtractor
from backend.systems.obligation_intelligence.dependency_analyzer import DependencyAnalyzer
from backend.systems.obligation_intelligence.deadline_planner import DeadlinePlanner
from backend.systems.obligation_intelligence.monitor import ObligationMonitoringAgent
from backend.systems.obligation_intelligence.escalation import ObligationEscalationAgent
from backend.systems.obligation_intelligence.reporter import ObligationReporter
from backend.integrations.adapters import GoogleCalendarAdapter
from backend.database.schema import ObligationScheduleModel

logger = get_logger("ObligationIntelligenceSystem")


class ObligationIntelligenceSystem:
    """
    SYSTEM 5 — OBLIGATION INTELLIGENCE
    Architecture: Event-Driven Monitoring Architecture
    Manages long-running post-signature obligations, payment schedules,
    renewal windows, and SLA deliverables.
    Can be run completely independently.
    """

    @classmethod
    async def register_obligations(
        cls,
        contract: Union[str, ContractGraph],
        contract_id: Optional[str] = None,
        effective_date: str = "2026-10-01",
        db_session: Optional[AsyncSession] = None,
    ) -> ObligationSchedule:
        if isinstance(contract, ContractGraph):
            cid = contract.contract_id
            contract_text = "\n\n".join([f"{c.section_number} {c.title}:\n{c.text}" for c in contract.clauses])
            effective_date = contract.effective_date or effective_date
        else:
            cid = contract_id or f"CTR-{uuid.uuid4().hex[:8].upper()}"
            contract_text = contract

        logger.info(f"Registering obligations for signed contract {cid} (Effective: {effective_date})...")

        # Step 1: Extract all post-signature items
        items = await ObligationItemExtractor.extract_all_obligations(contract_text)

        # Step 2: Analyze dependencies
        dependencies = await DependencyAnalyzer.analyze_dependencies(items)

        # Step 3: Project timeline deadlines
        scheduled_timeline = DeadlinePlanner.project_deadlines(items, effective_date)

        # Step 4: Run initial monitoring tick
        monitor_tick = ObligationMonitoringAgent.tick_monitoring(scheduled_timeline, effective_date)

        # Step 5: Evaluate escalations
        escalations = ObligationEscalationAgent.evaluate_escalations(monitor_tick)

        # Step 6: Compile schedule
        schedule = ObligationReporter.build_schedule(cid, items, scheduled_timeline, escalations)

        # Step 7: Persist in PostgreSQL
        if db_session:
            existing_sched = (await db_session.execute(
                select(ObligationScheduleModel).where(ObligationScheduleModel.contract_id == cid)
            )).scalar_one_or_none()

            if existing_sched:
                existing_sched.total_obligations = len(items)
                existing_sched.schedule_json = schedule.model_dump(mode="json")
            else:
                db_sched = ObligationScheduleModel(
                    contract_id=cid,
                    total_obligations=len(items),
                    schedule_json=schedule.model_dump(mode="json")
                )
                db_session.add(db_sched)

            await db_session.commit()
            logger.info(f"Persisted Obligation Schedule for {cid} in PostgreSQL.")

        # Step 8: Standardized CASMessage publication
        message = CASMessage.create(
            contract_id=cid,
            source_system="obligation_intelligence",
            target_system="director",
            event_type="CONTRACT_SIGNED",
            payload={
                "contract_id": cid,
                "total_obligations": len(items),
                "scheduled_count": len(scheduled_timeline),
                "active_breaches": schedule.active_breach_risks
            },
            evidence_refs=[i.obligation_id for i in items[:5]],
            confidence=0.95,
            priority="MEDIUM"
        )
        await event_bus.publish(message)

        # Step 9: Trigger live Fastn Obligation Sync Workflow to Google Calendar & Airtable
        fastn_payload = ObligationReporter.format_fastn_sync_payload(cid, scheduled_timeline)
        await GoogleCalendarAdapter.sync_obligations(cid, fastn_payload)

        return schedule

    @classmethod
    async def tick_monitoring(
        cls,
        contract_id: str,
        current_date_str: str,
        scheduled_timeline: List[Dict[str, Any]],
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Ticking time forward to monitor active obligations and trigger warnings."""
        logger.info(f"Running obligation tick for {contract_id} at simulated date {current_date_str}")
        tick_res = ObligationMonitoringAgent.tick_monitoring(scheduled_timeline, current_date_str)
        escalations = ObligationEscalationAgent.evaluate_escalations(tick_res)

        if escalations:
            msg = CASMessage.create(
                contract_id=contract_id,
                source_system="obligation_intelligence",
                target_system="director",
                event_type="OBLIGATION_TICK",
                payload={"tick_date": current_date_str, "escalations": escalations},
                priority="HIGH" if any(e["level"] == "CRITICAL" for e in escalations) else "MEDIUM"
            )
            await event_bus.publish(msg)

        return {"tick": tick_res, "escalations": escalations}


obligation_intelligence_system = ObligationIntelligenceSystem()
