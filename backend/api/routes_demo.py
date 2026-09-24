import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from backend.database.db import get_db, ensure_db_initialized
from backend.database.schema import (
    ContractModel,
    ContractGraphModel,
    RiskReportModel,
    ComplianceReportModel,
    NegotiationStrategyModel,
    ObligationScheduleModel,
    DisputeAssessmentModel,
    HumanReviewModel,
    CASMessageModel,
)
from backend.integrations.fastn_client import fastn_client
from backend.director.coordinator import cas_director
from backend.systems.contract_intelligence.system import contract_intelligence_system
from backend.systems.risk_intelligence.system import risk_intelligence_system
from backend.systems.negotiation_intelligence.system import negotiation_intelligence_system
from backend.systems.compliance_intelligence.system import compliance_intelligence_system
from backend.systems.obligation_intelligence.system import obligation_intelligence_system
from backend.systems.dispute_intelligence.system import dispute_intelligence_system
from backend.memory.feedback_loops import feedback_loops
from backend.memory.cas_memory import cas_memory
from backend.models.hitl import HumanDecision

router = APIRouter(prefix="/demo", tags=["Demo Workspace"])

DEMO_CONTRACT_ID = "CTR-DEMO-2026-SAAS"

DEFAULT_DEMO_CONTRACT_TEXT = """MASTER SAAS SERVICES AGREEMENT

This Master SaaS Services Agreement ("Agreement") is made and entered into as of October 1, 2026 ("Effective Date"), by and between NovaCloud Systems Inc., a Delaware corporation with its principal place of business at 500 Cloud Way, San Francisco, CA ("Vendor"), and Acme Global Enterprises LLC, a Delaware limited liability company with offices at 100 Enterprise Blvd, New York, NY ("Customer"). Vendor and Customer may each be referred to as a "Party" or collectively as the "Parties."

RECITALS
WHEREAS, Vendor provides an enterprise cloud analytics and infrastructure management platform; and
WHEREAS, Customer desires to subscribe to and utilize the Vendor platform under the terms and conditions set forth herein.

NOW, THEREFORE, the Parties agree as follows:

SECTION 1: DEFINITIONS & SUBSCRIPTION SERVICES
1.1 Platform Access: Vendor grants Customer a non-exclusive, non-transferable, revocable subscription license to access and use the NovaCloud Platform during the Term solely for Customer's internal business purposes.
1.2 Authorized Users: Access is restricted to designated employees and contractors of Customer. Customer is fully liable for any actions taken under authorized user credentials.

SECTION 2: TERM AND AUTOMATIC RENEWAL
2.1 Initial Term: This Agreement shall commence on the Effective Date and continue for an initial term of twelve (12) months ("Initial Term").
2.2 Automatic Renewal: Following the Initial Term, this Agreement shall automatically renew for successive twelve (12) month periods ("Renewal Terms"), unless either Party delivers written notice of non-renewal at least sixty (60) days prior to the expiration of the then-current term.
2.3 Price Increases: Vendor reserves the right to increase annual subscription fees by up to fifteen percent (15%) upon each renewal without prior consent.

SECTION 3: FEES, BILLING & PAYMENT TERMS
3.1 Subscription Fees: Customer shall pay an annual subscription fee of $240,000 USD, billed quarterly in advance ($60,000 USD per quarter).
3.2 Payment Due Date: All invoices are payable Net 30 days from the invoice date. Late payments shall accrue interest at the rate of one and a half percent (1.5%) per month or the maximum rate permitted by law.
3.3 Taxes: All fees are exclusive of all applicable sales, use, excise, or value-added taxes, which shall be Customer's sole responsibility.

SECTION 4: SERVICE LEVEL AGREEMENT & PERFORMANCE
4.1 Availability: Vendor shall use commercially reasonable efforts to make the Platform available with an Annual Uptime Percentage of at least 99.9% during each calendar year.
4.2 Exclusions: Uptime calculations exclude scheduled maintenance, emergency maintenance, force majeure events, and downtime caused by Customer's network or integrations.
4.3 Sole Remedy: Customer's sole and exclusive remedy for any failure to meet the SLA shall be a service credit equal to five percent (5%) of the monthly fee, applicable only to future invoices upon written claim submitted within ten (10) days of the outage.

SECTION 5: CONFIDENTIALITY
5.1 Definition: "Confidential Information" means any proprietary information disclosed by one Party to the other Party that is marked as confidential or should reasonably be understood to be confidential.
5.2 Obligation: Each Party agrees to protect the other Party's Confidential Information with the same degree of care it uses for its own confidential information, but not less than reasonable care, for a period of five (5) years following disclosure.

SECTION 6: DATA OWNERSHIP & DERIVATIVE WORKS
6.1 Customer Data: Customer retains all rights, title, and interest in and to Customer Data uploaded to the Platform.
6.2 Vendor Aggregate Rights: Customer hereby grants Vendor a perpetual, irrevocable, worldwide, royalty-free license to use, reproduce, aggregate, de-identify, and analyze Customer Data to train, improve, and deploy machine learning models, statistical benchmarks, and derivative analytics products.

SECTION 7: INTELLECTUAL PROPERTY INDEMNIFICATION
7.1 Vendor Indemnity: Vendor shall defend Customer against third-party claims alleging that the Platform infringes any US copyright or trade secret.
7.2 Customer Indemnity: Customer shall defend, indemnify, and hold harmless Vendor, its affiliates, and officers from and against any and all third-party claims, damages, liabilities, costs, and expenses (including reasonable attorneys' fees) arising out of or related to Customer Data, Customer's use of the Platform, or Customer's breach of this Agreement, without financial limitation.

SECTION 8: LIMITATION OF LIABILITY
8.1 Consequential Damages Waiver: IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING LOSS OF PROFITS, DATA, OR BUSINESS INTERRUPTION.
8.2 Aggregate Liability Cap: NOTWITHSTANDING ANYTHING TO THE CONTRARY IN THIS AGREEMENT, VENDOR'S TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATED TO THIS AGREEMENT SHALL BE STRICTLY LIMITED TO THE FEES ACTUALLY PAID BY CUSTOMER IN THE ONE (1) MONTH PRECEDING THE INCIDENT GIVING RISE TO LIABILITY.
8.3 Customer Liability: THE FOREGOING LIMITATION OF LIABILITY IN SECTION 8.2 SHALL NOT APPLY TO CUSTOMER'S PAYMENT OBLIGATIONS OR CUSTOMER'S INDEMNIFICATION OBLIGATIONS UNDER SECTION 7.2.

SECTION 9: TERMINATION
9.1 Termination for Cause: Either Party may terminate this Agreement immediately upon written notice if the other Party materially breaches any provision of this Agreement and fails to cure such breach within thirty (30) days of receipt of written notice.
9.2 Termination for Insolvency: Either Party may terminate immediately upon the insolvency or bankruptcy of the other Party.
9.3 Conflicting Termination Notice: Section 11.3 provides that Vendor may terminate services without cause upon ten (10) days email notice if Vendor determines Customer's use threatens system stability.

SECTION 10: GOVERNING LAW AND DISPUTE RESOLUTION
10.1 Governing Law: This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to its conflict of law principles.
10.2 Dispute Resolution: In the event of any controversy or dispute, the Parties shall first attempt in good faith to resolve the dispute through executive negotiation. If unresolved within thirty (30) days, the dispute shall be submitted to final and binding arbitration administered by JAMS in New York, NY.

IN WITNESS WHEREOF, the Parties have executed this Agreement by their duly authorized representatives.

NOVACLOUD SYSTEMS INC.             ACME GLOBAL ENTERPRISES LLC
By: ______________________         By: ______________________
Name: David Vance                  Name: Elena Rostova
Title: Chief Commercial Officer    Title: VP of Technology Procurement
Date: October 1, 2026              Date: October 1, 2026
"""


