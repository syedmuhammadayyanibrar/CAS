import uuid
from typing import Optional, Union, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.logging import get_logger
from backend.models.findings import RiskReport
from backend.models.graph import ContractGraph
from backend.models.cas_message import CASMessage
from backend.events.bus import event_bus
from backend.systems.risk_intelligence.hunter import RiskHunter
from backend.systems.risk_intelligence.legal_reasoner import LegalReasoner
from backend.systems.risk_intelligence.counterargument import CounterargumentAgent
from backend.systems.risk_intelligence.evidence_verifier import EvidenceVerifier
from backend.systems.risk_intelligence.severity_assessor import SeverityAssessor
from backend.systems.risk_intelligence.synthesizer import RiskSynthesizer
from backend.integrations.adapters import SlackAdapter
from backend.database.schema import RiskReportModel

logger = get_logger("RiskIntelligenceSystem")


class RiskIntelligenceSystem:
    """
    SYSTEM 2 — RISK INTELLIGENCE
    Architecture: Adversarial Debate Architecture
    Determines where a contract exposes an organization to risk through active debate,
    counterarguments, and evidentiary cross-examination.
    Can run completely independently.
    """

    @classmethod
    async def analyze_risk(
        cls,
        contract: Union[str, ContractGraph],
        contract_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> RiskReport:
        if isinstance(contract, ContractGraph):
            cid = contract.contract_id
            contract_text = "\n\n".join([f"{c.section_number} {c.title}:\n{c.text}" for c in contract.clauses])
        else:
            cid = contract_id or f"CTR-{uuid.uuid4().hex[:8].upper()}"
            contract_text = contract

        logger.info(f"Initiating Adversarial Risk Debate for {cid}...")

        # Step 1: Risk Hunter
        raw_risks = await RiskHunter.hunt_risks(contract_text)

        # Step 2: Legal Reasoner
        reasoned_risks = await LegalReasoner.reason_risks(raw_risks, contract_text)

        # Step 3: Counterargument Agent (Actively attacks/disproves risks)
        debated_risks = await CounterargumentAgent.attack_risks(reasoned_risks, contract_text)

        # Step 4: Evidence Verifier
        evidence_lookup = await EvidenceVerifier.verify_evidence(debated_risks, contract_text)

        # Step 5: Severity Assessor
        assessments = await SeverityAssessor.assess_severity(debated_risks, evidence_lookup)

        # Step 6: Risk Synthesizer
        report = await RiskSynthesizer.synthesize_report(
            contract_id=cid,
            debated_risks=debated_risks,
            assessments=assessments,
            evidence_lookup=evidence_lookup
        )

        # Step 7: Persist in PostgreSQL
        if db_session:
            db_report = RiskReportModel(
                contract_id=cid,
                overall_score=report.overall_risk_score,
                requires_escalation=report.requires_human_escalation,
                report_json=report.model_dump(mode="json")
            )
            db_session.add(db_report)
            await db_session.commit()
            logger.info(f"Persisted Risk Report {cid} in PostgreSQL.")

        # Step 8: Standardized CASMessage publication
        message = CASMessage.create(
            contract_id=cid,
            source_system="risk_intelligence",
            target_system="director",
            event_type="RISK_EVALUATED",
            payload={
                "contract_id": cid,
                "overall_risk_score": report.overall_risk_score,
                "finding_count": len(report.findings),
                "requires_human_escalation": report.requires_human_escalation,
                "top_risks": [f.model_dump(mode="json") for f in report.findings[:3]]
            },
            evidence_refs=[f.risky_clause_id for f in report.findings if f.risky_clause_id],
            confidence=0.92,
            priority="HIGH" if report.requires_human_escalation else "MEDIUM"
        )
        await event_bus.publish(message)

        # Step 9: Trigger Fastn Risk Escalation Workflow if critical risks detected
        if report.requires_human_escalation and report.findings:
            top_risk = next((f for f in report.findings if f.net_severity in ("HIGH", "CRITICAL")), report.findings[0])
            await SlackAdapter.post_risk_alert(
                contract_id=cid,
                severity=top_risk.net_severity,
                clause=top_risk.clause_title,
                consequence=top_risk.consequence,
                evidence=top_risk.evidence[:200]
            )

        return report


risk_intelligence_system = RiskIntelligenceSystem()
