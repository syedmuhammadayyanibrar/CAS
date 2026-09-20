from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from backend.core.config import settings
from backend.database.db import get_db
from backend.integrations.fastn_client import fastn_client
from backend.core.logging import get_logger

logger = get_logger("AutomationsAPI")
router = APIRouter(prefix="/automations", tags=["Fastn Automations"])


class ExecuteAutomationRequest(BaseModel):
    payload: Optional[Dict[str, Any]] = None


class GoogleDriveImportRequest(BaseModel):
    document_id: str = "gdrive_novacloud_saas_2026"
    custom_url: Optional[str] = None
    auto_create_contract: bool = False


@router.get("/google-drive/files")
async def list_google_drive_files():
    """
    Lists connected legal contract documents from Google Drive available for
    intake via Fastn.
    """
    return fastn_client.get_google_drive_documents()


@router.post("/google-drive/import")
async def import_google_drive_contract(
    req: GoogleDriveImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers Fastn's cas-contract-intake workflow (wf_0c61baf31b93) for an incoming
    Google Drive contract document, records execution in Fastn nervous system,
    and returns extracted text and metadata.
    """
    res = await fastn_client.import_from_google_drive(
        document_id=req.document_id,
        custom_url=req.custom_url,
        db_session=db
    )

    if req.auto_create_contract:
        from backend.database.schema import ContractModel
        contract = ContractModel(
            id=res["contract_id"],
            title=res["title"],
            raw_text=res["content"],
            status="INTAKE",
            governing_law=res.get("governing_law"),
            metadata_json={
                "source": "google_drive",
                "fastn_workflow": "cas-contract-intake",
                "document_id": req.document_id,
                "filename": res["filename"],
                "counterparty": res.get("counterparty"),
            }
        )
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        res["database_registered"] = True

    return res


@router.get("")
async def list_automations():
    """
    Lists all 10 deployed Fastn workflows, webhooks, and schedulers serving as
    the bidirectional nervous system for CAS.
    """
    catalog = fastn_client.get_workflow_catalog()

    # Enrich catalog with default payloads and descriptions for UI interactive testing
    enriched = []
    for wf in catalog:
        slug = wf["slug"]
        item = dict(wf)

        if slug == "cas-contract-intake":
            item["default_payload"] = {
                "contractId": "CTR-INTAKE-TEST",
                "documentName": "vendor_master_services_agreement.pdf",
                "source": "google_drive",
                "content": "Master Services Agreement between Customer and Cloud Services Inc."
            }
        elif slug == "cas-risk-escalation":
            item["default_payload"] = {
                "contractId": "CTR-DEMO-2026-SAAS",
                "severity": "CRITICAL",
                "riskyClause": "Section 8.2 Asymmetric Cap",
                "consequence": "Unlimited Customer exposure with 1-month Vendor shield",
                "evidence": "Customer total aggregate liability shall be uncapped.",
                "channel": "#legal-contract-risks"
            }
        elif slug == "cas-approval-dispatch":
            item["default_payload"] = {
                "contractId": "CTR-DEMO-2026-SAAS",
                "reason": "Uncapped indemnity and severe indemnification asymmetry",
                "requestedAction": "Approve redline amendment or reject contract",
                "agentConclusions": ["Risk: CRITICAL (0.85)", "Compliance: 2 Violations"],
                "reviewerEmail": "legal-lead@organization.com"
            }
        elif slug == "cas-obligation-sync":
            item["default_payload"] = {
                "contractId": "CTR-DEMO-2026-SAAS",
                "obligations": [
                    {
                        "title": "Annual Security Audit Report",
                        "party": "NovaCloud",
                        "dueDate": "2027-01-15",
                        "type": "AUDIT",
                        "noticeDays": 30
                    },
                    {
                        "title": "Net 30 Invoicing Payment",
                        "party": "Acme Global",
                        "dueDate": "2026-11-01",
                        "type": "PAYMENT",
                        "noticeDays": 7
                    }
                ]
            }
        elif slug == "cas-renewal-monitor":
            item["default_payload"] = {
                "activeContracts": [
                    {
                        "contractId": "CTR-DEMO-2026-SAAS",
                        "name": "NovaCloud Enterprise SaaS Agreement",
                        "renewalDate": "2026-11-15",
                        "noticePeriodDays": 60,
                        "autoRenews": True
                    }
                ]
            }
        elif slug == "cas-compliance-escalation":
            item["default_payload"] = {
                "contractId": "CTR-DEMO-2026-SAAS",
                "policyName": "Corporate Standard Vendor Policy v2.4",
                "violationsCount": 2,
                "violations": [
                    {"policy": "GDPR Standard Contractual Clauses", "severity": "CRITICAL", "description": "Mandatory EU sub-processor audit clause missing from Article 14."},
                    {"policy": "Payment Term Ceiling", "severity": "HIGH", "description": "Vendor demands Net 15 instead of standard corporate Net 60 policy."}
                ]
            }
        elif slug == "cas-negotiation-update":
            item["default_payload"] = {
                "contractId": "CTR-DEMO-2026-SAAS",
                "positions": [
                    {
                        "clause": "Section 8.2 Limitation of Liability",
                        "status": "COUNTER_OFFERED",
                        "originalTerm": "Unilateral Customer uncapped liability with $50k Vendor shield",
                        "proposedRedline": "Mutual aggregate liability capped at 12 months fees paid ($240,000)",
                        "rationale": "Enforce corporate symmetry policy."
                    }
                ],
                "channel": "#contract-negotiations"
            }
        elif slug == "cas-deadline-escalation":
            item["default_payload"] = {
                "contractId": "CTR-DEMO-2026-SAAS",
                "obligationId": "OBL-AUDIT-2026",
                "newDeadline": "2026-12-15",
                "reason": "SOC2 Type II external audit firm delay requested by Vendor",
                "requestedBy": "NovaCloud Compliance Officer",
                "impactLevel": "HIGH"
            }
        elif slug == "cas-dispute-escalation":
            item["default_payload"] = {
                "contractId": "CTR-DEMO-2026-SAAS",
                "disputeRisk": "HIGH",
                "ambiguities": [
                    "Section 14.1 vague SLA downtime definition conflicts with Section 4 credit mechanism.",
                    "Choice of law specifies Delaware but arbitration venue designates London."
                ],
                "counterpartyStance": "Vendor likely to argue downtime caused by upstream cloud provider is exempt from service credits.",
                "recommendedAction": "Require pre-litigation redline harmonization before commercial execution."
            }
        elif slug == "cas-decision-archive":
            item["default_payload"] = {
                "contractId": "CTR-DEMO-2026-SAAS",
                "decision": "APPROVED",
                "decisionMaker": "General Counsel / VP Legal",
                "society": "CAS_FEDERATION",
                "reason": "Redline compromise accepted with 12-month mutual fee liability cap.",
                "evidence": "Risk score reduced from 0.85 to 0.22 following bilateral concession.",
                "resultingAction": "EXECUTE_SIGNATURE"
            }

        enriched.append(item)

    return {
        "org_id": settings.FASTN_ORG_ID,
        "total_workflows": len(enriched),
        "workflows": enriched
    }


@router.get("/executions")
async def list_executions(
    limit: int = Query(50, ge=1, le=200),
    workflow_slug: Optional[str] = None,
    status: Optional[str] = None,
    direction: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns recent Fastn execution traces with masked sensitive parameters.
    Provides complete visibility into the bidirectional nervous system.
    """
    traces = await fastn_client.get_recent_executions(
        limit=limit,
        workflow_slug=workflow_slug,
        status=status,
        direction=direction,
        db_session=db
    )
    return {
        "total": len(traces),
        "executions": traces
    }


@router.get("/{slug}/executions")
async def list_workflow_executions(
    slug: str,
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Returns execution trace history specifically for a single workflow slug."""
    traces = await fastn_client.get_recent_executions(
        limit=limit,
        workflow_slug=slug,
        db_session=db
    )
    return {
        "workflow": slug,
        "total": len(traces),
        "executions": traces
    }


@router.post("/{slug}/execute")
async def execute_automation(
    slug: str,
    req: ExecuteAutomationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Executes a specific Fastn workflow with provided or default test data."""
    payload = req.payload or {}

    try:
        if slug == "cas-contract-intake":
            res = await fastn_client.trigger_intake_webhook(
                payload=payload or {
                    "contractId": "CTR-MANUAL-INTAKE",
                    "documentName": "manual_test_doc.pdf",
                    "source": "api_test",
                    "content": "Master Services Agreement between Parties"
                },
                db_session=db
            )
            return {"workflow": slug, "result": res}

        elif slug == "cas-risk-escalation":
            res = await fastn_client.execute_risk_escalation(
                contract_id=payload.get("contractId", "CTR-TEST-001"),
                severity=payload.get("severity", "HIGH"),
                risky_clause=payload.get("riskyClause", "Section 8.2 Limitation of Liability"),
                consequence=payload.get("consequence", "Uncapped customer exposure"),
                evidence=payload.get("evidence", "Total liability shall be uncapped."),
                channel=payload.get("channel", "#legal-contract-risks"),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        elif slug == "cas-approval-dispatch":
            res = await fastn_client.execute_approval_dispatch(
                contract_id=payload.get("contractId", "CTR-TEST-001"),
                reason=payload.get("reason", "High-severity risk requires general counsel review"),
                requested_action=payload.get("requestedAction", "Approve redline amendment"),
                agent_conclusions=payload.get("agentConclusions", ["Risk: HIGH", "Compliance: 1 Variance"]),
                reviewer_email=payload.get("reviewerEmail", "general_counsel@organization.com"),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        elif slug == "cas-obligation-sync":
            res = await fastn_client.execute_obligation_sync(
                contract_id=payload.get("contractId", "CTR-TEST-001"),
                obligations=payload.get("obligations", [
                    {"title": "Deliver Security Attestation", "party": "Vendor", "dueDate": "2026-12-01", "type": "AUDIT"}
                ]),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        elif slug == "cas-renewal-monitor":
            res = await fastn_client.execute_renewal_monitor(
                active_contracts=payload.get("activeContracts", [
                    {"contractId": "CTR-TEST-001", "name": "Vendor Subscription", "renewalDate": "2026-11-01", "noticePeriodDays": 60, "autoRenews": True}
                ]),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        elif slug == "cas-compliance-escalation":
            res = await fastn_client.execute_compliance_escalation(
                contract_id=payload.get("contractId", "CTR-TEST-001"),
                policy_name=payload.get("policyName", "Corporate Compliance Policy"),
                violations_count=payload.get("violationsCount", 1),
                violations=payload.get("violations", [{"policy": "Data Privacy", "severity": "HIGH", "description": "Breach notification period exceeds 72 hours"}]),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        elif slug == "cas-negotiation-update":
            res = await fastn_client.execute_negotiation_update(
                contract_id=payload.get("contractId", "CTR-TEST-001"),
                positions=payload.get("positions", [
                    {"clause": "Section 8.2", "status": "COUNTER_OFFERED", "originalTerm": "Unilateral", "proposedRedline": "Mutual $250k cap", "rationale": "Symmetry"}
                ]),
                channel=payload.get("channel", "#contract-negotiations"),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        elif slug == "cas-deadline-escalation":
            res = await fastn_client.execute_deadline_escalation(
                contract_id=payload.get("contractId", "CTR-TEST-001"),
                obligation_id=payload.get("obligationId", "OBL-001"),
                new_deadline=payload.get("newDeadline", "2026-12-31"),
                reason=payload.get("reason", "Vendor operational delay requested"),
                requested_by=payload.get("requestedBy", "Vendor Operations"),
                impact_level=payload.get("impactLevel", "HIGH"),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        elif slug == "cas-dispute-escalation":
            res = await fastn_client.execute_dispute_escalation(
                contract_id=payload.get("contractId", "CTR-TEST-001"),
                dispute_risk=payload.get("disputeRisk", "HIGH"),
                ambiguities=payload.get("ambiguities", ["Vague SLA termination clause", "Unclear arbitration venue"]),
                counterparty_stance=payload.get("counterpartyStance", "Opposing counsel will argue non-breach due to force majeure"),
                recommended_action=payload.get("recommendedAction", "Harmonize dispute clause before execution"),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        elif slug == "cas-decision-archive":
            res = await fastn_client.execute_decision_archive(
                contract_id=payload.get("contractId", "CTR-TEST-001"),
                decision=payload.get("decision", "APPROVED"),
                decision_maker=payload.get("decisionMaker", "Legal Director"),
                society=payload.get("society", "CAS_FEDERATION"),
                reason=payload.get("reason", "Approved redline concessions"),
                evidence=payload.get("evidence", "Bilateral risk mitigation completed"),
                resulting_action=payload.get("resultingAction", "EXECUTE_SIGNATURE"),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        # Simulated Inbound paths (Inbound Approval, Inbound Negotiation, Inbound Deadline)
        elif slug in ("cas-inbound-approval", "inbound-approval"):
            res = await fastn_client.trigger_inbound_approval(
                contract_id=payload.get("contractId", "CTR-TEST-001"),
                decision=payload.get("decision", "APPROVED"),
                reviewer_id=payload.get("reviewerId", "general_counsel@organization.com"),
                decision_notes=payload.get("decisionNotes", "Approved via interactive automation test trigger"),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        elif slug in ("cas-inbound-negotiation", "inbound-negotiation"):
            res = await fastn_client.trigger_inbound_negotiation(
                contract_id=payload.get("contractId", "CTR-TEST-001"),
                clause_reference=payload.get("clauseReference", "Section 8.2"),
                counterparty_proposal=payload.get("counterpartyProposal", "Vendor agrees to mutual $500,000 cap"),
                concession_offered=payload.get("concessionOffered", "Agreed to mutualize liability cap"),
                db_session=db
            )
            return {"workflow": slug, "result": res}

        else:
            raise HTTPException(status_code=404, detail=f"Workflow {slug} not recognized.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute Fastn workflow {slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