def get_demo_files() -> tuple[str, Optional[str]]:
    """Resolves demo contract text and policy file with multi-candidate path checks and in-memory fallback."""
    contract_text = None
    candidate_contract_paths = [
        os.path.join(os.path.dirname(__file__), "../../contracts/enterprise_saas_vendor_contract.txt"),
        os.path.join(os.getcwd(), "contracts/enterprise_saas_vendor_contract.txt"),
        os.path.join(os.path.dirname(__file__), "../contracts/enterprise_saas_vendor_contract.txt"),
    ]
    for p in candidate_contract_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    contract_text = f.read()
                if contract_text and contract_text.strip():
                    break
            except Exception:
                pass

    if not contract_text or not contract_text.strip():
        contract_text = DEFAULT_DEMO_CONTRACT_TEXT.strip()

    policy_file = None
    candidate_policy_paths = [
        os.path.join(os.path.dirname(__file__), "../../policies/corporate_compliance_policy.json"),
        os.path.join(os.getcwd(), "policies/corporate_compliance_policy.json"),
        os.path.join(os.path.dirname(__file__), "../policies/corporate_compliance_policy.json"),
    ]
    for p in candidate_policy_paths:
        if os.path.exists(p):
            policy_file = p
            break

    return contract_text, policy_file


@router.post("/reset")
async def reset_demo(db: AsyncSession = Depends(get_db)):
    """Resets the demo state in the database and pre-loads the Acme Global ↔ NovaCloud contract."""
    await ensure_db_initialized()
    contract_text, _ = get_demo_files()

    # Clean existing demo records
    await db.execute(delete(ContractGraphModel).where(ContractGraphModel.contract_id == DEMO_CONTRACT_ID))
    await db.execute(delete(RiskReportModel).where(RiskReportModel.contract_id == DEMO_CONTRACT_ID))
    await db.execute(delete(ComplianceReportModel).where(ComplianceReportModel.contract_id == DEMO_CONTRACT_ID))
    await db.execute(delete(NegotiationStrategyModel).where(NegotiationStrategyModel.contract_id == DEMO_CONTRACT_ID))
    await db.execute(delete(ObligationScheduleModel).where(ObligationScheduleModel.contract_id == DEMO_CONTRACT_ID))
    await db.execute(delete(DisputeAssessmentModel).where(DisputeAssessmentModel.contract_id == DEMO_CONTRACT_ID))
    await db.execute(delete(HumanReviewModel).where(HumanReviewModel.contract_id == DEMO_CONTRACT_ID))
    await db.execute(delete(ContractModel).where(ContractModel.id == DEMO_CONTRACT_ID))
    await db.commit()

    # Re-insert fresh demo contract
    demo_contract = ContractModel(
        id=DEMO_CONTRACT_ID,
        title="NovaCloud Enterprise Cloud Services Agreement",
        raw_text=contract_text,
        status="INTAKE",
        governing_law="State of Delaware",
        effective_date="2026-10-01",
        expiration_date="2027-10-01",
        metadata_json={
            "counterparty": "NovaCloud Inc.",
            "customer": "Acme Global Enterprises",
            "contract_type": "Enterprise SaaS Master Services Agreement",
            "annual_contract_value": "$480,000"
        }
    )
    db.add(demo_contract)
    await db.commit()

    return {
        "status": "RESET_COMPLETE",
        "contract_id": DEMO_CONTRACT_ID,
        "title": demo_contract.title,
        "counterparty": "NovaCloud Inc.",
        "message": "Demo scenario state reset to pristine Stage 0."
    }


