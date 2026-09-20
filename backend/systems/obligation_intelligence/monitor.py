from typing import List, Dict, Any
from datetime import datetime, timezone
from backend.models.findings import ObligationItem
from backend.core.logging import get_logger

logger = get_logger("ObligationMonitoringAgent")


class ObligationMonitoringAgent:
    """
    Autonomous Long-Running Monitor.
    Ticks through active obligations against the current date,
    detecting approaching deadlines, renewal windows, and active breach risks.
    """

    @staticmethod
    def tick_monitoring(
        scheduled_timeline: List[Dict[str, Any]],
        current_date_str: str = "2026-10-15"
    ) -> Dict[str, Any]:
        curr = datetime.fromisoformat(current_date_str)
        upcoming_items = []
        due_soon_items = []
        overdue_items = []

        for item in scheduled_timeline:
            due = datetime.fromisoformat(item["due_date"])
            reminder = datetime.fromisoformat(item["reminder_date"])

            days_remaining = (due - curr).days

            if days_remaining < 0:
                overdue_items.append({**item, "days_overdue": abs(days_remaining)})
            elif curr >= reminder:
                due_soon_items.append({**item, "days_remaining": days_remaining})
            else:
                upcoming_items.append({**item, "days_remaining": days_remaining})

        logger.info(
            f"Obligation Monitor tick at {current_date_str}: {len(due_soon_items)} due soon, "
            f"{len(overdue_items)} overdue, {len(upcoming_items)} upcoming."
        )

        return {
            "current_date": current_date_str,
            "due_soon_count": len(due_soon_items),
            "overdue_count": len(overdue_items),
            "upcoming_count": len(upcoming_items),
            "due_soon": due_soon_items,
            "overdue": overdue_items,
            "upcoming": upcoming_items
        }
