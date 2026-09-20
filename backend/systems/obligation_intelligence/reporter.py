from typing import List, Dict, Any
from backend.models.findings import ObligationItem, ObligationSchedule
from backend.core.logging import get_logger

logger = get_logger("ObligationReporter")


class ObligationReporter:
    """
    Compiles the active ObligationSchedule and formats Fastn Google Calendar/Airtable sync payloads.
    """

    @staticmethod
    def build_schedule(
        contract_id: str,
        items: List[ObligationItem],
        scheduled_timeline: List[Dict[str, Any]],
        escalations: List[Dict[str, Any]]
    ) -> ObligationSchedule:
        breach_risks = [e["message"] for e in escalations if e.get("level") in ("WARNING", "CRITICAL")]

        schedule = ObligationSchedule(
            contract_id=contract_id,
            total_obligations=len(items),
            items=items,
            monitoring_interval="DAILY",
            active_breach_risks=breach_risks
        )

        logger.info(f"Obligation Reporter compiled schedule for {contract_id}: {len(items)} items, {len(breach_risks)} breach risks.")
        return schedule

    @staticmethod
    def format_fastn_sync_payload(contract_id: str, scheduled_timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formats obligations for the live Fastn cas-obligation-sync workflow."""
        return [
            {
                "title": item["title"],
                "party": item["party"],
                "dueDate": item["due_date"],
                "type": item["type"],
                "noticeDays": item["notice_days"],
                "description": item["description"]
            }
            for item in scheduled_timeline
        ]