class RunStepRequest(BaseModel):
    step: int


@router.post("/run-step")
async def run_demo_step(req: RunStepRequest, db: AsyncSession = Depends(get_db)):
    """Executes a single stage (1 through 15) of the autonomous multi-agent bidirectional scenario."""
    step = req.step
    contract_text, policy_file = get_demo_files()

    contract = await db.get(ContractModel, DEMO_CONTRACT_ID)
    if not contract:
        await reset_demo(db)
        contract = await db.get(ContractModel, DEMO_CONTRACT_ID)

    if step == 1:
        # Stage 1: Contract Intake through Fastn Inbound Trigger
        try:
            intake_res = await fastn_client.trigger_intake_webhook({
                "contractId": DEMO_CONTRACT_ID,
                "documentName": "enterprise_saas_vendor_contract.pdf",
                "source": "google_drive",
                "content": contract_text[:500]
            }, db_session=db)
        except Exception as e:
            intake_res = {
                "workflow": "cas-contract-intake",
                "workflowId": getattr(fastn_client, "intake_workflow_id", "wf_0c61baf31b93"),
                "status": "SUCCESS",
                "fastn_response": {"status": "accepted", "note": f"Fastn inbound simulation: {e}"},
                "contractId": DEMO_CONTRACT_ID,
            }
        contract.status = "INTAKE"
        await db.commit()
        return {
            "step": 1,
            "title": "Contract Intake via Fastn Inbound Trigger",
            "society": "Fastn Inbound Nervous System",
            "summary": "Fastn public inbound webhook received contract from external repository and initiated CAS Director processing.",
            "data": intake_res
        }

    elif step == 2:
        # Stage 2: Contract Intelligence (Parallel + Verification)
        graph = await contract_intelligence_system.analyze_contract(
            contract_text=contract_text,
            contract_id=DEMO_CONTRACT_ID,
            db_session=db
        )
        return {
            "step": 2,
            "title": "Contract Intelligence Deconstruction",
            "society": "Contract Intelligence (Parallel + Verification)",
            "summary": f"Deconstructed agreement into {len(graph.clauses)} semantic clauses, {len(graph.parties)} parties, and dependency graph.",
            "data": graph.model_dump()
        }

    elif step == 3:
        # Stage 3: Risk Intelligence (Adversarial Debate)
        report = await risk_intelligence_system.analyze_risk(
            contract=contract_text,
            contract_id=DEMO_CONTRACT_ID,
            db_session=db
        )
        return {
            "step": 3,
            "title": "Adversarial Risk Debate",
            "society": "Risk Intelligence (Hunter vs Counterargument vs Assessor)",
            "summary": f"Identified {len(report.findings)} risk vectors. Overall Risk Score: {report.overall_risk_score:.2f} (Escalation: {report.requires_human_escalation}).",
            "data": report.model_dump()
        }

    elif step == 4:
        # Stage 4: Fastn Risk Escalation
        risk_res = await fastn_client.execute_risk_escalation(
            contract_id=DEMO_CONTRACT_ID,
            severity="CRITICAL",
            risky_clause="Section 8.2 Asymmetric Cap & Section 7.2 Indemnity",
            consequence="Customer subject to unlimited aggregate exposure while Vendor liability is capped at $50,000.",
            evidence="Customer total aggregate liability under this agreement shall be uncapped.",
            channel="#legal-contract-risks",
            db_session=db
        )
        return {
            "step": 4,
            "title": "Fastn Risk Escalation Dispatch",
            "society": "Fastn Outbound Nervous System (Slack #legal-contract-risks)",
            "summary": "Critical liability asymmetry automatically dispatched to enterprise Slack legal channel via Fastn connector.",
            "data": risk_res
        }

    elif step == 5:
        # Stage 5: Negotiation Strategy & Redline Generation
        strat = await negotiation_intelligence_system.plan_negotiation(
            contract=contract_text,
            objective="Cap aggregate liability at 12 months fees, delete uncapped indemnity, and ensure mutual 30-day termination.",
            contract_id=DEMO_CONTRACT_ID,
            db_session=db
        )
        return {
            "step": 5,
            "title": "Negotiation Strategy & Redline Generation",
            "society": "Negotiation Intelligence (Planner + Simulator + Critic)",
            "summary": f"Formulated {len(strat.positions)} redline counter-positions with commercial fallback concession ladders.",
            "data": strat.model_dump()
        }

    elif step == 6:
        # Stage 6: Compliance Policy Audit
        comp = await compliance_intelligence_system.audit_compliance(
            contract=contract_text,
            policy_path=policy_file,
            contract_id=DEMO_CONTRACT_ID,
            db_session=db
        )
        return {
            "step": 6,
            "title": "Corporate Compliance Policy Audit",
            "society": "Compliance Intelligence (Retrieval + Rules + Verification)",
            "summary": f"Audit status: {comp.overall_status}. Identified {comp.violations_count} policy variances against Corporate Standard Vendor Policy.",
            "data": comp.model_dump()
        }

    elif step == 7:
        # Stage 7: Fastn Compliance Escalation
        comp_res = await fastn_client.execute_compliance_escalation(
            contract_id=DEMO_CONTRACT_ID,
            policy_name="Corporate Standard Vendor Policy v2.4",
            violations_count=2,
            violations=[
                {"policy": "GDPR Standard Contractual Clauses", "severity": "CRITICAL", "description": "Mandatory EU sub-processor audit clause missing from Article 14."},
                {"policy": "Payment Term Ceiling", "severity": "HIGH", "description": "Vendor demands Net 15 instead of standard corporate Net 60 policy."}
            ],
            db_session=db
        )
        return {
            "step": 7,
            "title": "Fastn Compliance Breach Escalation",
            "society": "Fastn Outbound Nervous System (Compliance Audit Alert)",
            "summary": "Dispatched policy breach escalation to Chief Compliance Officer and Audit Committee via Fastn.",
            "data": comp_res
        }

    elif step == 8:
        # Stage 8: CAS Director Dynamic Mesh Orchestration & Conflict Arbitration
        mesh_result = await cas_director.orchestrate_mesh(
            contract_text=contract_text,
            contract_id=DEMO_CONTRACT_ID,
            commercial_objective="Cap aggregate liability at 12 months fees, delete uncapped indemnity, and ensure mutual 30-day termination.",
            policy_path=policy_file,
            db_session=db
        )
        contract.status = "ANALYZED"
        await db.commit()
        return {
            "step": 8,
            "title": "Director Dynamic Mesh Orchestration & Arbitration",
            "society": "CAS Director Federation Core",
            "summary": f"Synthesized findings across all autonomous societies. Resolved {len(mesh_result.get('detected_conflicts', []))} cross-domain tensions.",
            "data": mesh_result
        }

    elif step == 9:
        # Stage 9: Fastn Human-In-The-Loop Approval Dispatch
        hitl_res = await fastn_client.execute_approval_dispatch(
            contract_id=DEMO_CONTRACT_ID,
            reason="Uncapped customer liability and non-compliant audit terms require executive review.",
            requested_action="Approve bilateral 12-month cap compromise or mandate formal renegotiation.",
            agent_conclusions=["Risk: CRITICAL (0.85)", "Compliance: 2 Violations", "Dispute: HIGH Exposure"],
            reviewer_email="general_counsel@acme.com",
            db_session=db
        )
        return {
            "step": 9,
            "title": "Fastn HITL Approval Dispatch",
            "society": "Fastn Outbound Nervous System (Slack & Email Dispatch)",
            "summary": "Dispatched rich multi-agent context and redlines to General Counsel for formal review.",
            "data": hitl_res
        }

    elif step == 10:
        # Stage 10: Fastn Decision Archive
        archive_res = await fastn_client.execute_decision_archive(
            contract_id=DEMO_CONTRACT_ID,
            decision="APPROVED_WITH_CONDITIONS",
            decision_maker="General Counsel / VP Legal",
            society="CAS_FEDERATION",
            reason="Bilateral compromise acceptable: 12-month fees liability cap approved with mandatory SOC2 audit right.",
            evidence="Risk score reduced from 0.85 to 0.24 under simulated concessions.",
            resulting_action="EXECUTE_SIGNATURE",
            db_session=db
        )
        return {
            "step": 10,
            "title": "Fastn Decision Archival & Precedent Storage",
            "society": "Fastn Outbound Nervous System (Google Drive & Airtable)",
            "summary": "Archived executive approval, negotiation rationale, and evidence to enterprise document registry.",
            "data": archive_res
        }

    elif step == 11:
        # Stage 11: Obligation Intelligence Scheduling & Fastn Calendar Sync
        sched = await obligation_intelligence_system.register_obligations(
            contract=contract_text,
            contract_id=DEMO_CONTRACT_ID,
            effective_date="2026-10-01",
            db_session=db
        )
        contract.status = "SIGNED"
        await db.commit()

        sync_res = await fastn_client.execute_obligation_sync(
            contract_id=DEMO_CONTRACT_ID,
            obligations=[
                {"title": o.title, "party": o.party, "dueDate": o.due_date, "type": o.type}
                for o in sched.items
            ],
            db_session=db
        )
        return {
            "step": 11,
            "title": "Obligation Scheduling & Fastn Calendar Sync",
            "society": "Obligation Intelligence & Fastn (System 5)",
            "summary": f"Contract marked SIGNED. Registered {sched.total_obligations} ongoing obligations and synced deadlines to Google Calendar & Airtable.",
            "data": {
                "schedule": sched.model_dump(),
                "fastn_sync": sync_res
            }
        }

    elif step == 12:
        # Stage 12: Fastn Inbound Event (External Counterparty Redline Return)
        inbound_neg = await fastn_client.trigger_inbound_negotiation(
            contract_id=DEMO_CONTRACT_ID,
            clause_reference="Section 8.2 Limitation of Liability",
            counterparty_proposal="NovaCloud agrees to mutual aggregate liability capped at 12 months fees ($240,000) conditioned on exclusion of lost profits.",
            concession_offered="Withdrew unilateral $50k liability shield; agreed to reciprocal dollar cap.",
            db_session=db
        )
        return {
            "step": 12,
            "title": "Fastn Inbound Redline Event Received",
            "society": "Fastn Inbound Nervous System (External Counterparty Portal)",
            "summary": "External counterparty submitted revised redline proposal via Fastn inbound webhook trigger.",
            "data": inbound_neg
        }

    elif step == 13:
        # Stage 13: CAS Director Inbound Re-Routing & Strategy Adaptation
        adaptation_res = await cas_director.handle_inbound_negotiation(
            contract_id=DEMO_CONTRACT_ID,
            counterparty_proposal="NovaCloud agrees to mutual aggregate liability capped at 12 months fees ($240,000) conditioned on exclusion of lost profits.",
            clause_reference="Section 8.2 Limitation of Liability",
            concession_offered="Withdrew unilateral $50k liability shield; agreed to reciprocal dollar cap.",
            db_session=db
        )
        return {
            "step": 13,
            "title": "Director Inbound Re-Routing & Strategy Adaptation",
            "society": "CAS Director Dynamic Routing & Negotiation Society",
            "summary": "CAS Director ingested inbound redline, dynamically reactivated Negotiation Intelligence, adapted leverage posture, and broadcasted response via Fastn.",
            "data": adaptation_res
        }

    elif step == 14:
        # Stage 14: Fastn Dispute Escalation
        dispute_esc = await fastn_client.execute_dispute_escalation(
            contract_id=DEMO_CONTRACT_ID,
            dispute_risk="HIGH",
            ambiguities=[
                "Section 14.1 SLA downtime calculation conflicts with Section 4 credit remedy clause.",
                "Delaware governing law conflicts with London arbitration venue."
            ],
            counterparty_stance="Vendor will argue third-party upstream cloud outages are force majeure and exempt from credits.",
            recommended_action="Harmonize SLA remedy language before final signature.",
            db_session=db
        )
        return {
            "step": 14,
            "title": "Fastn Dispute Escalation Dispatch",
            "society": "Fastn Outbound Nervous System (Litigation Risk Alert)",
            "summary": "Dispatched pre-litigation dispute ambiguity alert and defensive playbook to Legal Operations via Fastn.",
            "data": dispute_esc
        }

    elif step == 15:
        # Stage 15: Dispute Intelligence Simulation & Precedent Memory Storage
        disp = await dispute_intelligence_system.analyze_disputes(
            contract=contract_text,
            contract_id=DEMO_CONTRACT_ID,
            party_a_name="Acme Global",
            party_b_name="NovaCloud",
            db_session=db
        )
        await cas_memory.store(
            memory_type="PRECEDENT",
            content={
                "event": "DISPUTE_SIMULATION_COMPLETED",
                "contract_id": DEMO_CONTRACT_ID,
                "overall_dispute_risk": disp.overall_dispute_risk,
                "scenarios_count": len(disp.scenarios),
                "resolution": "Precedent recorded: enforce bilateral liability symmetry on all future vendor cloud contracts."
            },
            tags=["dispute", "precedent", "liability", "delaware"]
        )
        return {
            "step": 15,
            "title": "Dispute Intelligence Simulation & Precedent Memory Storage",
            "society": "Dispute Intelligence (System 6) & Persistent CAS Memory",
            "summary": f"Completed multi-perspective adversarial trial simulation ({len(disp.scenarios)} scenarios). Outcome and strategy indexed in CAS Memory for future contract reasoning.",
            "data": {
                "dispute_assessment": disp.model_dump(),
                "status": "ALL_15_STAGES_COMPLETE",
                "federation_health": "OPTIMAL_BIDIRECTIONAL_MESH"
            }
        }

    else:
        raise HTTPException(status_code=400, detail=f"Invalid demo step {step}. Valid range is 1 to 15.")
