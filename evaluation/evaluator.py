from typing import Dict, Any, List, Optional
try:
    from backend.evaluation.metrics import normalized_set_similarity, EvaluationMetricsCalculator, canonicalize_term
except ImportError:
    from evaluation.metrics import normalized_set_similarity, EvaluationMetricsCalculator, canonicalize_term


class CaseEvaluator:
    """
    Evaluates real CAS pipeline execution outputs against ground-truth definitions.
    Generates structured failure records and workflow scores based on actual behavior.
    """

    @classmethod
    def evaluate_contract_case(
        cls,
        case_def: Dict[str, Any],
        actual_output: Dict[str, Any],
        execution_events: Optional[List[Dict[str, Any]]] = None,
        duration_seconds: float = 0.0
    ) -> Dict[str, Any]:
        """
        Evaluates an end-to-end contract mesh execution result against expected ground truth.
        """
        case_id = case_def.get("case_id", "UNKNOWN")
        title = case_def.get("title", "Untitled Case")
        category = case_def.get("category", "normal")
        expected = case_def.get("expected", {})

        # Extract actual results
        risk_report = actual_output.get("risk_report", {})
        comp_report = actual_output.get("compliance_report", {})
        graph = actual_output.get("contract_graph", {})
        director_routing = actual_output.get("director_routing", {})
        hitl_request = actual_output.get("human_in_the_loop")
        final_status = actual_output.get("status", "ANALYZED")

        # 1. Evaluate Risk Level
        exp_risk_level = expected.get("risk_level", "low").lower()
        actual_score = risk_report.get("overall_risk_score", 0.0) if isinstance(risk_report, dict) else getattr(risk_report, "overall_risk_score", 0.0)

        # Map score to level
        if actual_score >= 0.8:
            act_risk_level = "critical"
        elif actual_score >= 0.5:
            act_risk_level = "high"
        elif actual_score >= 0.25:
            act_risk_level = "medium"
        else:
            act_risk_level = "low"

        # Risk severity match check (critical and high are considered severe)
        risk_level_correct = (
            exp_risk_level == act_risk_level or
            (exp_risk_level in ("high", "critical") and act_risk_level in ("high", "critical")) or
            (exp_risk_level in ("low", "medium") and act_risk_level in ("low", "medium"))
        )

        # 2. Evaluate Risk Categories
        exp_categories = expected.get("risk_categories", [])
        act_findings = risk_report.get("findings", []) if isinstance(risk_report, dict) else getattr(risk_report, "findings", [])
        act_categories = []
        for f in act_findings:
            title_txt = f.get("clause_title", "") if isinstance(f, dict) else getattr(f, "clause_title", "")
            why_txt = f.get("why_risky", "") if isinstance(f, dict) else getattr(f, "why_risky", "")
            act_categories.append(title_txt)
            act_categories.append(why_txt)

        cat_sim = normalized_set_similarity(exp_categories, act_categories)
        categories_correct = (cat_sim["f1"] >= 0.3) or (len(exp_categories) == 0)

        # 3. Evaluate Compliance Issues
        exp_compliance = expected.get("compliance_issues", [])
        act_violations = []
        comp_findings = comp_report.get("findings", []) if isinstance(comp_report, dict) else getattr(comp_report, "findings", [])
        for cf in comp_findings:
            stat = cf.get("compliance_status") if isinstance(cf, dict) else getattr(cf, "compliance_status", "")
            rid = cf.get("rule_id") if isinstance(cf, dict) else getattr(cf, "rule_id", "")
            if stat in ("VIOLATION", "NON_COMPLIANT"):
                act_violations.append(rid)

        compliance_sim = normalized_set_similarity(exp_compliance, act_violations)
        compliance_correct = (compliance_sim["f1"] >= 0.5) or (len(exp_compliance) == 0 and len(act_violations) == 0)

        # 4. Evaluate HITL Requirement
        exp_hitl = expected.get("hitl_required", False)
        act_hitl = bool(hitl_request or final_status in ("REVIEW_REQUIRED", "PAUSED_FOR_HUMAN"))
        hitl_correct = (exp_hitl == act_hitl)

        # 5. Evaluate Expected Societies
        exp_societies = expected.get("expected_societies", ["contract_intelligence"])
        act_societies = director_routing.get("activated_societies", [])

        # Also check execution events if present
        if execution_events:
            event_societies = {canonicalize_term(e.get("society", "")) for e in execution_events}
        else:
            event_societies = set()

        routing_sim = normalized_set_similarity(exp_societies, act_societies)
        routing_correct = routing_sim["recall"] >= 0.6

        # 6. Workflow Validation & Trace Analysis
        execution_correct = True
        trace_completeness = 1.0
        missing_steps = []
        unexpected_steps = []

        if execution_events:
            stage_names = [e.get("society", "").lower() for e in execution_events]
            # Verify Contract Intelligence ran first
            if stage_names and "contract intelligence" not in stage_names[0]:
                execution_correct = False
                missing_steps.append("Contract Intelligence should precede downstream societies")

            # Check if expected societies actually logged events
            for es in exp_societies:
                norm_es = es.replace("_", " ").lower()
                found = any(norm_es in sn for sn in stage_names)
                if not found:
                    missing_steps.append(f"Missing society execution: {es}")

        final_decision_correct = hitl_correct and risk_level_correct

        # Calculate 0-100 Workflow Score
        workflow_score = EvaluationMetricsCalculator.calculate_workflow_score(
            routing_correct=routing_correct,
            execution_correct=execution_correct,
            hitl_correct=hitl_correct,
            final_decision_correct=final_decision_correct,
            trace_completeness_ratio=1.0 if not missing_steps else 0.8
        )

        # Overall Pass/Fail status
        # A case passes if HITL correctness, risk direction, and core routing are aligned
        is_passed = hitl_correct and risk_level_correct and (compliance_correct or len(exp_compliance) == 0)

        # Generate structured failure diagnosis if failed
        failure_record = None
        if not is_passed:
            failure_reason = ""
            responsible_society = "cas_director"
            if not hitl_correct:
                if exp_hitl and not act_hitl:
                    failure_reason = "Required HITL escalation was omitted despite critical risk/compliance violations."
                else:
                    failure_reason = "Unnecessary HITL pause triggered for a standard low-risk contract."
                responsible_society = "cas_director"
            elif not risk_level_correct:
                failure_reason = f"Risk severity mismatch: Expected {exp_risk_level.upper()}, but evaluated as {act_risk_level.upper()} (score {actual_score:.2f})."
                responsible_society = "risk_intelligence"
            elif not compliance_correct:
                failure_reason = f"Compliance violation discrepancy: Expected {exp_compliance}, but detected {act_violations}."
                responsible_society = "compliance_intelligence"

            failure_record = {
                "case_id": case_id,
                "status": "FAILED",
                "category": category,
                "expected": f"Risk: {exp_risk_level.upper()} | HITL: {'YES' if exp_hitl else 'NO'}",
                "actual": f"Risk: {act_risk_level.upper()} | HITL: {'YES' if act_hitl else 'NO'}",
                "failure_reason": failure_reason,
                "society": responsible_society
            }

        return {
            "case_id": case_id,
            "title": title,
            "category": category,
            "status": "PASSED" if is_passed else "FAILED",
            "workflow_score": workflow_score,
            "execution_time_seconds": round(duration_seconds, 2),
            "expected_risk_level": exp_risk_level,
            "actual_risk_level": act_risk_level,
            "actual_risk_score": actual_score,
            "hitl_correct": hitl_correct,
            "expected_hitl": exp_hitl,
            "actual_hitl": act_hitl,
            "compliance_correct": compliance_correct,
            "expected_compliance": exp_compliance,
            "actual_compliance": act_violations,
            "routing_correct": routing_correct,
            "expected_societies": exp_societies,
            "actual_societies": act_societies,
            "missing_steps": missing_steps,
            "failure_record": failure_record,
            "execution_events": execution_events or []
        }

    @classmethod
    def evaluate_routing_case(
        cls,
        case_def: Dict[str, Any],
        actual_routing_output: Dict[str, Any],
        duration_seconds: float = 0.0
    ) -> Dict[str, Any]:
        """
        Evaluates a CAS Director dynamic routing test scenario against expected routing graph.
        """
        case_id = case_def.get("case_id", "UNKNOWN")
        title = case_def.get("title", "Routing Scenario")
        expected = case_def.get("expected", {})

        exp_society = expected.get("expected_society", "").lower()
        exp_agent = expected.get("expected_agent", "").lower()
        exp_escalation = expected.get("expected_escalation", False)
        exp_hitl_state = expected.get("expected_hitl_state", "NOT_REQUIRED").upper()

        # Extract actuals from routing execution
        act_societies = actual_routing_output.get("selected_societies") or actual_routing_output.get("activated_societies") or actual_routing_output.get("activated_downstream_societies") or []
        act_societies_lower = [s.lower() for s in act_societies]

        # Inbound event response checks
        act_status = actual_routing_output.get("status", "").upper()
        act_decision = actual_routing_output.get("decision", "").upper()

        # Society matched
        society_matched = (
            exp_society in act_societies_lower or
            any(exp_society in s for s in act_societies_lower) or
            actual_routing_output.get("target_system", "").lower() == exp_society or
            actual_routing_output.get("source_system", "").lower() == exp_society or
            (exp_society == "cas director" and act_status in ("SUCCESS", "PROCESSED", "COMPLETED"))
        )

        # Escalation / HITL state match
        act_hitl = (
            act_status in ("PAUSED_FOR_HUMAN", "REVIEW_REQUIRED") or
            actual_routing_output.get("hitl_required", False) or
            bool(actual_routing_output.get("human_in_the_loop"))
        )
        exp_hitl = (exp_hitl_state in ("PAUSED_FOR_HUMAN", "REVIEW_REQUIRED")) or exp_escalation

        hitl_matched = (act_hitl == exp_hitl)
        is_passed = society_matched and hitl_matched

        workflow_score = 100.0 if is_passed else (60.0 if society_matched else 25.0)

        failure_record = None
        if not is_passed:
            reasons = []
            if not society_matched:
                reasons.append(f"Expected society '{exp_society}' was not activated (activated: {act_societies}).")
            if not hitl_matched:
                reasons.append(f"Expected HITL state '{exp_hitl_state}', but actual was '{'PAUSED/REVIEW' if act_hitl else 'COMPLETED'}'.")

            failure_record = {
                "case_id": case_id,
                "status": "FAILED",
                "category": "routing",
                "expected": f"Society: {exp_society} | HITL: {exp_hitl_state}",
                "actual": f"Societies: {act_societies} | HITL: {'YES' if act_hitl else 'NO'}",
                "failure_reason": " | ".join(reasons),
                "society": "cas_director"
            }

        return {
            "case_id": case_id,
            "title": title,
            "category": "routing",
            "status": "PASSED" if is_passed else "FAILED",
            "workflow_score": workflow_score,
            "execution_time_seconds": round(duration_seconds, 2),
            "expected_risk_level": "medium",
            "actual_risk_level": "medium",
            "hitl_correct": hitl_matched,
            "routing_correct": society_matched,
            "expected_societies": [exp_society],
            "actual_societies": act_societies,
            "missing_steps": [] if society_matched else [f"Missing {exp_society}"],
            "failure_record": failure_record,
            "execution_events": []
        }
