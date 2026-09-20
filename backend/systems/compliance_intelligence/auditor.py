from typing import List, Dict
from backend.systems.compliance_intelligence.analyzer import EvaluatedRuleDTO
from backend.systems.compliance_intelligence.evidence_agent import VerifiedComplianceEvidenceDTO
from backend.systems.compliance_intelligence.conflict_detector import ClauseConflictDTO
from backend.systems.compliance_intelligence.critic import ComplianceCritiqueResponse
from backend.models.findings import ComplianceFinding, ComplianceReport
from backend.core.logging import get_logger

logger = get_logger("FinalComplianceAuditor")


class FinalComplianceAuditor:
    """
    Final Auditor agent compiling the official ComplianceReport.
    """

    @staticmethod
    def compile_report(
        contract_id: str,
        policy_name: str,
        evaluations: List[EvaluatedRuleDTO],
        evidence_lookup: Dict[str, VerifiedComplianceEvidenceDTO],
        conflicts: List[ClauseConflictDTO],
        critique: ComplianceCritiqueResponse
    ) -> ComplianceReport:
        findings: List[ComplianceFinding] = []
        passed = 0
        violations = 0
        ambiguities = 0

        for e in evaluations:
            ev = evidence_lookup.get(e.rule_id)
            ev_text = ev.citation_text if (ev and ev.citation_text) else e.contract_evidence

            status = e.compliance_status.upper()
            if status == "COMPLIANT":
                passed += 1
            elif status == "VIOLATION":
                violations += 1
            elif status == "AMBIGUOUS":
                ambiguities += 1

            findings.append(ComplianceFinding(
                rule_id=e.rule_id,
                rule_name=e.rule_name,
                requirement=e.requirement,
                contract_evidence=ev_text,
                compliance_status=status,
                reason=e.reason,
                confidence=e.confidence,
                source_policy=policy_name,
                recommended_action=e.recommended_action
            ))

        # Determine overall status
        if violations > 0:
            overall = "NON_COMPLIANT"
        elif ambiguities > 0:
            overall = "REQUIRES_REVIEW"
        else:
            overall = "COMPLIANT"

        conflict_note = f" Detected {len(conflicts)} internal contract clause conflict(s)." if conflicts else ""
        auditor_notes = f"{critique.critique_notes}{conflict_note}"

        report = ComplianceReport(
            contract_id=contract_id,
            policy_name=policy_name,
            passed_rules_count=passed,
            violations_count=violations,
            ambiguities_count=ambiguities,
            findings=findings,
            overall_status=overall,
            auditor_notes=auditor_notes
        )

        logger.info(
            f"Compiled Compliance Report for {contract_id}: Status={overall}, "
            f"Violations={violations}, Passed={passed}, Ambiguities={ambiguities}."
        )
        return report
