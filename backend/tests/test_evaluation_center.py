import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
try:
    from backend.evaluation.metrics import (
        canonicalize_term,
        normalized_set_similarity,
        EvaluationMetricsCalculator
    )
    from backend.evaluation.evaluator import CaseEvaluator
    from backend.evaluation.runner import evaluation_runner
except ImportError:
    from evaluation.metrics import (
        canonicalize_term,
        normalized_set_similarity,
        EvaluationMetricsCalculator
    )
    from evaluation.evaluator import CaseEvaluator
    from evaluation.runner import evaluation_runner


def test_canonicalize_term():
    assert canonicalize_term("Uncapped Liability") == "liability"
    assert canonicalize_term("Liquidated Damages") == "penalty"
    assert canonicalize_term("Notice Period") == "notice"
    assert canonicalize_term("Automatic Renewal") == "renewal"


def test_normalized_set_similarity():
    # Order-insensitive match
    exp = ["termination", "liability"]
    act = ["liability", "termination"]
    res = normalized_set_similarity(exp, act)
    assert res["f1"] == 1.0
    assert res["precision"] == 1.0
    assert res["recall"] == 1.0

    # Partial match
    exp2 = ["uncapped liability", "penalty", "sla"]
    act2 = ["liability cap", "payment"]
    res2 = normalized_set_similarity(exp2, act2)
    assert res2["recall"] > 0.0


def test_workflow_score_calculation():
    # Perfect run: 25 + 25 + 25 + 25 = 100
    score = EvaluationMetricsCalculator.calculate_workflow_score(
        routing_correct=True,
        execution_correct=True,
        hitl_correct=True,
        final_decision_correct=True
    )
    assert score == 100.0

    # Partial run: missing HITL: 25 + 25 + 0 + 0 = 50
    score_partial = EvaluationMetricsCalculator.calculate_workflow_score(
        routing_correct=True,
        execution_correct=True,
        hitl_correct=False,
        final_decision_correct=False
    )
    assert score_partial == 50.0


def test_datasets_integrity():
    cases = evaluation_runner.load_all_cases()
    # Ensure all 50 cases loaded
    assert len(cases) >= 50
    case_ids = [c["case_id"] for c in cases]
    assert len(case_ids) == len(set(case_ids)), "Duplicate case IDs detected!"

    # Check categories
    categories = {c.get("category") for c in cases}
    assert "normal" in categories
    assert "risk" in categories
    assert "compliance" in categories
    assert "obligation" in categories
    assert "conflict" in categories
    assert "ambiguous" in categories
    assert "adversarial" in categories
    assert "routing" in categories


@pytest.mark.asyncio
async def test_case_evaluator_contract_pass():
    case_def = {
        "case_id": "TEST-CASE-001",
        "title": "Clean NDA",
        "category": "normal",
        "expected": {
            "contract_type": "NDA",
            "risk_level": "low",
            "risk_categories": ["confidentiality"],
            "obligations": ["safeguard_confidential_information"],
            "compliance_issues": [],
            "hitl_required": False,
            "expected_societies": ["contract_intelligence", "risk_intelligence"]
        }
    }
    actual_output = {
        "contract_graph": {"title": "Clean NDA", "clauses": []},
        "risk_report": {"overall_risk_score": 0.1, "findings": [{"clause_title": "Confidentiality"}]},
        "compliance_report": {"findings": [], "overall_status": "COMPLIANT"},
        "director_routing": {"activated_societies": ["contract_intelligence", "risk_intelligence"]},
        "human_in_the_loop": None,
        "status": "ANALYZED"
    }
    eval_res = CaseEvaluator.evaluate_contract_case(case_def, actual_output)
    assert eval_res["status"] == "PASSED"
    assert eval_res["workflow_score"] == 100.0
    assert eval_res["hitl_correct"] is True


@pytest.mark.asyncio
async def test_case_evaluator_contract_failure_recording():
    case_def = {
        "case_id": "TEST-CASE-002",
        "title": "Critical Uncapped Liability",
        "category": "risk",
        "expected": {
            "risk_level": "critical",
            "risk_categories": ["liability"],
            "compliance_issues": ["RULE-001"],
            "hitl_required": True,
            "expected_societies": ["risk_intelligence"]
        }
    }
    # Actual output falsely claims low risk and no HITL
    actual_output = {
        "risk_report": {"overall_risk_score": 0.1, "findings": []},
        "compliance_report": {"findings": [], "overall_status": "COMPLIANT"},
        "director_routing": {"activated_societies": ["contract_intelligence"]},
        "human_in_the_loop": None,
        "status": "ANALYZED"
    }
    eval_res = CaseEvaluator.evaluate_contract_case(case_def, actual_output)
    assert eval_res["status"] == "FAILED"
    assert eval_res["failure_record"] is not None
    assert eval_res["failure_record"]["case_id"] == "TEST-CASE-002"
    assert "HITL" in eval_res["failure_record"]["failure_reason"] or "Risk" in eval_res["failure_record"]["failure_reason"]


@pytest.mark.asyncio
async def test_routing_case_evaluation():
    case_def = {
        "case_id": "ROUTE-TEST-001",
        "title": "Signed Contract Transition",
        "category": "routing",
        "expected": {
            "expected_society": "obligation_intelligence",
            "expected_hitl_state": "NOT_REQUIRED"
        }
    }
    actual_output = {
        "selected_societies": ["obligation_intelligence"],
        "status": "PROCESSED",
        "hitl_required": False
    }
    res = CaseEvaluator.evaluate_routing_case(case_def, actual_output)
    assert res["status"] == "PASSED"
    assert res["workflow_score"] == 100.0


@pytest.mark.asyncio
async def test_evaluation_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # GET /evaluation/cases
        cases_res = await ac.get("/evaluation/cases")
        assert cases_res.status_code == 200
        cases_data = cases_res.json()
        assert len(cases_data) >= 50

        # GET /evaluation/cases/CASE-001
        case_res = await ac.get("/evaluation/cases/CASE-001")
        assert case_res.status_code == 200
        assert case_res.json()["case_id"] == "CASE-001"

        # GET /evaluation/summary
        summary_res = await ac.get("/evaluation/summary")
        assert summary_res.status_code == 200
        assert "end_to_end_accuracy" in summary_res.json()

        # Run single case via POST /evaluation/run/CASE-001
        run_res = await ac.post("/evaluation/run/CASE-001")
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert run_data["case_id"] == "CASE-001"
        assert run_data["status"] in ("PASSED", "FAILED")
        assert "workflow_score" in run_data

        # GET /evaluation/results
        results_res = await ac.get("/evaluation/results")
        assert results_res.status_code == 200
        assert isinstance(results_res.json(), list)

        # GET /evaluation/failures
        failures_res = await ac.get("/evaluation/failures")
        assert failures_res.status_code == 200
        assert "failures" in failures_res.json()

        # GET /evaluation/runs
        runs_res = await ac.get("/evaluation/runs")
        assert runs_res.status_code == 200
        assert isinstance(runs_res.json(), list)
