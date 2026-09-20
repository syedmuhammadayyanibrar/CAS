import uuid
from typing import Optional, Union, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.logging import get_logger
from backend.models.findings import ComplianceReport
from backend.models.graph import ContractGraph
from backend.models.cas_message import CASMessage
from backend.events.bus import event_bus
from backend.systems.compliance_intelligence.policy_retriever import PolicyRetriever
from backend.systems.compliance_intelligence.rules_engine import RuleMatcher
from backend.systems.compliance_intelligence.analyzer import ComplianceAnalyzer
from backend.systems.compliance_intelligence.conflict_detector import ComplianceConflictDetector
from backend.systems.compliance_intelligence.evidence_agent import ComplianceEvidenceAgent
from backend.systems.compliance_intelligence.critic import ComplianceCritic
from backend.systems.compliance_intelligence.auditor import FinalComplianceAuditor
from backend.database.schema import ComplianceReportModel

logger = get_logger("ComplianceIntelligenceSystem")


class ComplianceIntelligenceSystem:
    """
    SYSTEM 4 — COMPLIANCE INTELLIGENCE
    Architecture: Retrieval + Rules + Verification Architecture
    Determines whether contracts comply with organizational policies and configured regulatory requirements.
    Deterministic rules index explicit fields; Gemini performs all contextual interpretation and reasoning.
    Can be run completely independently.
    """

    @classmethod
    async def audit_compliance(
        cls,
        contract: Union[str, ContractGraph],
        policy_path: Optional[str] = None,
        contract_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> ComplianceReport:
        if isinstance(contract, ContractGraph):
            cid = contract.contract_id
            contract_text = "\n\n".join([f"{c.section_number} {c.title}:\n{c.text}" for c in contract.clauses])
        else:
            cid = contract_id or f"CTR-{uuid.uuid4().hex[:8].upper()}"
            contract_text = contract

        logger.info(f"Initiating Compliance Audit for {cid}...")

        # Step 1: Policy Retrieval
        policy_data = PolicyRetriever.load_policy(policy_path)
        policy_name = policy_data.get("policy_name", "Corporate Compliance Policy")
        policy_rules = policy_data.get("rules", [])

        # Step 2: Deterministic Rule Matcher (Preliminary indexing of explicit fields)
        candidate_matches = RuleMatcher.match_explicit_fields(contract_text, policy_rules)
        # If no explicit keyword matches, provide all rules for contextual evaluation
        if not candidate_matches:
            from backend.systems.compliance_intelligence.rules_engine import CandidateRuleMatch
            candidate_matches = [
                CandidateRuleMatch(rule=r, matched_clause_text=contract_text, match_reason="Full contract evaluation")
                for r in policy_rules
            ]

        # Step 3: Contextual Compliance Analyzer (Gemini primary decision-maker)
        evaluations = await ComplianceAnalyzer.analyze_compliance(contract_text, policy_name, candidate_matches)

        # Step 4: Internal Clause Conflict Detector (Gemini)
        conflicts = await ComplianceConflictDetector.detect_conflicts(contract_text)

        # Step 5: Evidence Verifier
        evidence_lookup = await ComplianceEvidenceAgent.verify_compliance_evidence(evaluations, contract_text)

        # Step 6: Compliance Critic
        critique = await ComplianceCritic.review_audit(evaluations, policy_name)

        # Step 7: Final Auditor compiles report
        report = FinalComplianceAuditor.compile_report(
            contract_id=cid,
            policy_name=policy_name,
            evaluations=evaluations,
            evidence_lookup=evidence_lookup,
            conflicts=conflicts,
            critique=critique
        )

        # Step 8: Persist to PostgreSQL
        if db_session:
            db_rep = ComplianceReportModel(
                contract_id=cid,
                policy_name=policy_name,
                overall_status=report.overall_status,
                report_json=report.model_dump(mode="json")
            )
            db_session.add(db_rep)
            await db_session.commit()
            logger.info(f"Persisted Compliance Report for {cid} in PostgreSQL.")

        # Step 9: Standardized CASMessage publication
        message = CASMessage.create(
            contract_id=cid,
            source_system="compliance_intelligence",
            target_system="director",
            event_type="COMPLIANCE_CHECKED",
            payload={
                "contract_id": cid,
                "policy_name": policy_name,
                "overall_status": report.overall_status,
                "violations_count": report.violations_count,
                "passed_count": report.passed_rules_count,
                "ambiguities_count": report.ambiguities_count,
                "top_violations": [f.model_dump(mode="json") for f in report.findings if f.compliance_status == "VIOLATION"]
            },
            evidence_refs=[f.rule_id for f in report.findings if f.compliance_status == "VIOLATION"],
            confidence=critique.confidence_calibration,
            priority="HIGH" if report.violations_count > 0 else "LOW"
        )
        await event_bus.publish(message)

        return report


compliance_intelligence_system = ComplianceIntelligenceSystem()
