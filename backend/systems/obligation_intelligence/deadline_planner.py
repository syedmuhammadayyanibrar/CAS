from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
from backend.models.findings import ObligationItem
from backend.core.logging import get_logger

logger = get_logger("DeadlinePlanner")


class DeadlinePlanner:
    """
    Projects concrete timeline events and sets early notification dates.
    Calculates milestone target dates based on Effective Date.
    """

    @staticmethod
    def project_deadlines(
        items: List[ObligationItem],
        effective_date_str: str = "2026-10-01"
    ) -> List[Dict[str, Any]]:
        try:
            base_date = datetime.fromisoformat(effective_date_str)
        except Exception:
            base_date = datetime(2026, 10, 1, tzinfo=timezone.utc)

        scheduled_timeline = []
        for item in items:
            # Deterministic calculation of standard intervals based on obligation type
            if item.type == "PAYMENT":
                due = base_date + timedelta(days=30)  # Net 30
            elif item.type == "RENEWAL":
                due = base_date + timedelta(days=365)  # 1-year mark
            elif item.type == "SLA":
                due = base_date + timedelta(days=90)   # Quarterly SLA review
            else:
                due = base_date + timedelta(days=60)

            notice_days = item.notice_days or 14
            reminder_date = due - timedelta(days=notice_days)

            scheduled_timeline.append({
                "obligation_id": item.obligation_id,
                "title": item.title,
                "party": item.party,
                "type": item.type,
                "due_date": due.strftime("%Y-%m-%d"),
                "reminder_date": reminder_date.strftime("%Y-%m-%d"),
                "notice_days": notice_days,
                "description": item.description
            })

        logger.info(f"Deadline Planner scheduled {len(scheduled_timeline)} operational milestones.")
        return scheduled_timeline
