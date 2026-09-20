from typing import List, Dict, Any, Optional
from backend.integrations.fastn_client import fastn_client
from backend.core.logging import get_logger

logger = get_logger("IntegrationAdapters")


class SlackAdapter:
    """Slack integration adapter mediated via Fastn."""

    @staticmethod
    async def post_risk_alert(contract_id: str, severity: str, clause: str, consequence: str, evidence: str):
        logger.info(f"[Slack via Fastn] Posting Risk Alert for {contract_id} ({severity})")
        return await fastn_client.execute_risk_escalation(
            contract_id=contract_id,
            severity=severity,
            risky_clause=clause,
            consequence=consequence,
            evidence=evidence,
            channel="#legal-contract-risks",
        )

    @staticmethod
    async def post_approval_request(contract_id: str, reason: str, action: str, conclusions: list):
        logger.info(f"[Slack via Fastn] Posting HITL Approval Request for {contract_id}")
        return await fastn_client.execute_approval_dispatch(
            contract_id=contract_id,
            reason=reason,
            requested_action=action,
            agent_conclusions=conclusions,
        )

    @staticmethod
    async def post_compliance_alert(
        contract_id: str,
        compliance_issue: str,
        severity: str = "HIGH",
        policy_name: str = "Enterprise Policy",
        rule_id: str = "COMP-001",
        evidence: str = "",
        required_action: str = "Legal Amendment",
    ):
        logger.info(f"[Slack via Fastn] Posting Compliance Escalation for {contract_id}")
        return await fastn_client.execute_compliance_escalation(
            contract_id=contract_id,
            compliance_issue=compliance_issue,
            severity=severity,
            policy_name=policy_name,
            rule_id=rule_id,
            evidence=evidence,
            required_action=required_action,
            channel="#legal-compliance-alerts",
        )

    @staticmethod
    async def broadcast_negotiation_update(
        contract_id: str,
        negotiation_state: str,
        current_proposal: str,
        strategy: str,
        concession: Optional[str] = None,
        rationale: str = "",
        next_action: str = "",
    ):
        logger.info(f"[Slack via Fastn] Broadcasting Negotiation Update for {contract_id} ({negotiation_state})")
        return await fastn_client.execute_negotiation_update(
            contract_id=contract_id,
            negotiation_state=negotiation_state,
            current_proposal=current_proposal,
            strategy=strategy,
            concession=concession,
            rationale=rationale,
            next_action=next_action,
            channel="#commercial-negotiations",
        )

    @staticmethod
    async def post_dispute_alert(
        contract_id: str,
        disputed_clause: str,
        party_a_interpretation: str,
        party_b_interpretation: str,
        conflict: str,
        severity: str = "HIGH",
        evidence: str = "",
        recommended_resolution: str = "",
    ):
        logger.info(f"[Slack via Fastn] Posting Dispute Alert for {contract_id} ({severity})")
        return await fastn_client.execute_dispute_escalation(
            contract_id=contract_id,
            disputed_clause=disputed_clause,
            party_a_interpretation=party_a_interpretation,
            party_b_interpretation=party_b_interpretation,
            conflict=conflict,
            severity=severity,
            evidence=evidence,
            recommended_resolution=recommended_resolution,
            channel="#dispute-arbitration-counsel",
        )


class GoogleCalendarAdapter:
    """Google Calendar integration adapter mediated via Fastn."""

    @staticmethod
    async def sync_obligations(contract_id: str, obligations: List[Dict[str, Any]]):
        logger.info(f"[Google Calendar via Fastn] Syncing {len(obligations)} deadlines for {contract_id}")
        return await fastn_client.execute_obligation_sync(
            contract_id=contract_id,
            obligations=obligations,
        )

    @staticmethod
    async def escalate_deadline(
        contract_id: str,
        obligation_title: str,
        deadline: str,
        severity: str = "due",
        responsible_party: str = "Customer",
        recommended_action: str = "",
    ):
        logger.info(f"[Google Calendar via Fastn] Escalating Deadline for {contract_id}: {obligation_title}")
        return await fastn_client.execute_deadline_escalation(
            contract_id=contract_id,
            obligation_title=obligation_title,
            deadline=deadline,
            severity=severity,
            responsible_party=responsible_party,
            recommended_action=recommended_action,
        )


class GmailAdapter:
    """Gmail integration adapter mediated via Fastn."""

    @staticmethod
    async def send_approval_email(contract_id: str, recipient: str, reason: str, action: str, conclusions: list):
        logger.info(f"[Gmail via Fastn] Sending approval notification to {recipient} for {contract_id}")
        return await fastn_client.execute_approval_dispatch(
            contract_id=contract_id,
            reason=reason,
            requested_action=action,
            agent_conclusions=conclusions,
            reviewer_email=recipient,
        )


class AirtableAdapter:
    """Airtable / CRM contract registry adapter mediated via Fastn."""

    @staticmethod
    async def update_registry(contract_id: str, obligations: List[Dict[str, Any]]):
        logger.info(f"[Airtable via Fastn] Updating contract obligation registry for {contract_id}")
        return await fastn_client.execute_obligation_sync(
            contract_id=contract_id,
            obligations=obligations,
        )

    @staticmethod
    async def archive_decision(
        contract_id: str,
        decision: str,
        decision_maker: str,
        reason: str,
        society: str = "director",
        evidence: str = "",
        resulting_action: str = "EXECUTE_SIGNATURE",
    ):
        logger.info(f"[Airtable/Drive via Fastn] Archiving HITL Decision for {contract_id}")
        return await fastn_client.execute_decision_archive(
            contract_id=contract_id,
            decision=decision,
            decision_maker=decision_maker,
            reason=reason,
            society=society,
            evidence=evidence,
            resulting_action=resulting_action,
        )


class GoogleDriveAdapter:
    """Google Drive document archive adapter mediated via Fastn."""

    @staticmethod
    async def archive_decision(
        contract_id: str,
        decision: str,
        decision_maker: str,
        reason: str,
        society: str = "director",
        evidence: str = "",
        resulting_action: str = "EXECUTE_SIGNATURE",
    ):
        return await AirtableAdapter.archive_decision(
            contract_id=contract_id,
            decision=decision,
            decision_maker=decision_maker,
            reason=reason,
            society=society,
            evidence=evidence,
            resulting_action=resulting_action,
        )
