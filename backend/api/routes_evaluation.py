import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.core.logging import get_logger
from backend.database.db import get_db, ensure_db_initialized
from backend.database.schema import EvaluationRunModel, EvaluationCaseResultModel
try:
    from backend.evaluation.runner import evaluation_runner, EvaluationRunner
except ImportError:
    from evaluation.runner import evaluation_runner, EvaluationRunner

logger = get_logger("RoutesEvaluation")
router = APIRouter(prefix="/evaluation", tags=["CAS Evaluation Center"])


def load_baseline_run_data() -> Optional[Dict[str, Any]]:
    """Loads pre-computed baseline evaluation benchmark from disk."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "evaluation", "datasets", "baseline_benchmark.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "evaluation", "datasets", "baseline_benchmark.json"),
        os.path.join(os.getcwd(), "backend", "evaluation", "datasets", "baseline_benchmark.json"),
        os.path.join(os.getcwd(), "evaluation", "datasets", "baseline_benchmark.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load baseline benchmark from {p}: {e}")
    return None


async def ensure_baseline_seeded(db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Ensures the evaluation benchmark dataset is seeded into the database on cold start."""
    try:
        await ensure_db_initialized()
        stmt = select(EvaluationRunModel.run_id).limit(1)
        existing = (await db.execute(stmt)).scalars().first()
        if existing:
            return None

        data = load_baseline_run_data()
        if not data:
            return None

        run_rec = EvaluationRunModel(
            run_id=data["run_id"],
            run_number=data.get("run_number", 1),
            dataset_version=data.get("dataset_version", "1.0.0"),
            number_of_cases=data.get("number_of_cases", len(data.get("results", []))),
            passed=data.get("passed", 0),
            failed=data.get("failed", 0),
            metrics_json=data.get("metrics_json", {}),
            model_provider=data.get("model_provider", "Google Gemini API"),
            cas_version=data.get("cas_version", "1.0.0"),
            duration_seconds=data.get("duration_seconds", 0.0)
        )
        db.add(run_rec)

        for r in data.get("results", []):
            case_rec = EvaluationCaseResultModel(
                run_id=data["run_id"],
                case_id=r.get("case_id"),
                title=r.get("title"),
                category=r.get("category"),
                status=r.get("status"),
                expected_json=r.get("expected_json", {}),
                actual_json=r.get("actual_json", {}),
                failure_reason=r.get("failure_reason"),
                society=r.get("society"),
                workflow_score=r.get("workflow_score", 100.0),
                execution_time_seconds=r.get("execution_time_seconds", 0.0),
                execution_trace_json=r.get("execution_trace_json", [])
            )
            db.add(case_rec)

        await db.commit()
        logger.info(f"Seeded baseline evaluation benchmark with {len(data.get('results', []))} cases.")
        if not evaluation_runner.latest_run_summary:
            evaluation_runner.latest_run_summary = data.get("metrics_json")
        return data
    except Exception as e:
        logger.warning(f"Could not seed baseline evaluation: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
        return None


class RunEvaluationRequest(BaseModel):
    mode: str = "all"  # 'all', 'failed', 'category', 'single'
    category: Optional[str] = None
    case_id: Optional[str] = None
    async_execution: bool = False


@router.get("/summary")
async def get_evaluation_summary(
    run_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns executive evaluation metrics (accuracy, workflow score, risk F1, HITL accuracy, category breakdowns).
    Loads from latest in-memory run, latest database record, or seeded benchmark baseline.
    """
    await ensure_baseline_seeded(db)

    # If specific run_id requested, fetch from DB
    if run_id:
        stmt = select(EvaluationRunModel).where(EvaluationRunModel.run_id == run_id)
        run_rec = (await db.execute(stmt)).scalars().first()
        if run_rec:
            return run_rec.metrics_json
        data = load_baseline_run_data()
        if data and data.get("run_id") == run_id:
            return data.get("metrics_json")
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")

    # Check in-memory runner first
    if evaluation_runner.latest_run_summary:
        return evaluation_runner.latest_run_summary

    # Otherwise fetch latest run from DB
    stmt = select(EvaluationRunModel).order_by(desc(EvaluationRunModel.created_at)).limit(1)
    latest_db_run = (await db.execute(stmt)).scalars().first()
    if latest_db_run:
        return latest_db_run.metrics_json

    # Fallback to pre-computed baseline benchmark
    data = load_baseline_run_data()
    if data and data.get("metrics_json"):
        return data.get("metrics_json")

    # Clean initial fallback
    all_cases = evaluation_runner.load_all_cases()
    return {
        "total_cases": len(all_cases),
        "passed": 0,
        "failed": 0,
        "end_to_end_accuracy": 0.0,
        "workflow_accuracy": 0.0,
        "risk_precision": 0.0,
        "risk_recall": 0.0,
        "risk_f1": 0.0,
        "false_positive_rate": 0.0,
        "false_negative_rate": 0.0,
        "hitl_accuracy": 0.0,
        "compliance_accuracy": 0.0,
        "routing_accuracy": 0.0,
        "status": "NOT_YET_RUN",
        "category_breakdown": {}
    }


@router.get("/cases")
async def list_evaluation_cases(
    category: Optional[str] = None
):
    """Lists all deterministic evaluation cases across contract, adversarial, and routing datasets."""
    cases = evaluation_runner.load_all_cases()
    if category and category.lower() != "all":
        cases = [c for c in cases if c.get("category", "").lower() == category.lower()]

    summary_cases = []
    for c in cases:
        summary_cases.append({
            "case_id": c.get("case_id"),
            "title": c.get("title"),
            "category": c.get("category"),
            "expected_risk": c.get("expected", {}).get("risk_level", "low"),
            "expected_hitl": c.get("expected", {}).get("hitl_required", False),
            "expected_societies": c.get("expected", {}).get("expected_societies", []),
            "has_adversarial": c.get("category") == "adversarial",
            "adversarial_type": c.get("adversarial_type")
        })
    return summary_cases


@router.get("/cases/{case_id}")
async def get_evaluation_case(case_id: str):
    """Retrieves full case details including raw contract text and expected outcomes."""
    c = evaluation_runner.get_case_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return c


@router.post("/run")
async def run_evaluation(
    req: RunEvaluationRequest,
    background_tasks: BackgroundTasks
):
    """
    Executes the CAS Evaluation Center benchmark.
    Supports running all, failed, category, or single case.
    """
    if evaluation_runner.is_running:
        return {
            "status": "ALREADY_RUNNING",
            "message": "An evaluation run is currently active.",
            "progress_percent": evaluation_runner.progress_percent,
            "current_case_id": evaluation_runner.current_case_id
        }

    if req.async_execution:
        background_tasks.add_task(
            evaluation_runner.run,
            mode=req.mode,
            category=req.category,
            case_id=req.case_id,
            persist=True
        )
        return {
            "status": "STARTED_BACKGROUND",
            "message": f"Evaluation initiated in background (mode={req.mode})."
        }

    # Synchronous run
    result = await evaluation_runner.run(
        mode=req.mode,
        category=req.category,
        case_id=req.case_id,
        persist=True
    )
    return result


@router.post("/run/{case_id}")
async def run_single_case(case_id: str):
    """Runs evaluation for a single case synchronously and returns detailed result."""
    result = await evaluation_runner.run(
        mode="single",
        case_id=case_id,
        persist=False
    )
    results_list = result.get("results", [])
    if results_list:
        return results_list[0]
    raise HTTPException(status_code=404, detail=f"Case {case_id} could not be evaluated.")


def _format_case_item(
    case_id: str,
    title: str,
    category: str,
    status_str: str,
    workflow_score: float,
    execution_time: float,
    expected_data: Dict[str, Any],
    actual_data: Dict[str, Any],
    failure_reason: Optional[str] = None,
    society: Optional[str] = None,
    trace_events: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """Helper to format uniform EvaluationResultItem matching the frontend TypeScript interface."""
    exp = expected_data or {}
    act = actual_data or {}
    is_failed = status_str.upper() == "FAILED"

    return {
        "case_id": case_id,
        "title": title,
        "category": category,
        "status": status_str.upper(),
        "workflow_score": workflow_score,
        "execution_time_seconds": execution_time,
        "expected_risk_level": exp.get("risk_level"),
        "expected_hitl": exp.get("hitl"),
        "expected_compliance": exp.get("compliance", []),
        "expected_societies": exp.get("societies", []),
        "actual_risk_level": act.get("risk_level"),
        "actual_risk_score": act.get("risk_score"),
        "actual_hitl": act.get("hitl"),
        "actual_compliance": act.get("compliance", []),
        "actual_societies": act.get("societies", []),
        "failure_reason": failure_reason,
        "society": society or "cas_director",
        "failure_record": {
            "case_id": case_id,
            "status": status_str.upper(),
            "category": category,
            "expected": f"Risk: {str(exp.get('risk_level', '')).upper()} | HITL: {'YES' if exp.get('hitl') else 'NO'}",
            "actual": f"Risk: {str(act.get('risk_level', '')).upper()} | HITL: {'YES' if act.get('hitl') else 'NO'}",
            "failure_reason": failure_reason or "Expectation mismatch",
            "society": society or "cas_director"
        } if is_failed else None,
        "execution_events": trace_events or [],
        "execution_trace": trace_events or []
    }


@router.get("/results")
async def get_evaluation_results(
    run_id: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns case-by-case evaluation results for the latest or selected run.
    Guarantees flat fields for risk, HITL, societies, failure record, and execution trace.
    """
    await ensure_baseline_seeded(db)

    # 1. Query database if specific run requested or no in-memory results
    if run_id or not evaluation_runner.latest_case_results:
        target_run_id = run_id
        if not target_run_id:
            stmt = select(EvaluationRunModel.run_id).order_by(desc(EvaluationRunModel.created_at)).limit(1)
            target_run_id = (await db.execute(stmt)).scalars().first()

        if target_run_id:
            c_stmt = select(EvaluationCaseResultModel).where(EvaluationCaseResultModel.run_id == target_run_id)
            if category and category.lower() != "all":
                c_stmt = c_stmt.where(EvaluationCaseResultModel.category == category)
            if status_filter and status_filter.lower() != "all":
                c_stmt = c_stmt.where(EvaluationCaseResultModel.status == status_filter.upper())

            case_recs = (await db.execute(c_stmt)).scalars().all()
            if case_recs:
                return [
                    _format_case_item(
                        case_id=r.case_id,
                        title=r.title,
                        category=r.category,
                        status_str=r.status,
                        workflow_score=r.workflow_score,
                        execution_time=r.execution_time_seconds,
                        expected_data=r.expected_json,
                        actual_data=r.actual_json,
                        failure_reason=r.failure_reason,
                        society=r.society,
                        trace_events=r.execution_trace_json
                    )
                    for r in case_recs
                ]

        # Fallback to baseline benchmark data file
        data = load_baseline_run_data()
        if data and data.get("results"):
            items = [
                _format_case_item(
                    case_id=r.get("case_id"),
                    title=r.get("title"),
                    category=r.get("category"),
                    status_str=r.get("status", "PASSED"),
                    workflow_score=r.get("workflow_score", 100.0),
                    execution_time=r.get("execution_time_seconds", 0.0),
                    expected_data=r.get("expected_json", {}),
                    actual_data=r.get("actual_json", {}),
                    failure_reason=r.get("failure_reason"),
                    society=r.get("society"),
                    trace_events=r.get("execution_trace_json", [])
                )
                for r in data.get("results", [])
            ]
            if category and category.lower() != "all":
                items = [r for r in items if r.get("category", "").lower() == category.lower()]
            if status_filter and status_filter.lower() != "all":
                items = [r for r in items if r.get("status", "").upper() == status_filter.upper()]
            return items

        return []

    # In-memory results
    res = evaluation_runner.latest_case_results
    if category and category.lower() != "all":
        res = [r for r in res if r.get("category", "").lower() == category.lower()]
    if status_filter and status_filter.lower() != "all":
        res = [r for r in res if r.get("status", "").upper() == status_filter.upper()]

    return res


@router.get("/failures")
async def get_evaluation_failures(
    run_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Returns structured failure records grouped by error category."""
    results = await get_evaluation_results(run_id=run_id, status_filter="FAILED", db=db)
    failures = []
    for r in results:
        f_rec = r.get("failure_record") or {
            "case_id": r.get("case_id"),
            "status": "FAILED",
            "category": r.get("category"),
            "expected": str(r.get("expected_risk_level")),
            "actual": str(r.get("actual_risk_level")),
            "failure_reason": r.get("failure_reason") or "Expectation mismatch",
            "society": r.get("society") or "cas_director"
        }
        failures.append(f_rec)

    # Group by failure society/category
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for f in failures:
        soc = f.get("society", "cas_director")
        if soc not in grouped:
            grouped[soc] = []
        grouped[soc].append(f)

    return {
        "total_failures": len(failures),
        "failures": failures,
        "grouped_by_society": grouped
    }


@router.get("/runs")
async def list_evaluation_runs(db: AsyncSession = Depends(get_db)):
    """Lists historical evaluation runs for audit and reproducibility."""
    await ensure_baseline_seeded(db)
    stmt = select(EvaluationRunModel).order_by(desc(EvaluationRunModel.created_at)).limit(20)
    recs = (await db.execute(stmt)).scalars().all()
    runs = []
    for r in recs:
        runs.append({
            "run_id": r.run_id,
            "run_number": r.run_number,
            "dataset_version": r.dataset_version,
            "total_cases": r.number_of_cases,
            "passed": r.passed,
            "failed": r.failed,
            "accuracy": r.metrics_json.get("end_to_end_accuracy", 0.0),
            "workflow_score": r.metrics_json.get("workflow_accuracy", 0.0),
            "risk_f1": r.metrics_json.get("risk_f1", 0.0),
            "hitl_accuracy": r.metrics_json.get("hitl_accuracy", 0.0),
            "model_provider": r.model_provider,
            "duration_seconds": r.duration_seconds,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    if not runs:
        data = load_baseline_run_data()
        if data:
            metrics = data.get("metrics_json", {})
            runs.append({
                "run_id": data.get("run_id", "RUN-BASELINE"),
                "run_number": data.get("run_number", 1),
                "dataset_version": data.get("dataset_version", "1.0.0"),
                "total_cases": data.get("number_of_cases", len(data.get("results", []))),
                "passed": data.get("passed", 35),
                "failed": data.get("failed", 15),
                "accuracy": metrics.get("end_to_end_accuracy", 0.70),
                "workflow_score": metrics.get("workflow_accuracy", 0.829),
                "risk_f1": metrics.get("risk_f1", 0.806),
                "hitl_accuracy": metrics.get("hitl_accuracy", 0.76),
                "model_provider": data.get("model_provider", "Google Gemini API"),
                "duration_seconds": data.get("duration_seconds", 0.0),
                "created_at": None
            })
    return runs


@router.get("/runs/{run_id}")
async def get_evaluation_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full details and scorecard for a specific historical evaluation run."""
    await ensure_baseline_seeded(db)
    stmt = select(EvaluationRunModel).where(EvaluationRunModel.run_id == run_id)
    run_rec = (await db.execute(stmt)).scalars().first()
    if run_rec:
        cases = await get_evaluation_results(run_id=run_id, db=db)
        return {
            "run_id": run_rec.run_id,
            "run_number": run_rec.run_number,
            "created_at": run_rec.created_at.isoformat() if run_rec.created_at else None,
            "metrics": run_rec.metrics_json,
            "cases": cases
        }

    data = load_baseline_run_data()
    if data and data.get("run_id") == run_id:
        cases = await get_evaluation_results(run_id=run_id, db=db)
        return {
            "run_id": data.get("run_id"),
            "run_number": data.get("run_number", 1),
            "created_at": data.get("metrics_json", {}).get("timestamp"),
            "metrics": data.get("metrics_json", {}),
            "cases": cases
        }

    raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
