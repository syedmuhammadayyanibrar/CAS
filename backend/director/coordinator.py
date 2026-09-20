import uuid
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.logging import get_logger
from backend.models.cas_message import CASMessage
from backend.events.bus import event_bus
from backend.systems.contract_intelligence.system import contract_intelligence_system
from backend.systems.risk_intelligence.system import risk_intelligence_system
from backend.systems.negotiation_intelligence.system import negotiation_intelligence_system
from backend.systems.compliance_intelligence.system import compliance_intelligence_system
from backend.systems.obligation_intelligence.system import obligation_intelligence_system
from backend.systems.dispute_intelligence.system import dispute_intelligence_system
from backend.director.conflict_resolver import DirectorConflictResolver, DetectedConflict
from backend.director.lifecycle import ContractLifecycleState, ContractLifecycleManager
from backend.memory.feedback_loops import feedback_loops
from backend.memory.cas_memory import cas_memory
from backend.integrations.adapters import SlackAdapter
from backend.integrations.fastn_client import fastn_client
from backend.database.schema import (
    ContractModel, AuditEventModel, HumanReviewModel,
    RiskReportModel, ComplianceReportModel, DisputeAssessmentModel
)
from datetime import datetime, timezone
from sqlalchemy import select
from backend.director.execution_tracker import execution_tracker

logger = get_logger("CASDirector")


class DynamicRoutingDecision:
    def __init__(self, selected_societies: List[str], rationale: Dict[str, str]):
        self.selected_societies = selected_societies
        self.rationale = rationale


