from typing import List, Dict, Any
from backend.core.logging import get_logger

logger = get_logger("RuleMatcher")


class CandidateRuleMatch:
    def __init__(self, rule: Dict[str, Any], matched_clause_text: str, match_reason: str):
        self.rule = rule
        self.matched_clause_text = matched_clause_text
        self.match_reason = match_reason


class RuleMatcher:
    """
    Deterministic rule indexer.
    Matches explicit fields and keywords between configured policy rules and contract clauses.
    IMPORTANT ARCHITECTURAL LIMITATION:
    Deterministic matching is strictly used for preliminary field/condition indexing.
    Gemini performs the actual contextual interpretation and compliance decision.
    """

    @staticmethod
    def match_explicit_fields(contract_text: str, policy_rules: List[Dict[str, Any]]) -> List[CandidateRuleMatch]:
        lower_contract = contract_text.lower()
        candidates: List[CandidateRuleMatch] = []

        for rule in policy_rules:
            field_matches = rule.get("field_matches", [])
            prohibited_terms = rule.get("prohibited_terms", [])

            # Check for keyword hits
            matched_keywords = [kw for kw in field_matches if kw.lower() in lower_contract]
            prohibited_hits = [pt for pt in prohibited_terms if pt.lower() in lower_contract]

            if matched_keywords or prohibited_hits:
                reason = f"Keyword matches: {matched_keywords}"
                if prohibited_hits:
                    reason += f" | Explicit prohibited terms detected: {prohibited_hits}"

                candidates.append(CandidateRuleMatch(
                    rule=rule,
                    matched_clause_text=contract_text,
                    match_reason=reason
                ))

        logger.info(f"Deterministic Rule Matcher identified {len(candidates)} candidate policy matches for contextual review.")
        return candidates
