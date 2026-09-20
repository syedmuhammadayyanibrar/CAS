from typing import List, Dict, Any
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.systems.compliance_intelligence.rules_engine import CandidateRuleMatch
from backend.core.logging import get_logger

logger = get_logger("ComplianceAnalyzer")


class EvaluatedRuleDTO(BaseModel):
    rule_id: str
    rule_name: str
    requirement: str
    contract_evidence: str
    compliance_status: str  # COMPLIANT, VIOLATION, AMBIGUOUS, EXEMPT
    reason: str
    confidence: float = 0.95
    recommended_action: str


class ContextualComplianceResponse(BaseModel):
    evaluations: List[EvaluatedRuleDTO] = Field(default_factory=list)
    contextual_summary: str = ""


class ComplianceAnalyzer:
    """
    PRIMARY DECISION-MAKER in Compliance Intelligence.
    Uses Google Gemini API to contextually interpret contract terms against configured policy rules,
    resolving semantic subtleties, carve-outs, and legal intent without hallucinating external laws.
    """

    @staticmethod
    async def analyze_compliance(
        contract_text: str,
        policy_name: str,
        candidate_matches: List[CandidateRuleMatch]
    ) -> List[EvaluatedRuleDTO]:
        rules_context = []
        for c in candidate_matches:
            rule = c.rule
            rules_context.append(
                f"- [RULE: {rule.get('rule_id')}] {rule.get('rule_name')}\n"
                f"  Requirement: {rule.get('requirement')}\n"
                f"  Criticality: {rule.get('criticality')}\n"
                f"  Prohibited Terms: {rule.get('prohibited_terms', [])}\n"
                f"  Permitted Values: {rule.get('permitted_values', [])}\n"
                f"  Indexer Note: {c.match_reason}\n"
            )

        prompt = (
            "You are the Compliance Analyzer agent in a Compliance Intelligence System.\n"
            f"Active Policy: {policy_name}\n\n"
            "Evaluate the contract text against each configured policy rule below.\n"
            "You are the primary decision-maker: use contextual interpretation to determine whether the contract "
            "satisfies, breaches, or creates ambiguity regarding each requirement.\n"
            "For each rule, provide:\n"
            "- rule_id & rule_name\n"
            "- requirement\n"
            "- contract_evidence (exact verbatim clause quote)\n"
            "- compliance_status (one of: COMPLIANT, VIOLATION, AMBIGUOUS, EXEMPT)\n"
            "- reason (clear contextual legal reasoning grounded exclusively in this contract)\n"
            "- confidence (0.0 to 1.0)\n"
            "- recommended_action (exact required contractual amendment)\n\n"
            f"RULES TO EVALUATE:\n" + "\n".join(rules_context)
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text[:4000])

        result: ContextualComplianceResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=ContextualComplianceResponse,
            system_instruction="You are a strict corporate compliance auditor grounding decisions exclusively in provided policy rules."
        )

        logger.info(f"Compliance Analyzer evaluated {len(result.evaluations)} rules.")
        return result.evaluations
