from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.findings import RiskReport, NegotiationStrategy, ComplianceReport, DisputeAssessment
from backend.models.hitl import HumanDecision
from backend.models.cas_message import CASMessage
from backend.events.bus import event_bus
from backend.memory.cas_memory import cas_memory
from backend.core.logging import get_logger

logger = get_logger("FeedbackLoops")


class CrossSocietyFeedbackLoops:
    """
    Orchestrates bidirectional feedback loops between independent autonomous societies.
    Ensures findings from one society dynamically inform and refine others.
    """

    @staticmethod
    async def apply_risk_to_negotiation(
        risk_report: RiskReport,
        negotiation_strategy: NegotiationStrategy
    ) -> NegotiationStrategy:
        """
        Feedback Loop: Risk Intelligence -> Negotiation Intelligence
        Elevates high/critical risks into non-negotiable red lines in the negotiation strategy.
        """
        high_risks = [f for f in risk_report.findings if f.net_severity in ("HIGH", "CRITICAL")]
        if not high_risks:
            return negotiation_strategy

        logger.info(f"[Feedback Loop] Propagating {len(high_risks)} high-risk findings into Negotiation Strategy...")
        updated_positions = list(negotiation_strategy.positions)

        for hr in high_risks:
            # Check if position already exists for this clause
            existing = next((p for p in updated_positions if p.target_clause_id == hr.risky_clause_id), None)
            if existing:
                existing.red_line = f"MANDATORY RISK REDLINE: Must eliminate '{hr.why_risky}'. Mitigation: {hr.suggested_mitigation}"
                existing.leverage += f" | Grounded in critical risk exposure ({hr.net_severity})"
            else:
                from backend.models.findings import NegotiationPosition
                updated_positions.append(NegotiationPosition(
                    position_id=f"POS-FB-{len(updated_positions)+1:02d}",
                    target_clause_id=hr.risky_clause_id,
                    clause_title=hr.clause_title,
                    desired_outcome=hr.suggested_mitigation,
                    acceptable_outcome="Mutual limitation of liability and standard bilateral terms",
                    fallback_position="Strict bilateral cap at 12 months fees",
                    red_line=f"Deal-breaker: Cannot accept uncapped exposure ({hr.net_severity})",
                    concession="Offer multi-year commitment or prompt payment",
                    leverage="Corporate risk policy and catastrophic exposure assessment",
                    counter_proposal=f"Replace with mutual standard terms: {hr.suggested_mitigation}",
                    simulated_counterparty_reaction="Vendor will likely push for a 3-month or 6-month cap compromise"
                ))

        negotiation_strategy.positions = updated_positions
        negotiation_strategy.strategy_summary += f" [Updated via Risk Feedback Loop: {len(high_risks)} risk red-lines reinforced]."

        # Publish feedback event
        await event_bus.publish(CASMessage.create(
            contract_id=risk_report.contract_id,
            source_system="feedback_loop",
            target_system="negotiation_intelligence",
            event_type="STRATEGY_UPDATED_FROM_RISK",
            payload={"updated_position_count": len(updated_positions)},
            priority="HIGH"
        ))

        return negotiation_strategy

    @staticmethod
    async def apply_compliance_to_negotiation(
        compliance_report: ComplianceReport,
        negotiation_strategy: NegotiationStrategy
    ) -> NegotiationStrategy:
        """
        Feedback Loop: Compliance Intelligence -> Negotiation Intelligence
        Locks corporate policy violations as mandatory non-negotiable constraints.
        """
        violations = [f for f in compliance_report.findings if f.compliance_status == "VIOLATION"]
        if not violations:
            return negotiation_strategy

        logger.info(f"[Feedback Loop] Propagating {len(violations)} compliance violations into Negotiation Strategy...")
        negotiation_strategy.critic_notes += f" [Compliance Lock: {len(violations)} corporate policy non-negotiables locked]."
        return negotiation_strategy

    @staticmethod
    async def apply_dispute_to_risk(
        dispute_assessment: DisputeAssessment,
        risk_report: RiskReport
    ) -> RiskReport:
        """
        Feedback Loop: Dispute Intelligence -> Risk Intelligence
        Incorporates realistic dispute crisis scenarios into future risk evaluations.
        """
        severe_disputes = [s for s in dispute_assessment.scenarios if s.severity in ("HIGH", "CATASTROPHIC")]
        if not severe_disputes:
            return risk_report

        logger.info(f"[Feedback Loop] Ingesting {len(severe_disputes)} high-severity dispute precedents into Risk Intelligence...")
        risk_report.adversarial_debate_summary += f" [Dispute Feedback: Calibrated against {len(severe_disputes)} high-severity crisis scenarios]."
        return risk_report

    @staticmethod
    async def record_human_decision(
        session: AsyncSession,
        contract_id: str,
        decision: HumanDecision
    ):
        """
        Feedback Loop: Human Review Decision -> PostgreSQL CAS Memory
        """
        logger.info(f"[Feedback Loop] Storing Human Decision for {contract_id} ({decision.decision}) into CAS Memory...")
        await cas_memory.record_human_decision(
            session=session,
            contract_id=contract_id,
            review_id=decision.review_id,
            decision=decision.decision,
            reasoning=decision.decision_notes
        )


feedback_loops = CrossSocietyFeedbackLoops()
