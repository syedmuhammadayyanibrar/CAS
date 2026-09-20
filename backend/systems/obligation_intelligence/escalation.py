from typing import List, Dict, Any
from backend.core.logging import get_logger

logger = get_logger("ObligationEscalationAgent")


class ObligationEscalationAgent:
    """
    Evaluates breach risk severity for upcoming or overdue obligations
    and formats escalation notices.
    """

    @staticmethod
    def evaluate_escalations(monitor_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        escalations = []

        # Process overdue obligations
        for item in monitor_results.get("overdue", []):
            escalations.append({
                "obligation_id": item["obligation_id"],
                "title": item["title"],
                "party": item["party"],
                "level": "CRITICAL",
                "message": f"BREACH RISK: '{item['title']}' for {item['party']} is {item['days_overdue']} day(s) overdue!",
                "suggested_action": "Issue formal cure notice or make emergency payment."
            })

        # Process due soon obligations
        for item in monitor_results.get("due_soon", []):
            level = "WARNING" if item["days_remaining"] <= 3 else "REMINDER"
            escalations.append({
                "obligation_id": item["obligation_id"],
                "title": item["title"],
                "party": item["party"],
                "level": level,
                "message": f"UPCOMING MILESTONE: '{item['title']}' is due in {item['days_remaining']} day(s) (Due: {item['due_date']}).",
                "suggested_action": "Confirm milestone completion or notify account manager."
            })

        logger.info(f"Escalation Agent generated {len(escalations)} escalation item(s).")
        return escalations