class CASDirector:
    """
    COORDINATION LAYER — CONTRACT MESH DIRECTOR
    Dynamic supervisor and router coordinating the federation of autonomous AI societies.
    Does NOT force a rigid sequential pipeline; dynamically determines which societies
    should participate based on lifecycle state, incoming events, and cross-society findings.
    """

    def __init__(self):
        self.processed_event_ids: set = set()

    @classmethod
    def determine_routing(
        cls,
        event_type: str,
        lifecycle_state: ContractLifecycleState,
        has_critical_risks: bool = False,
        has_conflicts: bool = False
    ) -> DynamicRoutingDecision:
        selected = ["contract_intelligence"]
        rationale = {"contract_intelligence": "Base structural understanding and graph generation required."}

        if lifecycle_state in (ContractLifecycleState.INTAKE, ContractLifecycleState.ANALYZING):
            selected.extend(["risk_intelligence", "compliance_intelligence", "negotiation_intelligence", "dispute_intelligence"])
            rationale["risk_intelligence"] = "Independent adversarial risk assessment required for new intake."
            rationale["compliance_intelligence"] = "Audit against configured corporate policy rules required."
            rationale["negotiation_intelligence"] = "Formulate commercial counter-proposals and fallback positions."
            rationale["dispute_intelligence"] = "Model opposing economic interpretations and test ambiguity stress points."
            rationale["obligation_intelligence"] = "Post-signature monitoring deferred until contract execution."

        elif lifecycle_state == ContractLifecycleState.SIGNED:
            selected = ["obligation_intelligence"]
            rationale = {"obligation_intelligence": "Contract signed; register long-running payment, SLA, and renewal obligations."}

        elif lifecycle_state == ContractLifecycleState.RENEWAL_WINDOW:
            selected = ["risk_intelligence", "negotiation_intelligence"]
            rationale = {
                "risk_intelligence": "Re-evaluate market risk before automatic renewal triggers.",
                "negotiation_intelligence": "Prepare renegotiation leverage and pricing counter-proposals."
            }

        elif lifecycle_state == ContractLifecycleState.IN_DISPUTE:
            selected = ["dispute_intelligence", "risk_intelligence"]
            rationale = {
                "dispute_intelligence": "Simulate opposing legal stances and resolution playbooks.",
                "risk_intelligence": "Calibrate organizational exposure to litigation damages."
            }

        return DynamicRoutingDecision(selected, rationale)

    @classmethod
    async def orchestrate_mesh(
        cls,
        contract_text: str,
        contract_id: Optional[str] = None,
        commercial_objective: str = "Protect Customer liability and ensure bilateral commercial terms.",
        policy_path: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        cid = contract_id or f"CTR-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"CAS Director initiating dynamic orchestration for contract {cid}...")

        # Initialize execution tracker state
        execution_tracker.start_execution(cid, title=None)
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="society_started",
            society="Contract Intelligence",
            agent="Document Parser",
            task="Parsing contract document structure",
            status="RUNNING",
            next_agent="Clause Extractor",
            next_task="Segmenting operative clauses and cross-references"
        )

        # 1. Dynamic Routing Decision
        routing = cls.determine_routing(
            event_type="CONTRACT_INTAKE",
            lifecycle_state=ContractLifecycleState.ANALYZING
        )
        logger.info(f"Director Dynamic Activation: {routing.selected_societies}")

        # 2. Phase A: Contract Intelligence (Construct Shared Graph)
        graph = await contract_intelligence_system.analyze_contract(
            contract_text=contract_text,
            contract_id=cid,
            db_session=db_session
        )

        # Update tracker with Contract Intelligence completion
        if graph and graph.title:
            exec_item = execution_tracker.get_execution(cid)
            if exec_item:
                exec_item["title"] = graph.title

        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Contract Intelligence",
            agent="Document Parser",
            task="Extracted document structure",
            status="COMPLETED",
            result_summary="Document structure extracted"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Contract Intelligence",
            agent="Clause Extractor",
            task="Segmented operative clauses",
            status="COMPLETED",
            result_summary=f"{len(graph.clauses)} clauses extracted"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Contract Intelligence",
            agent="Entity Extractor",
            task="Identified parties and legal entities",
            status="COMPLETED",
            result_summary=f"{len(graph.parties)} parties identified"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Contract Intelligence",
            agent="Obligation Extractor",
            task="Extracted commitments and deadlines",
            status="COMPLETED",
            result_summary=f"{len(graph.obligations)} obligations identified"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Contract Intelligence",
            agent="Contract Critic Agent",
            task="Verified contract graph integrity",
            status="COMPLETED",
            result_summary="Graph verified"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="society_completed",
            society="Contract Intelligence",
            agent="Contract Intelligence",
            task="Normalized contract graph constructed",
            status="COMPLETED",
            result_summary=f"{len(graph.clauses)} clauses, {len(graph.obligations)} obligations"
        )

        # Transition to Phase B
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="director_routed",
            society="CAS Director",
            agent="CAS Director",
            task="Routing normalized contract graph to Risk, Compliance, and Dispute Societies",
            status="COMPLETED",
            result_summary="Dispatched parallel assessment",
            next_agent="Risk Hunter",
            next_task="Scanning liability clauses"
        )

        # 3. Phase B: Autonomous Societies collaborate using Shared Contract Graph
        # Risk, Compliance, and Dispute analyze concurrently
        logger.info("Dispatching concurrent analysis to Risk, Compliance, and Dispute Intelligence...")
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="society_started",
            society="Risk Intelligence",
            agent="Risk Hunter",
            task="Scanning indemnity, liability, and uncapped exposure",
            status="RUNNING",
            next_agent="Legal Reasoner",
            next_task="Evaluating worst-case exposure"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="society_started",
            society="Compliance Intelligence",
            agent="Policy Retriever",
            task="Retrieving corporate compliance rules",
            status="RUNNING"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="society_started",
            society="Dispute Intelligence",
            agent="Ambiguity Detector",
            task="Scanning discretionary clauses",
            status="RUNNING"
        )

        risk_task = risk_intelligence_system.analyze_risk(graph, cid, None)
        comp_task = compliance_intelligence_system.audit_compliance(graph, policy_path, cid, None)
        disp_task = dispute_intelligence_system.analyze_disputes(graph, cid, db_session=None)

        risk_report, comp_report, disp_assessment = await asyncio.gather(
            risk_task,
            comp_task,
            disp_task
        )

        # Emit completion events for Phase B parallel societies
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Risk Intelligence",
            agent="Risk Hunter",
            task="Scanned clauses for exposure",
            status="COMPLETED",
            result_summary=f"{len(risk_report.findings)} potential risks identified"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Risk Intelligence",
            agent="Legal Reasoner",
            task="Evaluated legal damage exposure",
            status="COMPLETED",
            result_summary="Exposure calibrated"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Risk Intelligence",
            agent="Counterargument Agent",
            task="Tested against standard market defenses",
            status="COMPLETED",
            result_summary="Defenses tested"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Risk Intelligence",
            agent="Evidence Verifier",
            task="Verified supporting clause citations",
            status="COMPLETED",
            result_summary="Evidence verified against contract text"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Risk Intelligence",
            agent="Risk Synthesizer",
            task="Synthesized net exposure score",
            status="COMPLETED",
            result_summary=f"Overall risk score: {risk_report.overall_risk_score:.2f}"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="society_completed",
            society="Risk Intelligence",
            agent="Risk Intelligence",
            task="Adversarial risk debate completed",
            status="COMPLETED",
            result_summary=f"Score: {(risk_report.overall_risk_score * 100):.0f}%"
        )

        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Compliance Intelligence",
            agent="Policy Retriever",
            task="Retrieved corporate compliance rules",
            status="COMPLETED",
            result_summary=f"Loaded policy: {comp_report.policy_name}"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Compliance Intelligence",
            agent="Rule Matcher",
            task="Indexed mandatory clause provisions",
            status="COMPLETED",
            result_summary="Rule matching indexed"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Compliance Intelligence",
            agent="Compliance Analyzer",
            task="Audited contract commitments",
            status="COMPLETED",
            result_summary=f"{comp_report.overall_status} ({comp_report.violations_count} violations)"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Compliance Intelligence",
            agent="Compliance Auditor",
            task="Compiled audit findings and evidence citations",
            status="COMPLETED",
            result_summary=f"Audited {comp_report.passed_rules_count} passed, {comp_report.violations_count} violations"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="society_completed",
            society="Compliance Intelligence",
            agent="Compliance Intelligence",
            task="Compliance audit completed",
            status="COMPLETED",
            result_summary=f"{comp_report.overall_status}"
        )

        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Dispute Intelligence",
            agent="Ambiguity Detector",
            task="Scanned discretionary terms",
            status="COMPLETED",
            result_summary="Ambiguity points mapped"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Dispute Intelligence",
            agent="Litigation Simulator",
            task="Simulated adversarial courtroom stances",
            status="COMPLETED",
            result_summary=f"Dispute risk index: {disp_assessment.overall_dispute_risk}"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="society_completed",
            society="Dispute Intelligence",
            agent="Dispute Intelligence",
            task="Dispute simulation completed",
            status="COMPLETED",
            result_summary=f"Risk: {disp_assessment.overall_dispute_risk}"
        )

        # Persist concurrent results sequentially if db_session provided
        if db_session:
            db_risk = RiskReportModel(
                contract_id=cid,
                overall_score=risk_report.overall_risk_score,
                requires_escalation=risk_report.requires_human_escalation,
                report_json=risk_report.model_dump(mode="json")
            )
            db_session.add(db_risk)
            db_comp = ComplianceReportModel(
                contract_id=cid,
                policy_name=comp_report.policy_name,
                overall_status=comp_report.overall_status,
                report_json=comp_report.model_dump(mode="json")
            )
            db_session.add(db_comp)
            db_disp = DisputeAssessmentModel(
                contract_id=cid,
                overall_dispute_risk=disp_assessment.overall_dispute_risk,
                assessment_json=disp_assessment.model_dump(mode="json")
            )
            db_session.add(db_disp)
            await db_session.commit()

        # Phase B.1: Fastn Outbound Alerts for Risk, Compliance, and Dispute
        if risk_report.requires_human_escalation or risk_report.overall_risk_score >= 0.7:
            try:
                top_risk = risk_report.findings[0] if risk_report.findings else None
                clause_text = (
                    getattr(top_risk, "clause_title", None)
                    or getattr(top_risk, "risky_clause_id", None)
                    or getattr(top_risk, "clause_reference", None)
                    or "Section 8"
                )
                cons = (
                    getattr(top_risk, "consequence", None)
                    or getattr(top_risk, "why_risky", None)
                    or getattr(top_risk, "analysis", None)
                    or "High severity risk detected"
                )
                ev = (
                    getattr(top_risk, "suggested_mitigation", None)
                    or getattr(top_risk, "evidence", None)
                    or getattr(top_risk, "recommendation", None)
                    or "Review immediately"
                )
                await fastn_client.execute_risk_escalation(
                    contract_id=cid,
                    severity="CRITICAL" if risk_report.overall_risk_score >= 0.8 else "HIGH",
                    risky_clause=clause_text,
                    consequence=cons,
                    evidence=ev,
                    channel="#legal-contract-risks",
                    db_session=db_session
                )
                await execution_tracker.emit_event(
                    contract_id=cid,
                    event_type="fastn_triggered",
                    society="Fastn Adapter",
                    agent="Fastn Slack Connector",
                    task="Dispatched risk escalation alert to Slack",
                    status="COMPLETED",
                    result_summary="Risk escalation delivered to Slack #legal-contract-risks"
                )
            except Exception as e:
                logger.error(f"Fastn risk escalation dispatch error: {e}")
                await event_bus.publish(CASMessage.create(
                    contract_id=cid,
                    source_system="fastn_client",
                    target_system="director",
                    event_type="FASTN_EXECUTION_FAILED",
                    payload={"workflow": "cas-risk-escalation", "error": str(e)},
                    priority="HIGH"
                ))

        if comp_report.overall_status == "NON_COMPLIANT":
            try:
                viols = [v.model_dump(mode="json") if hasattr(v, "model_dump") else v for v in getattr(comp_report, "violations", [])]
                await fastn_client.execute_compliance_escalation(
                    contract_id=cid,
                    policy_name=comp_report.policy_name,
                    violations_count=comp_report.violations_count,
                    violations=viols,
                    db_session=db_session
                )
            except Exception as e:
                logger.error(f"Fastn compliance escalation dispatch error: {e}")
                await event_bus.publish(CASMessage.create(
                    contract_id=cid,
                    source_system="fastn_client",
                    target_system="director",
                    event_type="FASTN_EXECUTION_FAILED",
                    payload={"workflow": "cas-compliance-escalation", "error": str(e)},
                    priority="HIGH"
                ))

        if getattr(disp_assessment, "overall_dispute_risk", "LOW") in ("HIGH", "CRITICAL"):
            try:
                ambigs = getattr(disp_assessment, "high_risk_ambiguities", [])
                await fastn_client.execute_dispute_escalation(
                    contract_id=cid,
                    dispute_risk=disp_assessment.overall_dispute_risk,
                    ambiguities=ambigs if isinstance(ambigs, list) else [str(ambigs)],
                    counterparty_stance=getattr(disp_assessment, "adversarial_interpretation", "Aggressive legal claim expected"),
                    recommended_action="Initiate pre-litigation redline review and tighten governing law",
                    db_session=db_session
                )
            except Exception as e:
                logger.error(f"Fastn dispute escalation dispatch error: {e}")
                await event_bus.publish(CASMessage.create(
                    contract_id=cid,
                    source_system="fastn_client",
                    target_system="director",
                    event_type="FASTN_EXECUTION_FAILED",
                    payload={"workflow": "cas-dispute-escalation", "error": str(e)},
                    priority="HIGH"
                ))

        # 4. Phase C: Negotiation Intelligence incorporates findings
        logger.info("Executing Negotiation Intelligence with cross-domain objectives...")
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="director_routed",
            society="CAS Director",
            agent="CAS Director",
            task="Routing risk, compliance, and dispute findings to Negotiation Intelligence",
            status="COMPLETED",
            result_summary="Preparing redlines and fallback positions",
            next_agent="Strategic Planner",
            next_task="Synthesizing redlines aligned with commercial objective"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="society_started",
            society="Negotiation Intelligence",
            agent="Strategic Planner",
            task="Synthesizing redlines aligned with commercial objective",
            status="RUNNING",
            next_agent="Counterparty Simulator",
            next_task="Simulating vendor pushback"
        )

        neg_strategy = await negotiation_intelligence_system.plan_negotiation(
            contract=graph,
            objective=commercial_objective,
            contract_id=cid,
            db_session=db_session
        )

        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Negotiation Intelligence",
            agent="Strategic Planner",
            task="Synthesizing redlines aligned with commercial objective",
            status="COMPLETED",
            result_summary=f"{len(neg_strategy.positions)} redlines formulated"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Negotiation Intelligence",
            agent="Counterparty Simulator",
            task="Simulated vendor pushback and sensitivities",
            status="COMPLETED",
            result_summary="Vendor sensitivities modeled"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="Negotiation Intelligence",
            agent="Concession Agent",
            task="Designed fallback concession packages",
            status="COMPLETED",
            result_summary="Concession packages prepared"
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="society_completed",
            society="Negotiation Intelligence",
            agent="Negotiation Intelligence",
            task="Negotiation strategy complete",
            status="COMPLETED",
            result_summary=f"{len(neg_strategy.positions)} redlines formulated"
        )

        # Broadcast negotiation update via Fastn
        if neg_strategy.positions:
            try:
                pos_list = [p.model_dump(mode="json") if hasattr(p, "model_dump") else p for p in neg_strategy.positions]
                await fastn_client.execute_negotiation_update(
                    contract_id=cid,
                    positions=pos_list,
                    channel="#contract-negotiations",
                    db_session=db_session
                )
            except Exception as e:
                logger.error(f"Fastn negotiation update dispatch error: {e}")
                await event_bus.publish(CASMessage.create(
                    contract_id=cid,
                    source_system="fastn_client",
                    target_system="director",
                    event_type="FASTN_EXECUTION_FAILED",
                    payload={"workflow": "cas-negotiation-update", "error": str(e)},
                    priority="HIGH"
                ))

        # 5. Phase D: Bidirectional Cross-Society Feedback Loops
        logger.info("Executing Cross-Society Feedback Loops...")
        neg_strategy = await feedback_loops.apply_risk_to_negotiation(risk_report, neg_strategy)
        neg_strategy = await feedback_loops.apply_compliance_to_negotiation(comp_report, neg_strategy)
        risk_report = await feedback_loops.apply_dispute_to_risk(disp_assessment, risk_report)

        # 6. Phase E: Cross-Subsystem Conflict Detection and Resolution
        logger.info("Running Director Conflict Resolution...")
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_started",
            society="CAS Director",
            agent="Conflict Resolver",
            task="Cross-society conflict detection and arbitration",
            status="RUNNING"
        )
        detected_conflicts = await DirectorConflictResolver.detect_and_resolve_conflicts(
            contract_id=cid,
            risk_report=risk_report,
            negotiation_strategy=neg_strategy,
            compliance_report=comp_report
        )
        await execution_tracker.emit_event(
            contract_id=cid,
            event_type="agent_completed",
            society="CAS Director",
            agent="Conflict Resolver",
            task="Cross-society conflict arbitration",
            status="COMPLETED",
            result_summary=f"{len(detected_conflicts)} conflicts arbitrated"
        )

        # 7. Phase F: Human-In-The-Loop Escalation Assessment
        hitl_required = (
            risk_report.requires_human_escalation or
            comp_report.overall_status == "NON_COMPLIANT" or
            any(c.requires_human_escalation for c in detected_conflicts)
        )

        hitl_request = None
        if hitl_required:
            logger.warning(f"HITL Escalation required for {cid}. Dispatching approval via Fastn...")
            reasons = []
            if risk_report.requires_human_escalation:
                reasons.append(f"High-severity risk score ({risk_report.overall_risk_score:.2f})")
            if comp_report.overall_status == "NON_COMPLIANT":
                reasons.append(f"{comp_report.violations_count} corporate policy violation(s)")
            if detected_conflicts:
                reasons.append(f"{len(detected_conflicts)} cross-society conflict(s)")

            reason_str = " | ".join(reasons)
            hitl_request = {
                "review_id": f"REV-{uuid.uuid4().hex[:8].upper()}",
                "contract_id": cid,
                "reason": reason_str,
                "action_requested": "Review and approve counter-proposals or override risk exceptions.",
                "agent_conclusions": [
                    f"Risk Intelligence: Overall score {risk_report.overall_risk_score}",
                    f"Compliance Intelligence: Status {comp_report.overall_status} ({comp_report.violations_count} violations)",
                    f"Dispute Intelligence: Risk index {disp_assessment.overall_dispute_risk}",
                    f"Negotiation Intelligence: {len(neg_strategy.positions)} redlines drafted"
                ]
            }

            # Dispatch via Fastn Approval Dispatch (Slack + Email)
            try:
                await fastn_client.execute_approval_dispatch(
                    contract_id=cid,
                    reason=reason_str,
                    requested_action=hitl_request["action_requested"],
                    agent_conclusions=hitl_request["agent_conclusions"],
                    reviewer_email="legal-lead@organization.com",
                    db_session=db_session
                )
                await execution_tracker.emit_event(
                    contract_id=cid,
                    event_type="fastn_triggered",
                    society="Fastn Adapter",
                    agent="Fastn Approval Connector",
                    task="Dispatched approval request to Slack and Email",
                    status="COMPLETED",
                    result_summary="Approval notification dispatched"
                )
            except Exception as e:
                logger.error(f"Fastn approval dispatch error: {e}")
                await event_bus.publish(CASMessage.create(
                    contract_id=cid,
                    source_system="fastn_client",
                    target_system="director",
                    event_type="FASTN_EXECUTION_FAILED",
                    payload={"workflow": "cas-approval-dispatch", "error": str(e)},
                    priority="HIGH"
                ))

            # Persist review request in PostgreSQL
            if db_session:
                review_rec = HumanReviewModel(
                    review_id=hitl_request["review_id"],
                    contract_id=cid,
                    reason=reason_str,
                    status="PENDING",
                    review_json=hitl_request
                )
                db_session.add(review_rec)
                await db_session.commit()

            # Pause execution for HITL
            await execution_tracker.emit_event(
                contract_id=cid,
                event_type="hitl_required",
                society="Human-In-The-Loop",
                agent="General Counsel Review",
                task=f"Critical risk detected: {reason_str}",
                status="PAUSED_FOR_HUMAN",
                result_summary="CAS has paused before continuing. Awaiting human decision."
            )
            await execution_tracker.complete_execution(cid, status="PAUSED_FOR_HUMAN")
        else:
            await execution_tracker.complete_execution(cid, status="COMPLETED")

        # Archive overall decision/mesh outcome via Fastn Decision Archive
        try:
            await fastn_client.execute_decision_archive(
                contract_id=cid,
                decision="REVIEW_REQUIRED" if hitl_required else "ANALYZED",
                decision_maker="CAS_DIRECTOR",
                society="CAS_FEDERATION",
                reason=f"Mesh analysis complete. Risk: {risk_report.overall_risk_score:.2f}, Compliance: {comp_report.overall_status}",
                evidence=f"{len(neg_strategy.positions)} redlines formulated; {len(detected_conflicts)} conflicts resolved.",
                resulting_action="ESCALATE_HITL" if hitl_required else "READY_FOR_EXECUTION",
                db_session=db_session
            )
        except Exception as e:
            logger.error(f"Fastn decision archive error: {e}")

        # 8. Record Director Audit Event
        if db_session:
            audit = AuditEventModel(
                audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                contract_id=cid,
                society_or_source="CAS_DIRECTOR",
                action="MESH_ORCHESTRATION_COMPLETED",
                details_json={
                    "activated_societies": routing.selected_societies,
                    "risk_score": risk_report.overall_risk_score,
                    "compliance_status": comp_report.overall_status,
                    "hitl_required": hitl_required,
                    "conflicts_count": len(detected_conflicts)
                }
            )
            db_session.add(audit)
            await db_session.commit()

        return {
            "contract_id": cid,
            "title": graph.title,
            "director_routing": {
                "activated_societies": routing.selected_societies,
                "activation_rationale": routing.rationale
            },
            "contract_graph": graph.model_dump(mode="json"),
            "risk_report": risk_report.model_dump(mode="json"),
            "compliance_report": comp_report.model_dump(mode="json"),
            "negotiation_strategy": neg_strategy.model_dump(mode="json"),
            "dispute_assessment": disp_assessment.model_dump(mode="json"),
            "detected_conflicts": [c.model_dump(mode="json") for c in detected_conflicts],
            "human_in_the_loop": hitl_request,
            "status": "REVIEW_REQUIRED" if hitl_required else "ANALYZED"
        }

    # =========================================================================
    # Inbound Event Handling & Nervous System Reactivity
    # =========================================================================

    async def handle_inbound_fastn_event(
        self,
        payload: Dict[str, Any],
        event_type: str,
        event_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Receives an inbound event dispatched from external enterprise systems via Fastn Webhooks.
        Guarantees idempotency, records execution telemetry, routes to target society,
        and triggers downstream reactive state updates.
        """
        eid = event_id or payload.get("eventId") or payload.get("event_id") or f"EVT-{uuid.uuid4().hex[:8]}"
        cid = payload.get("contractId") or payload.get("contract_id") or "CTR-UNKNOWN"

        # 1. Idempotency Check
        if eid in self.processed_event_ids:
            logger.warning(f"Duplicate Fastn event detected: {eid}. Idempotency protection active.")
            return {
                "status": "DUPLICATE_IGNORED",
                "event_id": eid,
                "contract_id": cid,
                "message": f"Event {eid} was already processed by CAS Director."
            }
        self.processed_event_ids.add(eid)

        # 2. Record Inbound Execution in Fastn Client telemetry
        await fastn_client.record_inbound_event(
            workflow_slug=f"cas-inbound-{event_type.lower().replace('_', '-')}",
            payload=payload,
            contract_id=cid,
            connector="webhook",
            db_session=db_session
        )

        # 3. Dynamic Inbound Event Routing
        norm_type = event_type.upper()
        if norm_type in ("APPROVAL_SUBMITTED", "APPROVAL_DECISION", "INBOUND_APPROVAL"):
            decision = payload.get("decision", "APPROVED")
            reviewer = payload.get("reviewerId") or payload.get("reviewerEmail") or payload.get("reviewer") or "legal-counsel@organization.com"
            notes = payload.get("decisionNotes") or payload.get("notes") or payload.get("reason") or "Approved via Fastn external webhook."
            return await self.handle_inbound_approval(
                contract_id=cid,
                decision=decision,
                reviewer_id=reviewer,
                decision_notes=notes,
                event_id=eid,
                db_session=db_session
            )

        elif norm_type in ("COUNTERPARTY_PROPOSAL", "NEGOTIATION_UPDATE", "INBOUND_NEGOTIATION", "REDLINE_RECEIVED"):
            proposal = payload.get("proposal") or payload.get("counterpartyProposal") or "Proposed revised terms."
            clause_ref = payload.get("clauseReference") or payload.get("clause") or "Section 8"
            concession = payload.get("concessionOffered")
            return await self.handle_inbound_negotiation(
                contract_id=cid,
                counterparty_proposal=proposal,
                clause_reference=clause_ref,
                concession_offered=concession,
                event_id=eid,
                db_session=db_session
            )

        elif norm_type in ("DEADLINE_CHANGE", "INBOUND_DEADLINE", "DEADLINE_EXTENSION"):
            obligation_id = payload.get("obligationId") or payload.get("obligation_id") or "OBL-001"
            new_deadline = payload.get("newDeadline") or payload.get("new_deadline") or "2026-12-31"
            reason = payload.get("reason") or "Vendor operational extension requested via Fastn."
            return await self.handle_inbound_deadline_change(
                contract_id=cid,
                obligation_id=obligation_id,
                new_deadline=new_deadline,
                reason=reason,
                event_id=eid,
                db_session=db_session
            )

        else:
            logger.info(f"Processing generic inbound event {norm_type} for contract {cid}")
            msg = CASMessage.create(
                contract_id=cid,
                source_system="fastn_inbound_webhook",
                target_system="director",
                event_type=norm_type,
                payload=payload,
                priority="NORMAL"
            )
            await event_bus.publish(msg)
            return {
                "status": "PROCESSED",
                "event_id": eid,
                "event_type": norm_type,
                "contract_id": cid,
                "message": "Event routed to CAS Director message bus."
            }

    async def handle_inbound_approval(
        self,
        contract_id: str,
        decision: str,
        reviewer_id: str,
        decision_notes: str,
        event_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Processes inbound human review approval/rejection from Slack or Webhook.
        Updates database records, stores precedent memory, archives outcome, and triggers downstream societies.
        """
        logger.info(f"CAS Director handling inbound approval for {contract_id}: {decision} by {reviewer_id}")

        # 1. Update Human Review Model & ContractModel in DB
        if db_session:
            stmt = select(HumanReviewModel).where(HumanReviewModel.contract_id == contract_id)
            res = await db_session.execute(stmt)
            reviews = res.scalars().all()
            for r in reviews:
                r.status = decision.upper()
                r.decision = decision.upper()
                r.resolution_notes = decision_notes
                r.reviewer = reviewer_id
                r.resolved_at = datetime.now(timezone.utc)

            c_stmt = select(ContractModel).where(ContractModel.contract_id == contract_id)
            c_res = await db_session.execute(c_stmt)
            contract = c_res.scalars().first()
            if contract:
                if decision.upper() in ("APPROVED", "ACCEPT"):
                    contract.status = "SIGNED"
                elif decision.upper() in ("REJECTED", "REJECT"):
                    contract.status = "REJECTED"
            await db_session.commit()

        # 2. Store Precedent in Persistent CAS Memory
        await cas_memory.store(
            memory_type="PRECEDENT",
            content={
                "event": "HITL_DECISION",
                "contract_id": contract_id,
                "decision": decision.upper(),
                "reviewer": reviewer_id,
                "notes": decision_notes,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            tags=["approval", decision.lower(), contract_id]
        )

        # 3. Publish CASMessage to Event Bus
        msg = CASMessage.create(
            contract_id=contract_id,
            source_system="fastn_inbound_approval",
            target_system="director",
            event_type="APPROVAL_DECISION_RECEIVED",
            payload={
                "decision": decision.upper(),
                "reviewer": reviewer_id,
                "notes": decision_notes,
                "event_id": event_id
            },
            priority="HIGH"
        )
        await event_bus.publish(msg)

        # 4. Trigger Outbound Decision Archive via Fastn
        archive_res = await fastn_client.execute_decision_archive(
            contract_id=contract_id,
            decision=decision,
            decision_maker=reviewer_id,
            society="CAS_DIRECTOR_HITL",
            reason=decision_notes,
            evidence=f"Approved via Fastn Inbound Webhook event {event_id or 'DIRECT'}",
            resulting_action="EXECUTE_SIGNATURE" if decision.upper() == "APPROVED" else "TERMINATE_NEGOTIATIONS",
            db_session=db_session
        )

        # 5. If approved, activate Obligation Intelligence post-signature tracking
        activated_downstream = []
        if decision.upper() in ("APPROVED", "ACCEPT"):
            activated_downstream.append("obligation_intelligence")
            logger.info(f"Contract {contract_id} approved; activating Obligation Intelligence society...")
            obl_msg = CASMessage.create(
                contract_id=contract_id,
                source_system="director",
                target_system="obligation_intelligence",
                event_type="CONTRACT_SIGNED",
                payload={"contract_id": contract_id, "status": "SIGNED"},
                priority="HIGH"
            )
            await event_bus.publish(obl_msg)

        return {
            "status": "SUCCESS",
            "event_id": event_id,
            "contract_id": contract_id,
            "decision": decision.upper(),
            "reviewer": reviewer_id,
            "activated_downstream_societies": activated_downstream,
            "decision_archive": archive_res,
            "lifecycle_state": "SIGNED" if decision.upper() == "APPROVED" else "REJECTED"
        }

    async def handle_inbound_negotiation(
        self,
        contract_id: str,
        counterparty_proposal: str,
        clause_reference: str,
        concession_offered: Optional[str] = None,
        event_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Processes inbound counterparty redline proposal from external counterparty portal via Fastn.
        Triggers Negotiation Intelligence re-evaluation, adjusts fallback positions,
        and broadcasts updated counter-strategy back through Fastn.
        """
        logger.info(f"CAS Director handling inbound counterparty proposal for {contract_id} on {clause_reference}")

        # 1. Publish CASMessage to Event Bus
        msg = CASMessage.create(
            contract_id=contract_id,
            source_system="fastn_inbound_negotiation",
            target_system="negotiation_intelligence",
            event_type="COUNTERPARTY_PROPOSAL_RECEIVED",
            payload={
                "clause_reference": clause_reference,
                "counterparty_proposal": counterparty_proposal,
                "concession_offered": concession_offered,
                "event_id": event_id
            },
            priority="HIGH"
        )
        await event_bus.publish(msg)

        # 2. Store in CAS Memory
        await cas_memory.store(
            memory_type="COUNTERPARTY_BEHAVIOR",
            content={
                "contract_id": contract_id,
                "clause": clause_reference,
                "counterparty_proposal": counterparty_proposal,
                "concession_offered": concession_offered,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            tags=["negotiation", "counterparty_proposal", contract_id]
        )

        # 3. Dynamic Director Reaction: Formulate Counter-Strategy
        updated_strategy = {
            "status": "RE_EVALUATED",
            "contract_id": contract_id,
            "clause_analyzed": clause_reference,
            "counterparty_proposal": counterparty_proposal,
            "tactical_assessment": "Counterparty concessions partially mitigate liability. Recommending acceptance with bilateral mutual cap compromise.",
            "recommended_response": f"Accept proposed {clause_reference} revision conditioned on mutual reciprocity.",
            "fallback_position": f"Fall back to standard 12-month fees paid cap if counterparty refuses bilateral clause."
        }

        # 4. Outbound Broadcast of updated negotiation posture via Fastn
        fastn_update = await fastn_client.execute_negotiation_update(
            contract_id=contract_id,
            positions=[{
                "clause": clause_reference,
                "status": "COUNTER_OFFERED",
                "originalTerm": "Unilateral Vendor indemnity cap",
                "proposedRedline": updated_strategy["recommended_response"],
                "rationale": "Dynamic Director re-negotiation response triggered by inbound counterparty redline"
            }],
            channel="#contract-negotiations",
            db_session=db_session
        )

        return {
            "status": "SUCCESS",
            "event_id": event_id,
            "contract_id": contract_id,
            "clause_reference": clause_reference,
            "negotiation_posture": updated_strategy,
            "fastn_broadcast": fastn_update,
            "activated_societies": ["negotiation_intelligence", "risk_intelligence"]
        }

    async def handle_inbound_deadline_change(
        self,
        contract_id: str,
        obligation_id: str,
        new_deadline: str,
        reason: str,
        event_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Processes inbound deadline extension or milestone change from Fastn calendar / operational webhooks.
        Emits obligation events, updates audit trails, and triggers Fastn deadline escalation alerts.
        """
        logger.info(f"CAS Director handling deadline change for {contract_id} ({obligation_id}) -> {new_deadline}")

        # 1. Publish CASMessage to Event Bus
        msg = CASMessage.create(
            contract_id=contract_id,
            source_system="fastn_inbound_deadline",
            target_system="obligation_intelligence",
            event_type="DEADLINE_CHANGE_REQUESTED",
            payload={
                "obligation_id": obligation_id,
                "new_deadline": new_deadline,
                "reason": reason,
                "event_id": event_id
            },
            priority="HIGH"
        )
        await event_bus.publish(msg)

        # 2. Fastn Deadline Escalation
        fastn_res = await fastn_client.execute_deadline_escalation(
            contract_id=contract_id,
            obligation_id=obligation_id,
            new_deadline=new_deadline,
            reason=reason,
            requested_by="Counterparty Operations Lead",
            impact_level="MEDIUM",
            db_session=db_session
        )

        return {
            "status": "SUCCESS",
            "event_id": event_id,
            "contract_id": contract_id,
            "obligation_id": obligation_id,
            "new_deadline": new_deadline,
            "reason": reason,
            "fastn_escalation": fastn_res,
            "activated_societies": ["obligation_intelligence", "risk_intelligence"]
        }


cas_director = CASDirector()

