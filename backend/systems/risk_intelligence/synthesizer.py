from typing import List, Dict
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.risk_intelligence.counterargument import DebatedRiskDTO
from backend.systems.risk_intelligence.evidence_verifier import VerifiedEvidenceDTO
from backend.systems.risk_intelligence.severity_assessor import NetSeverityDTO
from backend.models.findings import RiskFinding, RiskReport
from backend.core.logging import get_logger

logger = get_logger("RiskSynthesizer")


class MitigationSuggestionDTO(BaseModel):
    clause_reference: str
    suggested_mitigation: str


class MitigationResponse(BaseModel):
    mitigations: List[MitigationSuggestionDTO] = Field(default_factory=list)
    executive_summary: str = ""


class RiskSynthesizer:
    """
    Final agent in the Adversarial Debate pipeline.
    Synthesizes the debated findings into a cohesive, structured RiskReport,
    generates concrete mitigations, and sets human review triggers.
    """

    @staticmethod
    async def synthesize_report(
        contract_id: str,
        debated_risks: List[DebatedRiskDTO],
        assessments: List[NetSeverityDTO],
        evidence_lookup: Dict[str, VerifiedEvidenceDTO]
    ) -> RiskReport:
        assessment_map = {a.clause_reference: a for a in assessments}

        # Query Gemini for actionable commercial mitigations
        debate_points = "\n".join([
            f"- Clause: {d.clause_reference} | Title: {d.clause_title} | Severity: {assessment_map.get(d.clause_reference, NetSeverityDTO(clause_reference='', net_severity='MEDIUM', severity_rationale='')).net_severity}"
            for d in debated_risks
        ])
        mitigation_prompt = (
            "You are the Risk Synthesizer agent in an Adversarial Risk Intelligence System.\n"
            "For each of the evaluated risks below, propose a concrete, practical contractual mitigation "
            "(e.g., standard redline amendment, reciprocal cap, or deletion).\n\n"
            f"RISKS:\n{debate_points}\n"
        )

        mitigation_res: MitigationResponse = await gemini_service.generate_structured(
            prompt=mitigation_prompt,
            response_model=MitigationResponse,
            system_instruction="You are an expert commercial contract drafting and risk mitigation specialist."
        )
        mitigation_map = {m.clause_reference: m.suggested_mitigation for m in mitigation_res.mitigations}

        findings: List[RiskFinding] = []
        severity_weights = {"LOW": 0.1, "MEDIUM": 0.4, "HIGH": 0.8, "CRITICAL": 1.0}
        total_score = 0.0
        escalate = False

        for idx, d in enumerate(debated_risks):
            ass = assessment_map.get(d.clause_reference)
            net_sev = ass.net_severity if ass else "MEDIUM"
            is_hr = ass.recommend_human_review if ass else (net_sev in ("HIGH", "CRITICAL"))
            if net_sev in ("HIGH", "CRITICAL"):
                escalate = True

            weight = severity_weights.get(net_sev, 0.4)
            total_score += weight

            ev = evidence_lookup.get(d.clause_reference)
            evidence_text = ev.verbatim_text_found if ev else d.clause_reference

            findings.append(RiskFinding(
                finding_id=f"RSK-{idx+1:03d}",
                risky_clause_id=d.clause_reference,
                clause_title=d.clause_title,
                why_risky=d.hunter_claim,
                exposed_party="Customer",
                consequence=ass.severity_rationale if ass else "Potential financial/operational exposure",
                initial_severity="HIGH",
                evidence=evidence_text,
                counter_argument=d.counterargument,
                counter_argument_strength=d.counterargument_strength,
                net_severity=net_sev,
                uncertainty=ass.uncertainty if ass else 0.1,
                suggested_mitigation=mitigation_map.get(d.clause_reference, "Propose mutual bilateral terms and cap liability."),
                requires_human_review=is_hr
            ))

        overall_score = min(1.0, (total_score / max(1, len(findings))) if findings else 0.0)

        report = RiskReport(
            contract_id=contract_id,
            overall_risk_score=round(overall_score, 2),
            findings=findings,
            adversarial_debate_summary=mitigation_res.executive_summary or "Adversarial risk debate completed.",
            requires_human_escalation=escalate
        )

        logger.info(
            f"Risk Report compiled for {contract_id}: {len(findings)} findings, "
            f"Overall Score: {report.overall_risk_score}, Escalation Required: {report.requires_human_escalation}"
        )
        return report
