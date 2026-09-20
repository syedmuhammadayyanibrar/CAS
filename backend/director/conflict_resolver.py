from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.models.findings import RiskReport, NegotiationStrategy, ComplianceReport
from backend.models.hitl import HumanReviewRequest
from backend.core.logging import get_logger

logger = get_logger("DirectorConflictResolver")


class DetectedConflict(BaseModel):
    conflict_id: str
    clause_reference: str
    societies_involved: List[str]
    conflicting_positions: Dict[str, str]
    resolved_automatically: bool = False
    resolution_rationale: str = ""
    requires_human_escalation: bool = True
    escalation_request: Optional[HumanReviewRequest] = None


class ConflictResolutionResponse(BaseModel):
    can_reconcile: bool
    reconciliation_rationale: str
    recommended_position: str
    escalate_to_human: bool


class DirectorConflictResolver:
    """
    Arbitrates disagreements between independent autonomous societies.
    Example:
      - Risk Intelligence: "Strike Section 8.2 immediately (uncapped exposure)."
      - Negotiation Intelligence: "Retain Section 8.2 as commercial leverage to win pricing concessions."
      - Compliance Intelligence: "Section 8.2 is a hard violation of RULE-001."
    Weighs evidentiary backing, policy mandates, and risk severity using Gemini reasoning.
    Escalates to Human-In-The-Loop if contradictory priorities cannot be safely reconciled.
    """

    @staticmethod
    async def detect_and_resolve_conflicts(
        contract_id: str,
        risk_report: Optional[RiskReport],
        negotiation_strategy: Optional[NegotiationStrategy],
        compliance_report: Optional[ComplianceReport]
    ) -> List[DetectedConflict]:
        conflicts: List[DetectedConflict] = []
        if not (risk_report and negotiation_strategy and compliance_report):
            return conflicts

        # Identify overlapping clauses
        risk_clauses = {f.risky_clause_id: f for f in risk_report.findings if f.risky_clause_id}
        strat_clauses = {p.target_clause_id: p for p in negotiation_strategy.positions if p.target_clause_id}
        comp_violations = {f.rule_id: f for f in compliance_report.findings if f.compliance_status == "VIOLATION"}

        for ref, risk_item in risk_clauses.items():
            strat_item = strat_clauses.get(ref)
            if strat_item and risk_item.net_severity in ("HIGH", "CRITICAL"):
                # Potential clash: High Risk vs Concession/Leverage
                is_clash = (
                    "concession" in strat_item.concession.lower() or
                    "trade" in strat_item.fallback_position.lower() or
                    "retain" in strat_item.desired_outcome.lower()
                )
                if is_clash or risk_item.net_severity == "CRITICAL":
                    conflict_id = f"CONF-{len(conflicts)+1:02d}"
                    conflicting_positions = {
                        "risk_intelligence": f"Severely dangerous ({risk_item.net_severity}): {risk_item.why_risky}. Mitigation: {risk_item.suggested_mitigation}",
                        "negotiation_intelligence": f"Proposed term: {strat_item.desired_outcome}. Fallback/Concession: {strat_item.fallback_position}",
                    }

                    prompt = (
                        "You are the Director Conflict Resolver in the Contract Agentic Society.\n"
                        f"Resolving cross-society contradiction on Clause {ref}:\n"
                        f"- Risk Assessment: {conflicting_positions['risk_intelligence']}\n"
                        f"- Negotiation Strategy: {conflicting_positions['negotiation_intelligence']}\n\n"
                        "Can this disagreement be safely reconciled without violating legal boundaries?\n"
                        "Rules:\n"
                        "1. Compliance hard policy rules are non-negotiable.\n"
                        "2. If Risk is CRITICAL (uncapped financial risk), Risk MUST override commercial leverage.\n"
                        "3. If unresolved or ambiguous, escalate_to_human must be True.\n"
                    )

                    res: ConflictResolutionResponse = await gemini_service.generate_structured(
                        prompt=prompt,
                        response_model=ConflictResolutionResponse,
                        system_instruction="You are an executive legal-commercial arbitrator."
                    )

                    hitl_req = None
                    if res.escalate_to_human:
                        hitl_req = HumanReviewRequest(
                            contract_id=contract_id,
                            trigger_source="DIRECTOR_CONFLICT_RESOLVER",
                            reason_for_review=f"Cross-Society Contradiction on {ref} ({risk_item.clause_title})",
                            agent_conclusions=conflicting_positions,
                            disagreement_matrix=f"Risk wants to strike/limit clause; Negotiation proposes using it as trade-off. Resolver: {res.reconciliation_rationale}",
                            evidence_citations=[risk_item.evidence[:150]],
                            action_requested=f"Decide whether to accept commercial concession or enforce strict risk mitigation on {ref}."
                        )

                    conflicts.append(DetectedConflict(
                        conflict_id=conflict_id,
                        clause_reference=ref,
                        societies_involved=["risk_intelligence", "negotiation_intelligence"],
                        conflicting_positions=conflicting_positions,
                        resolved_automatically=res.can_reconcile and not res.escalate_to_human,
                        resolution_rationale=res.reconciliation_rationale,
                        requires_human_escalation=res.escalate_to_human,
                        escalation_request=hitl_req
                    ))

        logger.info(f"Director Conflict Resolver detected {len(conflicts)} cross-society conflict(s).")
        return conflicts
