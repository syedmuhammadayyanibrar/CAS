import re
from typing import List, Set, Dict, Any, Union


def canonicalize_term(term: str) -> str:
    """Normalizes a category, clause, or obligation label for robust set comparisons."""
    if not term:
        return ""
    # Lowercase, replace hyphens and underscores with spaces, remove punctuation
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", str(term).lower())
    # Collapse multiple spaces
    cleaned = " ".join(cleaned.split())
    # Synonym mappings
    synonyms = {
        "liability cap": "liability",
        "uncapped liability": "liability",
        "missing liability cap": "liability",
        "indemnification": "indemnity",
        "unilateral indemnity": "indemnity",
        "unilateral indemnification": "indemnity",
        "liquidated damages": "penalty",
        "penalties": "penalty",
        "automatic renewal": "renewal",
        "auto renewal": "renewal",
        "evergreen renewal": "renewal",
        "notice period": "notice",
        "notice periods": "notice",
        "payment terms": "payment",
        "payment deadlines": "payment",
        "milestone payment": "payment",
        "service level": "sla",
        "service levels": "sla",
        "data ownership": "ip",
        "intellectual property": "ip",
        "ip rights": "ip",
        "confidentiality agreement": "confidentiality",
        "governing jurisdiction": "governing law",
    }
    return synonyms.get(cleaned, cleaned)


def normalized_set_similarity(expected: List[str], actual: List[str]) -> Dict[str, float]:
    """
    Compares two lists of terms using normalized canonical set comparison.
    Returns precision, recall, and F1.
    """
    if not expected and not actual:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "jaccard": 1.0}
    if not expected or not actual:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "jaccard": 0.0}

    exp_set = {canonicalize_term(x) for x in expected if x}
    act_set = {canonicalize_term(x) for x in actual if x}

    # Intersect with fuzzy subset matching for canonical terms
    tp = 0
    matched_act = set()
    for e in exp_set:
        for a in act_set:
            if a in matched_act:
                continue
            if e == a or e in a or a in e:
                tp += 1
                matched_act.add(a)
                break

    precision = tp / len(act_set) if act_set else 0.0
    recall = tp / len(exp_set) if exp_set else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    union_len = len(exp_set.union(act_set))
    jaccard = tp / union_len if union_len > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "jaccard": round(jaccard, 4)
    }


class EvaluationMetricsCalculator:
    """
    Computes fine-grained accuracy, precision, recall, F1, and workflow scores
    across CAS societies, routing decisions, and execution traces.
    """

    @staticmethod
    def calculate_binary_metrics(true_positives: int, false_positives: int, false_negatives: int, true_negatives: int) -> Dict[str, float]:
        total = true_positives + false_positives + false_negatives + true_negatives
        accuracy = (true_positives + true_negatives) / total if total > 0 else 1.0
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        fpr = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0.0
        fnr = false_negatives / (false_negatives + true_positives) if (false_negatives + true_positives) > 0 else 0.0

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4)
        }

    @staticmethod
    def calculate_workflow_score(
        routing_correct: bool,
        execution_correct: bool,
        hitl_correct: bool,
        final_decision_correct: bool,
        trace_completeness_ratio: float = 1.0
    ) -> float:
        """
        Calculates the normalized 0-100 Workflow Score:
          Workflow Score = (
              routing_correct (25 pts) +
              execution_correct (25 pts) +
              hitl_correct (25 pts) +
              final_decision_correct (25 pts)
          ) * trace_completeness_ratio
        """
        base_score = 0.0
        if routing_correct:
            base_score += 25.0
        if execution_correct:
            base_score += 25.0
        if hitl_correct:
            base_score += 25.0
        if final_decision_correct:
            base_score += 25.0

        score = base_score * max(0.0, min(1.0, trace_completeness_ratio))
        return round(score, 1)

    @staticmethod
    def aggregate_case_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregates individual case evaluation records into executive scorecard metrics."""
        total = len(results)
        if total == 0:
            return {
                "total_cases": 0,
                "passed": 0,
                "failed": 0,
                "end_to_end_accuracy": 0.0,
                "workflow_accuracy": 0.0,
                "risk_f1": 0.0,
                "hitl_accuracy": 0.0,
                "compliance_accuracy": 0.0,
                "routing_accuracy": 0.0,
            }

        passed_count = sum(1 for r in results if r.get("status") == "PASSED")
        failed_count = total - passed_count

        # End-to-end accuracy
        e2e_accuracy = passed_count / total

        # Average workflow score normalized to 0.0 - 1.0
        wf_scores = [r.get("workflow_score", 100.0) for r in results]
        workflow_accuracy = (sum(wf_scores) / total) / 100.0

        # Risk metrics aggregation
        risk_tp = 0
        risk_fp = 0
        risk_fn = 0
        risk_tn = 0
        hitl_correct_count = 0
        comp_correct_count = 0
        comp_total = 0
        routing_correct_count = 0
        routing_total = 0

        for r in results:
            # Risk detection check
            exp_risk = r.get("expected_risk_level", "low").lower() in ("high", "critical")
            act_risk = r.get("actual_risk_level", "low").lower() in ("high", "critical")
            if exp_risk and act_risk:
                risk_tp += 1
            elif not exp_risk and act_risk:
                risk_fp += 1
            elif exp_risk and not act_risk:
                risk_fn += 1
            else:
                risk_tn += 1

            # HITL accuracy check
            if r.get("hitl_correct", True):
                hitl_correct_count += 1

            # Compliance check if applicable
            if "compliance_correct" in r:
                comp_total += 1
                if r["compliance_correct"]:
                    comp_correct_count += 1

            # Routing check if applicable
            if "routing_correct" in r:
                routing_total += 1
                if r["routing_correct"]:
                    routing_correct_count += 1

        risk_metrics = EvaluationMetricsCalculator.calculate_binary_metrics(
            risk_tp, risk_fp, risk_fn, risk_tn
        )

        hitl_accuracy = hitl_correct_count / total
        comp_accuracy = comp_correct_count / comp_total if comp_total > 0 else 1.0
        routing_accuracy = routing_correct_count / routing_total if routing_total > 0 else 1.0

        # Category breakdown
        categories = {}
        for r in results:
            cat = r.get("category", "general")
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0, "failed": 0}
            categories[cat]["total"] += 1
            if r.get("status") == "PASSED":
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1

        return {
            "total_cases": total,
            "passed": passed_count,
            "failed": failed_count,
            "end_to_end_accuracy": round(e2e_accuracy, 4),
            "workflow_accuracy": round(workflow_accuracy, 4),
            "risk_precision": risk_metrics["precision"],
            "risk_recall": risk_metrics["recall"],
            "risk_f1": risk_metrics["f1"],
            "false_positive_rate": risk_metrics["false_positive_rate"],
            "false_negative_rate": risk_metrics["false_negative_rate"],
            "hitl_accuracy": round(hitl_accuracy, 4),
            "compliance_accuracy": round(comp_accuracy, 4),
            "routing_accuracy": round(routing_accuracy, 4),
            "category_breakdown": categories
        }
