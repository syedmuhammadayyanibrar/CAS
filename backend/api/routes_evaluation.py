import asyncio
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.core.logging import get_logger
from backend.database.db import get_db
from backend.database.schema import EvaluationRunModel, EvaluationCaseResultModel
try:
    from backend.evaluation.runner import evaluation_runner, EvaluationRunner
except ImportError:
    from evaluation.runner import evaluation_runner, EvaluationRunner

logger = get_logger("RoutesEvaluation")
router = APIRouter(prefix="/evaluation", tags=["CAS Evaluation Center"])


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
    Loads from latest in-memory run or latest database record.
    """
    # If specific run_id requested, fetch from DB
    if run_id:
        stmt = select(EvaluationRunModel).where(EvaluationRunModel.run_id == run_id)
        run_rec = (await db.execute(stmt)).scalars().first()
        if not run_rec:
            raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")
        return run_rec.metrics_json

    # Check in-memory runner first
    if evaluation_runner.latest_run_summary:
        return evaluation_runner.latest_run_summary

    # Otherwise fetch latest run from DB
    stmt = select(EvaluationRunModel).order_by(desc(EvaluationRunModel.created_at)).limit(1)
    latest_db_run = (await db.execute(stmt)).scalars().first()
    if latest_db_run:
        return latest_db_run.metrics_json

    # Fallback to empty clean initial summary
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
    if category:
        cases = [c for c in cases if c.get("category", "").lower() == category.lower()]

    # Format for UI table listing
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


@router.get("/results")
async def get_evaluation_results(
    run_id: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns case-by-case evaluation results for the latest or selected run.
    """
    # If run_id specified or no in-memory results, query database
    if run_id or not evaluation_runner.latest_case_results:
        target_run_id = run_id
        if not target_run_id:
            stmt = select(EvaluationRunModel.run_id).order_by(desc(EvaluationRunModel.created_at)).limit(1)
            target_run_id = (await db.execute(stmt)).scalars().first()

        if not target_run_id:
            return []

        c_stmt = select(EvaluationCaseResultModel).where(EvaluationCaseResultModel.run_id == target_run_id)
        if category:
            c_stmt = c_stmt.where(EvaluationCaseResultModel.category == category)
        if status_filter:
            c_stmt = c_stmt.where(EvaluationCaseResultModel.status == status_filter.upper())

        case_recs = (await db.execute(c_stmt)).scalars().all()
        return [
            {
                "case_id": r.case_id,
                "title": r.title,
                "category": r.category,
                "status": r.status,
                "expected": r.expected_json,
                "actual": r.actual_json,
                "failure_reason": r.failure_reason,
                "society": r.society,
                "workflow_score": r.workflow_score,
                "execution_time_seconds": r.execution_time_seconds,
                "execution_trace": r.execution_trace_json
            }
            for r in case_recs
        ]

    # In-memory results
    res = evaluation_runner.latest_case_results
    if category:
        res = [r for r in res if r.get("category", "").lower() == category.lower()]
    if status_filter:
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
            "expected": str(r.get("expected")),
            "actual": str(r.get("actual")),
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
    return runs


@router.get("/runs/{run_id}")
async def get_evaluation_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full details and scorecard for a specific historical evaluation run."""
    stmt = select(EvaluationRunModel).where(EvaluationRunModel.run_id == run_id)
    run_rec = (await db.execute(stmt)).scalars().first()
    if not run_rec:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    cases = await get_evaluation_results(run_id=run_id, db=db)
    return {
        "run_id": run_rec.run_id,
        "run_number": run_rec.run_number,
        "created_at": run_rec.created_at.isoformat() if run_rec.created_at else None,
        "metrics": run_rec.metrics_json,
        "cases": cases
    }
