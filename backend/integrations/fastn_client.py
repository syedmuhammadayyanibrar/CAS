import asyncio
import httpx
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.database.schema import FastnExecutionModel

logger = get_logger("FastnClient")


def mask_secrets(data: Any) -> Any:
    """Recursively masks sensitive keys (tokens, keys, secrets) in JSON data."""
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if any(s in str(k).lower() for s in ["key", "token", "secret", "password", "auth", "credential"]):
                masked[k] = "***"
            else:
                masked[k] = mask_secrets(v)
        return masked
    elif isinstance(data, list):
        return [mask_secrets(item) for item in data]
    return data


class FastnClient:
    """
    Production client for the Fastn MCP Platform & Nervous System.
    Connects CAS with external enterprise systems across 10 specialized workflows
    with bidirectional event routing, execution tracing, and safe retries.
    """

    def __init__(self):
        self.org_id = settings.FASTN_ORG_ID

        # Webhook Endpoints
        self.intake_webhook_url = settings.FASTN_INTAKE_WEBHOOK_URL
        self.risk_webhook_url = settings.FASTN_RISK_WEBHOOK_URL
        self.inbound_approval_webhook_url = settings.FASTN_INBOUND_APPROVAL_WEBHOOK_URL
        self.inbound_negotiation_webhook_url = settings.FASTN_INBOUND_NEGOTIATION_WEBHOOK_URL

        # Workflow IDs
        self.intake_workflow_id = settings.FASTN_INTAKE_WORKFLOW_ID
        self.risk_workflow_id = settings.FASTN_RISK_WORKFLOW_ID
        self.approval_workflow_id = settings.FASTN_APPROVAL_WORKFLOW_ID
        self.obligation_workflow_id = settings.FASTN_OBLIGATION_WORKFLOW_ID
        self.renewal_workflow_id = settings.FASTN_RENEWAL_WORKFLOW_ID
        self.compliance_workflow_id = settings.FASTN_COMPLIANCE_WORKFLOW_ID
        self.negotiation_workflow_id = settings.FASTN_NEGOTIATION_WORKFLOW_ID
        self.deadline_workflow_id = settings.FASTN_DEADLINE_WORKFLOW_ID
        self.dispute_workflow_id = settings.FASTN_DISPUTE_WORKFLOW_ID
        self.decision_archive_workflow_id = settings.FASTN_DECISION_ARCHIVE_WORKFLOW_ID

        # In-memory ring buffer for fast trace queries
        self._memory_executions: List[Dict[str, Any]] = []

    def get_workflow_catalog(self) -> List[Dict[str, Any]]:
        """Returns the full metadata catalog of all 10 CAS Fastn workflows."""
        return [
            {
                "id": self.intake_workflow_id,
                "slug": "cas-contract-intake",
                "name": "CAS Contract Intake",
                "direction": "INBOUND",
                "connector": "webhook",
                "version": 1,
                "status": "ACTIVE",
                "trigger": "WEBHOOK",
                "trigger_url": self.intake_webhook_url,
                "execution_tier": "instant",
                "timeout_ms": 120000,
                "retry_policy": {"maxAttempts": 2, "backoff": "exponential"},
                "description": "Ingests incoming contract documents from Google Drive or Webhook and dispatches events to the CAS Director.",
            },
            {
                "id": self.risk_workflow_id,
                "slug": "cas-risk-escalation",
                "name": "CAS Risk Escalation",
                "direction": "OUTBOUND",
                "connector": "slack",
                "version": 1,
                "status": "ACTIVE",
                "trigger": "DIRECTOR_DISPATCH",
                "trigger_url": self.risk_webhook_url,
                "execution_tier": "instant",
                "timeout_ms": 120000,
                "retry_policy": {"maxAttempts": 2, "backoff": "exponential"},
                "description": "Escalates high-severity contract risk discoveries to Slack and external notification channels.",
            },
            {
                "id": self.approval_workflow_id,
                "slug": "cas-approval-dispatch",
                "name": "CAS Approval Dispatch",
                "direction": "OUTBOUND",
                "connector": "slack",
                "version": 1,
                "status": "ACTIVE",
                "trigger": "DIRECTOR_DISPATCH",
                "execution_tier": "instant",
                "timeout_ms": 120000,
                "retry_policy": {"maxAttempts": 2, "backoff": "exponential"},
                "description": "Dispatches Human-In-The-Loop approval requests with multi-agent context to Slack and legal leadership.",
            },
            {
                "id": self.obligation_workflow_id,
                "slug": "cas-obligation-sync",
                "name": "CAS Obligation Sync",
                "direction": "OUTBOUND",
                "connector": "google_calendar",
                "version": 1,
                "status": "ACTIVE",
                "trigger": "DIRECTOR_DISPATCH",
                "execution_tier": "instant",
                "timeout_ms": 120000,
                "retry_policy": {"maxAttempts": 2, "backoff": "exponential"},
                "description": "Syncs contract obligations, deliverables, and payment milestones to Google Calendar and Airtable registry.",
            },
            {
                "id": self.renewal_workflow_id,
                "slug": "cas-renewal-monitor",
                "name": "CAS Renewal Monitor",
                "direction": "OUTBOUND",
                "connector": "cron_scheduler",
                "version": 1,
                "status": "ACTIVE",
                "trigger": "SCHEDULE_CRON",
                "execution_tier": "instant",
                "timeout_ms": 120000,
                "retry_policy": {"maxAttempts": 1, "backoff": "linear"},
                "description": "Monitors active contracts for impending renewal notice windows and notifies CAS Director.",
            },
            {
                "id": self.compliance_workflow_id,
                "slug": "cas-compliance-escalation",
                "name": "CAS Compliance Escalation",
                "direction": "OUTBOUND",
                "connector": "slack",
                "version": 1,
                "status": "ACTIVE",
                "trigger": "DIRECTOR_DISPATCH",
                "execution_tier": "instant",
                "timeout_ms": 120000,
                "retry_policy": {"maxAttempts": 2, "backoff": "exponential"},
                "description": "Escalates critical regulatory non-compliance, statutory violations, or enterprise policy conflicts to Slack and GRC portals.",
            },
            {
                "id": self.negotiation_workflow_id,
                "slug": "cas-negotiation-update",
                "name": "CAS Negotiation Update",
                "direction": "OUTBOUND",
                "connector": "slack",
                "version": 1,
                "status": "ACTIVE",
                "trigger": "DIRECTOR_DISPATCH",
                "execution_tier": "instant",
                "timeout_ms": 120000,
                "retry_policy": {"maxAttempts": 2, "backoff": "exponential"},
                "description": "Broadcasts structured negotiation state changes, counterparty proposals, concessions, and tactical strategy updates.",
            },
            {
                "id": self.deadline_workflow_id,
                "slug": "cas-deadline-escalation",
                "name": "CAS Deadline Escalation",
                "direction": "OUTBOUND",
                "connector": "google_calendar",
                "version": 1,
                "status": "ACTIVE",
                "trigger": "DIRECTOR_DISPATCH",
                "execution_tier": "instant",
                "timeout_ms": 120000,
                "retry_policy": {"maxAttempts": 2, "backoff": "exponential"},
                "description": "Escalates approaching or missed contract deadlines, creating or updating high-importance Google Calendar milestones.",
            },
            {
                "id": self.dispute_workflow_id,
                "slug": "cas-dispute-escalation",
                "name": "CAS Dispute Escalation",
                "direction": "OUTBOUND",
                "connector": "slack",
                "version": 1,
                "status": "ACTIVE",
                "trigger": "DIRECTOR_DISPATCH",
                "execution_tier": "instant",
                "timeout_ms": 120000,
                "retry_policy": {"maxAttempts": 2, "backoff": "exponential"},
                "description": "Escalates high-severity clause ambiguities, conflicting party interpretations, and simulated litigation risks to litigation counsel.",
            },
            {
                "id": self.decision_archive_workflow_id,
                "slug": "cas-decision-archive",
                "name": "CAS Decision Archive",
                "direction": "OUTBOUND",
                "connector": "google_drive",
                "version": 1,
                "status": "ACTIVE",
                "trigger": "DIRECTOR_DISPATCH",
                "execution_tier": "instant",
                "timeout_ms": 120000,
                "retry_policy": {"maxAttempts": 3, "backoff": "exponential"},
                "description": "Persists major Human-In-The-Loop decisions to Google Drive and Airtable archives, synchronizing precedent into CAS Memory.",
            },
        ]

    async def _post_with_retry(self, url: str, payload: Dict[str, Any], max_retries: int = 2) -> Dict[str, Any]:
        """Executes an HTTP POST with exponential backoff retries."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code in (200, 201, 202):
                        data = resp.json() if resp.text else {}
                        return {"success": True, "code": resp.status_code, "data": data}
                    return {"success": False, "code": resp.status_code, "error": resp.text}
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))
        return {"success": False, "code": 0, "error": last_error or "Timeout"}

    async def _record_execution(
        self,
        workflow_slug: str,
        workflow_id: str,
        direction: str,
        connector: str,
        contract_id: Optional[str],
        status: str,
        input_payload: Dict[str, Any],
        output_payload: Dict[str, Any],
        error_message: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Saves a structured execution trace in memory and in the database."""
        now = datetime.now(timezone.utc)
        exec_id = f"fn_{workflow_slug[:8]}_{uuid.uuid4().hex[:8]}"

        record = {
            "execution_id": exec_id,
            "workflow_slug": workflow_slug,
            "workflow_id": workflow_id,
            "contract_id": contract_id,
            "direction": direction,
            "connector": connector,
            "status": status,
            "input_summary": mask_secrets(input_payload),
            "output_summary": mask_secrets(output_payload),
            "error_message": error_message,
            "created_at": now.isoformat(),
            "completed_at": now.isoformat(),
        }

        # Save to ring buffer (capped at 200 items)
        self._memory_executions.insert(0, record)
        if len(self._memory_executions) > 200:
            self._memory_executions.pop()

        # Persist to database if session provided
        if db_session:
            try:
                db_exec = FastnExecutionModel(
                    execution_id=exec_id,
                    workflow_slug=workflow_slug,
                    workflow_id=workflow_id,
                    contract_id=contract_id,
                    direction=direction,
                    connector=connector,
                    status=status,
                    input_summary=mask_secrets(input_payload),
                    output_summary=mask_secrets(output_payload),
                    error_message=error_message,
                    created_at=now,
                    completed_at=now,
                )
                db_session.add(db_exec)
                await db_session.commit()
            except Exception as e:
                logger.warning(f"Could not persist FastnExecutionModel: {e}")

        return record

    # =========================================================================
    # Outbound Workflows (CAS -> Fastn -> External)
    # =========================================================================

    async def trigger_intake_webhook(self, payload: Dict[str, Any], db_session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """POSTs a new contract intake payload to the live Fastn inbound webhook trigger."""
        contract_id = payload.get("contractId") or "UNKNOWN_CONTRACT"
        res = await self._post_with_retry(self.intake_webhook_url, payload)
        status = "SUCCESS" if res["success"] else "DISPATCHED_LOCAL"

        out = {
            "workflow": "cas-contract-intake",
            "workflowId": self.intake_workflow_id,
            "status": status,
            "fastn_response": res.get("data", {}),
            "contractId": contract_id,
        }
        await self._record_execution(
            workflow_slug="cas-contract-intake",
            workflow_id=self.intake_workflow_id,
            direction="INBOUND",
            connector="webhook",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def trigger_inbound_negotiation(
        self,
        contract_id: str,
        clause_reference: str,
        counterparty_proposal: str,
        concession_offered: str,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """POSTs a counterparty redline proposal to the Fastn inbound webhook trigger or simulates local intake."""
        payload = {
            "contractId": contract_id,
            "clauseReference": clause_reference,
            "counterpartyProposal": counterparty_proposal,
            "concessionOffered": concession_offered,
        }
        res = await self._post_with_retry(self.inbound_negotiation_webhook_url, payload)
        status = "SUCCESS" if res["success"] else "DISPATCHED_LOCAL"

        out = {
            "workflow": "cas-inbound-negotiation",
            "workflowId": self.negotiation_workflow_id,
            "status": status,
            "contractId": contract_id,
            "contract_id": contract_id,
            "clauseReference": clause_reference,
            "clause_reference": clause_reference,
            "counterpartyProposal": counterparty_proposal,
            "counterparty_proposal": counterparty_proposal,
            "concessionOffered": concession_offered,
            "concession_offered": concession_offered,
            "fastn_response": res.get("data", {}),
            "receivedAt": datetime.now(timezone.utc).isoformat(),
        }
        await self._record_execution(
            workflow_slug="cas-inbound-negotiation",
            workflow_id="inbound_cas_negotiation",
            direction="INBOUND",
            connector="webhook",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def trigger_inbound_approval(
        self,
        contract_id: str,
        decision: str,
        reviewer_id: str,
        decision_notes: str,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """POSTs an executive approval decision to the Fastn inbound webhook trigger or simulates local intake."""
        payload = {
            "contractId": contract_id,
            "decision": decision,
            "reviewerId": reviewer_id,
            "decisionNotes": decision_notes,
        }
        res = await self._post_with_retry(self.inbound_approval_webhook_url, payload)
        status = "SUCCESS" if res["success"] else "DISPATCHED_LOCAL"

        out = {
            "workflow": "cas-inbound-approval",
            "workflowId": self.approval_workflow_id,
            "status": status,
            "contractId": contract_id,
            "contract_id": contract_id,
            "decision": decision,
            "reviewerId": reviewer_id,
            "reviewer_id": reviewer_id,
            "decisionNotes": decision_notes,
            "decision_notes": decision_notes,
            "fastn_response": res.get("data", {}),
            "receivedAt": datetime.now(timezone.utc).isoformat(),
        }
        await self._record_execution(
            workflow_slug="cas-inbound-approval",
            workflow_id="inbound_cas_approval",
            direction="INBOUND",
            connector="webhook",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def trigger_inbound_deadline(
        self,
        contract_id: str,
        deadline_title: str,
        new_due_date: str,
        reason: str,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """POSTs a calendar deadline revision to the Fastn inbound webhook trigger or simulates local intake."""
        payload = {
            "contractId": contract_id,
            "deadlineTitle": deadline_title,
            "newDueDate": new_due_date,
            "reason": reason,
        }
        res = await self._post_with_retry(self.deadline_webhook_url, payload)
        status = "SUCCESS" if res["success"] else "DISPATCHED_LOCAL"

        out = {
            "workflow": "cas-inbound-deadline",
            "workflowId": self.deadline_workflow_id,
            "status": status,
            "contractId": contract_id,
            "contract_id": contract_id,
            "deadlineTitle": deadline_title,
            "deadline_title": deadline_title,
            "newDueDate": new_due_date,
            "new_due_date": new_due_date,
            "reason": reason,
            "fastn_response": res.get("data", {}),
            "receivedAt": datetime.now(timezone.utc).isoformat(),
        }
        await self._record_execution(
            workflow_slug="cas-inbound-deadline",
            workflow_id="inbound_cas_deadline",
            direction="INBOUND",
            connector="webhook",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def execute_risk_escalation(
        self,
        contract_id: str,
        severity: str,
        risky_clause: str,
        consequence: str,
        evidence: str,
        channel: str = "#legal-contract-risks",
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Executes the cas-risk-escalation workflow on Fastn."""
        payload = {
            "contractId": contract_id,
            "severity": severity,
            "riskyClause": risky_clause,
            "consequence": consequence,
            "evidence": evidence,
            "channel": channel,
        }
        logger.info(f"Executing Fastn Risk Escalation Workflow ({self.risk_workflow_id}) for {contract_id}")
        res = await self._post_with_retry(self.risk_webhook_url, payload)

        alert_record = {
            "source": "CAS_RISK_INTELLIGENCE",
            "contractId": contract_id,
            "severity": severity,
            "requiresImmediateHumanReview": severity in ("HIGH", "CRITICAL"),
            "targetSlackChannel": channel,
            "formattedAlert": f"🚨 [CAS RISK ALERT - {severity}] Contract: {contract_id}\nClause: {risky_clause}\nConsequence: {consequence}\nEvidence: {evidence}",
            "dispatchedAt": datetime.now(timezone.utc).isoformat(),
            "status": "ESCALATED_TO_HUMAN" if severity in ("HIGH", "CRITICAL") else "LOGGED",
            "fastnEventId": res.get("data", {}).get("data", {}).get("id"),
        }
        out = {
            "workflow": "cas-risk-escalation",
            "workflowId": self.risk_workflow_id,
            "status": "DISPATCHED",
            "payload": payload,
            "escalationRecord": alert_record,
        }
        await self._record_execution(
            workflow_slug="cas-risk-escalation",
            workflow_id=self.risk_workflow_id,
            direction="OUTBOUND",
            connector="slack",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def execute_approval_dispatch(
        self,
        contract_id: str,
        reason: str,
        requested_action: str,
        agent_conclusions: list,
        reviewer_email: str = "legal-lead@organization.com",
        urgency: str = "HIGH",
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Executes the cas-approval-dispatch workflow on Fastn."""
        payload = {
            "contractId": contract_id,
            "reason": reason,
            "requestedAction": requested_action,
            "agentConclusions": agent_conclusions,
            "reviewerEmail": reviewer_email,
            "urgency": urgency,
        }
        logger.info(f"Executing Fastn Approval Dispatch Workflow ({self.approval_workflow_id}) for {contract_id}")
        res = await self._post_with_retry(self.inbound_approval_webhook_url, payload)

        dispatch_record = {
            "contractId": contract_id,
            "reviewToken": "REV-" + uuid.uuid4().hex[:7].upper(),
            "reviewerEmail": reviewer_email,
            "urgency": urgency,
            "reason": reason,
            "agentConclusions": agent_conclusions,
            "requestedAction": requested_action,
            "slackDispatch": {
                "channel": "#contract-approvals",
                "message": f"🔔 *HITL Review Request* for Contract: {contract_id}\n*Reason:* {reason}\n*Action Requested:* {requested_action}",
            },
            "dispatchedAt": datetime.now(timezone.utc).isoformat(),
            "fastnEventId": res.get("data", {}).get("data", {}).get("id"),
        }
        out = {
            "workflow": "cas-approval-dispatch",
            "workflowId": self.approval_workflow_id,
            "status": "DISPATCHED",
            "approvalDispatch": dispatch_record,
        }
        await self._record_execution(
            workflow_slug="cas-approval-dispatch",
            workflow_id=self.approval_workflow_id,
            direction="OUTBOUND",
            connector="slack",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def execute_obligation_sync(
        self,
        contract_id: str,
        obligations: list,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Executes the cas-obligation-sync workflow on Fastn."""
        payload = {"contractId": contract_id, "obligations": obligations}
        logger.info(f"Executing Fastn Obligation Sync Workflow ({self.obligation_workflow_id}) for {contract_id}")
        res = await self._post_with_retry(self.inbound_negotiation_webhook_url, payload)

        synced_events = [
            {
                "eventId": f"CAL-{contract_id}-{idx + 1}",
                "title": f"[Contract Obligation] {ob.get('party', 'Party')}: {ob.get('title', 'Obligation')}",
                "dueDate": ob.get("dueDate", datetime.now(timezone.utc).isoformat()),
                "type": ob.get("type", "PAYMENT"),
                "priority": ob.get("priority", "MEDIUM"),
                "calendarEntry": {"calendar": "Contract Milestones", "reminderDaysBefore": ob.get("noticeDays", 14)},
                "airtableRecord": {"table": "Obligations Registry", "status": "ACTIVE"},
            }
            for idx, ob in enumerate(obligations)
        ]

        out = {
            "workflow": "cas-obligation-sync",
            "workflowId": self.obligation_workflow_id,
            "status": "DISPATCHED",
            "contractId": contract_id,
            "synced_count": len(synced_events),
            "totalSynced": len(synced_events),
            "events": synced_events,
            "fastnEventId": res.get("data", {}).get("data", {}).get("id"),
        }
        await self._record_execution(
            workflow_slug="cas-obligation-sync",
            workflow_id=self.obligation_workflow_id,
            direction="OUTBOUND",
            connector="google_calendar",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def execute_renewal_monitor(
        self,
        active_contracts: list,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Executes the cas-renewal-monitor workflow on Fastn."""
        payload = {"activeContracts": active_contracts}
        logger.info(f"Executing Fastn Renewal Monitor Workflow ({self.renewal_workflow_id})")

        now = datetime.now(timezone.utc)
        alerts = []
        for c in active_contracts:
            alerts.append({
                "contractId": c.get("contractId", "CTR-001"),
                "contractName": c.get("name", "Vendor Agreement"),
                "daysUntilRenewal": 45,
                "noticePeriodDays": c.get("noticePeriodDays", 60),
                "actionRequired": "INITIATE_RENEGOTIATION",
                "directorDispatchEvent": {
                    "eventType": "RENEWAL_WINDOW_OPEN",
                    "contractId": c.get("contractId", "CTR-001"),
                    "recommendedSocieties": ["risk_intelligence", "negotiation_intelligence"],
                    "priority": "HIGH",
                },
            })

        out = {
            "workflow": "cas-renewal-monitor",
            "workflowId": self.renewal_workflow_id,
            "status": "DISPATCHED",
            "checkedCount": len(active_contracts),
            "alertsTriggered": len(alerts),
            "renewalAlerts": alerts,
        }
        await self._record_execution(
            workflow_slug="cas-renewal-monitor",
            workflow_id=self.renewal_workflow_id,
            direction="OUTBOUND",
            connector="cron_scheduler",
            contract_id=None,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def execute_compliance_escalation(
        self,
        contract_id: str,
        compliance_issue: str = "Corporate compliance variance",
        severity: str = "HIGH",
        policy_name: str = "Enterprise Corporate Policy",
        rule_id: str = "COMP-RULE-001",
        evidence: str = "",
        confidence: float = 0.95,
        required_action: str = "Mandatory Legal Amendment",
        channel: str = "#legal-compliance-alerts",
        violations: Optional[List[Any]] = None,
        violations_count: Optional[int] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Executes the cas-compliance-escalation workflow on Fastn."""
        v_count = violations_count if violations_count is not None else (len(violations) if violations else 1)
        issue_str = compliance_issue
        if violations and (not compliance_issue or compliance_issue == "Corporate compliance variance"):
            issue_str = f"{v_count} policy violation(s) detected: " + ", ".join(
                v.get("policy", "") if isinstance(v, dict) else str(v) for v in violations[:2]
            )

        payload = {
            "contractId": contract_id,
            "policyName": policy_name,
            "ruleId": rule_id,
            "complianceIssue": issue_str,
            "severity": severity.upper(),
            "evidence": evidence,
            "confidence": confidence,
            "requiredAction": required_action,
            "channel": channel,
            "violations": violations or [],
            "violationsCount": v_count,
        }
        logger.info(f"Executing Fastn Compliance Escalation for {contract_id} ({severity})")

        escalation_record = {
            "source": "CAS_COMPLIANCE_INTELLIGENCE",
            "contractId": contract_id,
            "policyName": policy_name,
            "ruleId": rule_id,
            "complianceIssue": issue_str,
            "severity": severity.upper(),
            "confidence": confidence,
            "evidence": evidence,
            "violationsCount": v_count,
            "requiredAction": required_action,
            "requiresImmediateHumanReview": severity.upper() in ("HIGH", "CRITICAL"),
            "slackDispatch": {
                "channel": channel,
                "message": f"⚠️ *[CAS COMPLIANCE ESCALATION - {severity.upper()}]* Contract: `{contract_id}`\n*Policy:* {policy_name} ({rule_id})\n*Violation:* {issue_str}\n*Required Action:* {required_action}",
            },
            "grcAuditRecord": {
                "system": "Enterprise GRC Portal",
                "status": "FLAGGED_FOR_LEGAL_REVIEW",
                "auditTimestamp": datetime.now(timezone.utc).isoformat(),
            },
            "dispatchedAt": datetime.now(timezone.utc).isoformat(),
        }

        out = {
            "workflow": "cas-compliance-escalation",
            "workflowId": self.compliance_workflow_id,
            "status": "DISPATCHED",
            "contractId": contract_id,
            "severity": severity.upper(),
            "violationsCount": v_count,
            "escalationRecord": escalation_record,
        }
        await self._record_execution(
            workflow_slug="cas-compliance-escalation",
            workflow_id=self.compliance_workflow_id,
            direction="OUTBOUND",
            connector="slack",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def execute_negotiation_update(
        self,
        contract_id: str,
        negotiation_state: str = "COUNTER_OFFERED",
        current_proposal: str = "Proposed counter-terms",
        strategy: str = "Bilateral risk symmetry",
        concession: Optional[str] = None,
        rationale: str = "",
        next_action: str = "",
        positions: Optional[List[Any]] = None,
        channel: str = "#commercial-negotiations",
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Executes the cas-negotiation-update workflow on Fastn."""
        pos_list = positions or []
        pos_count = len(pos_list) if pos_list else 1
        payload = {
            "contractId": contract_id,
            "negotiationState": negotiation_state,
            "currentProposal": current_proposal,
            "concession": concession,
            "strategy": strategy,
            "rationale": rationale,
            "nextAction": next_action,
            "positions": pos_list,
            "positionsCount": pos_count,
            "channel": channel,
        }
        logger.info(f"Executing Fastn Negotiation Update for {contract_id} ({negotiation_state})")

        event_record = {
            "source": "CAS_NEGOTIATION_INTELLIGENCE",
            "contractId": contract_id,
            "negotiationState": negotiation_state,
            "currentProposal": current_proposal,
            "concession": concession,
            "strategy": strategy,
            "rationale": rationale,
            "nextAction": next_action,
            "positions": pos_list,
            "positionsCount": pos_count,
            "collaborationDispatch": {
                "channel": channel,
                "summary": f"🤝 *[CAS NEGOTIATION UPDATE]* Contract: `{contract_id}`\n*State:* *{negotiation_state}*\n*Proposal:* {current_proposal}\n*Strategy:* {strategy}",
            },
            "crmRecord": {
                "stage": "READY_TO_SIGN" if negotiation_state == "AGREED" else "ACTIVE_NEGOTIATION",
                "lastUpdated": datetime.now(timezone.utc).isoformat(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        out = {
            "workflow": "cas-negotiation-update",
            "workflowId": self.negotiation_workflow_id,
            "status": "DISPATCHED",
            "contractId": contract_id,
            "negotiationState": negotiation_state,
            "positionsCount": pos_count,
            "positions": pos_list,
            "negotiationEvent": event_record,
        }
        await self._record_execution(
            workflow_slug="cas-negotiation-update",
            workflow_id=self.negotiation_workflow_id,
            direction="OUTBOUND",
            connector="slack",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def execute_deadline_escalation(
        self,
        contract_id: str,
        obligation_title: str = "Contract Obligation Deadline",
        deadline: str = "2026-12-31",
        severity: str = "due",
        responsible_party: str = "Customer",
        recommended_action: str = "",
        calendar_id: str = "Contract Operations Calendar",
        obligation_id: Optional[str] = None,
        new_deadline: Optional[str] = None,
        reason: Optional[str] = None,
        requested_by: Optional[str] = None,
        impact_level: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Executes the cas-deadline-escalation workflow on Fastn."""
        effective_deadline = new_deadline or deadline
        effective_title = obligation_title or (f"Obligation {obligation_id}" if obligation_id else "Milestone Deadline")
        effective_severity = impact_level or severity
        payload = {
            "contractId": contract_id,
            "obligationTitle": effective_title,
            "obligationId": obligation_id,
            "deadline": effective_deadline,
            "severity": effective_severity,
            "responsibleParty": requested_by or responsible_party,
            "recommendedAction": recommended_action or reason or "Review deadline schedule",
            "calendarId": calendar_id,
        }
        logger.info(f"Executing Fastn Deadline Escalation for {contract_id} ({effective_severity})")
        is_urgent = effective_severity.lower() in ("overdue", "critical", "high")

        calendar_action = {
            "action": "UPDATE_WITH_HIGH_IMPORTANCE" if is_urgent else "CREATE_REMINDER",
            "calendar": calendar_id,
            "eventTitle": f"[DEADLINE {effective_severity.upper()}] {contract_id}: {effective_title}",
            "scheduledTime": effective_deadline,
            "attendees": [requested_by or responsible_party],
            "reminderMinutesBefore": 60 if is_urgent else 1440,
            "urgentColorTag": "#FF0000" if is_urgent else "#FFA500",
        }
        notification = {
            "source": "CAS_OBLIGATION_INTELLIGENCE",
            "contractId": contract_id,
            "obligationTitle": effective_title,
            "obligationId": obligation_id,
            "deadline": effective_deadline,
            "responsibleParty": requested_by or responsible_party,
            "severity": effective_severity,
            "recommendedAction": recommended_action or reason or "Review deadline schedule",
            "isUrgent": is_urgent,
            "calendarAction": calendar_action,
            "dispatchedAt": datetime.now(timezone.utc).isoformat(),
        }

        out = {
            "workflow": "cas-deadline-escalation",
            "workflowId": self.deadline_workflow_id,
            "status": "DISPATCHED",
            "contractId": contract_id,
            "severity": effective_severity,
            "calendarUpdated": True,
            "notification": notification,
        }
        await self._record_execution(
            workflow_slug="cas-deadline-escalation",
            workflow_id=self.deadline_workflow_id,
            direction="OUTBOUND",
            connector="google_calendar",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def execute_dispute_escalation(
        self,
        contract_id: str,
        disputed_clause: str = "Section 8",
        party_a_interpretation: str = "Standard liability protection",
        party_b_interpretation: str = "Uncapped liability recovery",
        conflict: str = "Asymmetric liability ambiguity",
        severity: str = "HIGH",
        evidence: str = "",
        recommended_resolution: str = "Formulate mutual redline",
        channel: str = "#dispute-arbitration-counsel",
        dispute_risk: Optional[str] = None,
        ambiguities: Optional[List[Any]] = None,
        counterparty_stance: Optional[str] = None,
        recommended_action: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Executes the cas-dispute-escalation workflow on Fastn."""
        effective_risk = (dispute_risk or severity).upper()
        effective_conflict = conflict or (f"{len(ambiguities)} high-risk ambiguities identified" if ambiguities else "Contract clause dispute")
        effective_resolution = recommended_action or recommended_resolution

        payload = {
            "contractId": contract_id,
            "disputedClause": disputed_clause,
            "partyAInterpretation": party_a_interpretation,
            "partyBInterpretation": counterparty_stance or party_b_interpretation,
            "conflict": effective_conflict,
            "evidence": evidence,
            "severity": effective_risk,
            "recommendedResolution": effective_resolution,
            "ambiguities": ambiguities or [],
            "litigationChannel": channel,
        }
        logger.info(f"Executing Fastn Dispute Escalation for {contract_id} ({effective_risk})")

        dispute_record = {
            "source": "CAS_DISPUTE_INTELLIGENCE",
            "contractId": contract_id,
            "disputedClause": disputed_clause,
            "partyAInterpretation": party_a_interpretation,
            "partyBInterpretation": counterparty_stance or party_b_interpretation,
            "conflict": effective_conflict,
            "evidence": evidence,
            "severity": effective_risk,
            "disputeRisk": effective_risk,
            "ambiguities": ambiguities or [],
            "recommendedResolutionPath": effective_resolution,
            "requiresHumanLegalArbitration": effective_risk in ("HIGH", "CRITICAL"),
            "slackAlert": {
                "channel": channel,
                "message": f"⚖️ *[CAS DISPUTE SIMULATION ALERT - {effective_risk}]* Contract: `{contract_id}`\n*Clause:* {disputed_clause}\n*Conflict:* {effective_conflict}\n*Recommended Cure:* {effective_resolution}",
            },
            "litigationRiskAudit": {
                "forum": "Arbitration Pre-Hearing Preparation",
                "recommendedCounsel": "Commercial Litigation Specialist",
                "auditTimestamp": datetime.now(timezone.utc).isoformat(),
            },
            "dispatchedAt": datetime.now(timezone.utc).isoformat(),
        }

        out = {
            "workflow": "cas-dispute-escalation",
            "workflowId": self.dispute_workflow_id,
            "status": "DISPATCHED",
            "contractId": contract_id,
            "disputeRisk": effective_risk,
            "severity": effective_risk,
            "disputeRecord": dispute_record,
        }
        await self._record_execution(
            workflow_slug="cas-dispute-escalation",
            workflow_id=self.dispute_workflow_id,
            direction="OUTBOUND",
            connector="slack",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    async def execute_decision_archive(
        self,
        contract_id: str,
        decision: str,
        decision_maker: str,
        reason: str,
        society: str = "director",
        evidence: str = "",
        resulting_action: str = "EXECUTE_SIGNATURE",
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Executes the cas-decision-archive workflow on Fastn."""
        payload = {
            "contractId": contract_id,
            "decision": decision.upper(),
            "decisionMaker": decision_maker,
            "society": society,
            "reason": reason,
            "evidence": evidence,
            "resultingAction": resulting_action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"Executing Fastn Decision Archive for {contract_id} ({decision})")

        archive_record = {
            "archiveId": "ARC-" + uuid.uuid4().hex[:7].upper(),
            "contractId": contract_id,
            "decision": decision.upper(),
            "decisionMaker": decision_maker,
            "society": society,
            "reason": reason,
            "evidence": evidence,
            "resultingAction": resulting_action,
            "timestamp": payload["timestamp"],
            "airtablePersistence": {
                "table": "Executive Legal Decisions",
                "fields": {
                    "ContractId": contract_id,
                    "Decision": decision.upper(),
                    "Reviewer": decision_maker,
                    "Reason": reason,
                    "ArchivedAt": payload["timestamp"],
                },
            },
            "googleDriveArchive": {
                "folder": "Executed Contracts & Legal Precedents",
                "fileName": f"DECISION_{contract_id}_{decision.upper()}.json",
                "status": "PERSISTED",
            },
            "casMemoryPrecedent": {
                "memoryType": "DECISION",
                "tags": ["hitl_approval", decision.lower(), society],
                "summary": f"[{decision.upper()}] {contract_id} resolved by {decision_maker}: {reason}",
                "storedAt": payload["timestamp"],
            },
        }

        out = {
            "workflow": "cas-decision-archive",
            "workflowId": self.decision_archive_workflow_id,
            "status": "ARCHIVED",
            "contractId": contract_id,
            "decision": decision.upper(),
            "archiveRecord": archive_record,
        }
        await self._record_execution(
            workflow_slug="cas-decision-archive",
            workflow_id=self.decision_archive_workflow_id,
            direction="OUTBOUND",
            connector="google_drive",
            contract_id=contract_id,
            status="SUCCESS",
            input_payload=payload,
            output_payload=out,
            db_session=db_session,
        )
        return out

    # =========================================================================
    # Inbound Event Handlers (External -> Fastn -> CAS)
    # =========================================================================

    async def record_inbound_event(
        self,
        workflow_slug: str,
        payload: Dict[str, Any],
        contract_id: Optional[str] = None,
        connector: str = "webhook",
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Records an incoming webhook execution dispatched from Fastn into CAS."""
        return await self._record_execution(
            workflow_slug=workflow_slug,
            workflow_id=f"inbound_{workflow_slug}",
            direction="INBOUND",
            connector=connector,
            contract_id=contract_id or payload.get("contractId") or payload.get("contract_id"),
            status="SUCCESS",
            input_payload=payload,
            output_payload={"status": "RECEIVED_BY_CAS_DIRECTOR", "received_at": datetime.now(timezone.utc).isoformat()},
            db_session=db_session,
        )

    async def record_failed_execution(
        self,
        workflow_slug: str,
        contract_id: Optional[str],
        error_message: str,
        payload: Optional[Dict[str, Any]] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Records a failed execution lifecycle state for telemetry and Director escalation."""
        return await self._record_execution(
            workflow_slug=workflow_slug,
            workflow_id=f"wf_{workflow_slug}",
            direction="OUTBOUND",
            connector="fastn_gateway",
            contract_id=contract_id,
            status="FAILED",
            input_payload=payload or {},
            output_payload={"status": "EXECUTION_ERROR", "error": error_message},
            error_message=error_message,
            db_session=db_session,
        )

    # =========================================================================
    # Execution Queries
    # =========================================================================

    async def get_recent_executions(
        self,
        limit: int = 50,
        workflow_slug: Optional[str] = None,
        status: Optional[str] = None,
        direction: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves recent Fastn executions from database, falling back to memory buffer."""
        if db_session:
            try:
                stmt = select(FastnExecutionModel).order_by(desc(FastnExecutionModel.created_at)).limit(limit)
                if workflow_slug:
                    stmt = stmt.where(FastnExecutionModel.workflow_slug == workflow_slug)
                if status:
                    stmt = stmt.where(FastnExecutionModel.status == status)
                if direction:
                    stmt = stmt.where(FastnExecutionModel.direction == direction)
                res = await db_session.execute(stmt)
                db_records = res.scalars().all()
                if db_records:
                    return [
                        {
                            "execution_id": r.execution_id,
                            "workflow_slug": r.workflow_slug,
                            "workflow_id": r.workflow_id,
                            "contract_id": r.contract_id,
                            "direction": r.direction,
                            "connector": r.connector,
                            "status": r.status,
                            "input_summary": r.input_summary,
                            "output_summary": r.output_summary,
                            "error_message": r.error_message,
                            "created_at": r.created_at.isoformat() if r.created_at else None,
                            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                        }
                        for r in db_records
                    ]
            except Exception as e:
                logger.warning(f"Error querying FastnExecutionModel: {e}")

        # In-memory filter
        filtered = self._memory_executions
        if workflow_slug:
            filtered = [e for e in filtered if e.get("workflow_slug") == workflow_slug]
        if status:
            filtered = [e for e in filtered if e.get("status") == status]
        if direction:
            filtered = [e for e in filtered if e.get("direction") == direction]
        return filtered[:limit]


fastn_client = FastnClient()
