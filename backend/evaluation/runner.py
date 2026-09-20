import os
import json
import time
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from backend.core.logging import get_logger
from backend.core.config import settings
from backend.database.db import AsyncSessionLocal, init_db
from backend.database.schema import EvaluationRunModel, EvaluationCaseResultModel
from backend.director.coordinator import cas_director
from backend.director.execution_tracker import execution_tracker
try:
    from backend.evaluation.evaluator import CaseEvaluator
    from backend.evaluation.metrics import EvaluationMetricsCalculator
except ImportError:
    from evaluation.evaluator import CaseEvaluator
    from evaluation.metrics import EvaluationMetricsCalculator
from sqlalchemy import select, desc

logger = get_logger("EvaluationRunner")

DATASET_DIR = os.path.join(os.path.dirname(__file__), "datasets")


class EvaluationRunner:
    """
    Executes contract cases, adversarial tests, and routing scenarios through
    the real CAS pipeline, recording complete execution traces and persistent benchmarks.
    """

    def __init__(self):
        self.latest_run_summary: Optional[Dict[str, Any]] = None
        self.latest_case_results: List[Dict[str, Any]] = []
        self.is_running: bool = False
        self.current_case_id: Optional[str] = None
        self.progress_percent: float = 0.0

    @staticmethod
    def load_all_cases() -> List[Dict[str, Any]]:
        """Loads all evaluation cases across contract, adversarial, and routing datasets."""
        cases = []
        paths = [
            os.path.join(DATASET_DIR, "contract_cases.json"),
            os.path.join(DATASET_DIR, "adversarial_cases.json"),
            os.path.join(DATASET_DIR, "routing_cases.json"),
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            cases.extend(data)
                except Exception as e:
                    logger.error(f"Failed to load dataset {p}: {e}")
        return cases

    @staticmethod
    def get_case_by_id(case_id: str) -> Optional[Dict[str, Any]]:
        all_cases = EvaluationRunner.load_all_cases()
        for c in all_cases:
            if c.get("case_id") == case_id:
                return c
        return None

    async def run(
        self,
        mode: str = "all",
        category: Optional[str] = None,
        case_id: Optional[str] = None,
        persist: bool = True
    ) -> Dict[str, Any]:
        """
        Executes the evaluation suite based on the specified mode.
        Modes: 'all', 'failed', 'category', 'single'
        """
        if self.is_running:
            logger.warning("Evaluation run is already in progress.")
            return {"status": "ALREADY_RUNNING", "message": "An evaluation run is currently active."}

        self.is_running = True
        self.progress_percent = 0.0
        start_time = time.time()
        run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

        try:
            all_cases = self.load_all_cases()

            # Filter cases based on mode
            if mode == "single" and case_id:
                cases_to_run = [c for c in all_cases if c.get("case_id") == case_id]
            elif mode == "category" and category:
                cases_to_run = [c for c in all_cases if c.get("category", "").lower() == category.lower()]
            elif mode == "failed":
                failed_ids = {r.get("case_id") for r in self.latest_case_results if r.get("status") == "FAILED"}
                cases_to_run = [c for c in all_cases if c.get("case_id") in failed_ids]
                if not cases_to_run:
                    cases_to_run = all_cases  # If no prior failed records, run all
            else:
                cases_to_run = all_cases

            total_cases = len(cases_to_run)
            logger.info(f"Starting Evaluation Run {run_id} with {total_cases} cases (mode={mode})...")

            results = []
            for idx, c in enumerate(cases_to_run):
                self.current_case_id = c.get("case_id")
                self.progress_percent = round(((idx) / total_cases) * 100.0, 1)

                case_res = await self._execute_single_case(c)
                results.append(case_res)

            self.progress_percent = 100.0
            duration = round(time.time() - start_time, 2)

            # Compute aggregated scorecard
            summary = EvaluationMetricsCalculator.aggregate_case_results(results)
            summary["run_id"] = run_id
            summary["timestamp"] = datetime.now(timezone.utc).isoformat()
            summary["duration_seconds"] = duration
            summary["dataset_version"] = "1.0.0"
            summary["model_provider"] = "Google Gemini 2.5 Flash (Sole Provider)" if settings.GEMINI_API_KEY else "Google Gemini API (Deterministic Evaluation Mode)"
            summary["cas_version"] = settings.VERSION

            # Update in-memory state
            self.latest_run_summary = summary
            self.latest_case_results = results

            # Persist run to database if requested
            if persist:
                await self._persist_run(run_id, summary, results)

            logger.info(f"Evaluation Run {run_id} complete in {duration}s. Passed: {summary['passed']}/{summary['total_cases']} (E2E Accuracy: {summary['end_to_end_accuracy']*100:.1f}%)")

            return {
                "summary": summary,
                "results": results
            }

        finally:
            self.is_running = False
            self.current_case_id = None

    async def _execute_single_case(self, case_def: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a case through the genuine CAS pipeline and returns its evaluation record."""
        cid = case_def.get("case_id", "CTR-EVAL")
        cat = case_def.get("category", "normal")
        case_start = time.time()

        if cat == "routing":
            # Director routing test
            input_evt = case_def.get("input_event", {})
            evt_type = input_evt.get("event_type", "CONTRACT_INTAKE")
            payload = input_evt.get("payload", {})

            if evt_type in ("APPROVAL_DECISION", "COUNTERPARTY_PROPOSAL", "DEADLINE_CHANGE"):
                routing_res = await cas_director.handle_inbound_fastn_event(
                    payload=payload,
                    event_type=evt_type,
                    event_id=f"EVT-{cid}"
                )
            else:
                from backend.director.lifecycle import ContractLifecycleState
                lifecycle_str = input_evt.get("lifecycle_state", "ANALYZING")
                try:
                    l_state = ContractLifecycleState(lifecycle_str)
                except Exception:
                    l_state = ContractLifecycleState.ANALYZING
                routing_decision = cas_director.determine_routing(
                    event_type=evt_type,
                    lifecycle_state=l_state
                )
                routing_res = {
                    "selected_societies": routing_decision.selected_societies,
                    "rationale": routing_decision.rationale,
                    "status": "PROCESSED",
                    "hitl_required": "risk_intelligence" in routing_decision.selected_societies and input_evt.get("payload", {}).get("severity") == "CRITICAL"
                }

            duration = time.time() - case_start
            return CaseEvaluator.evaluate_routing_case(case_def, routing_res, duration_seconds=duration)

        else:
            # End-to-end Contract mesh execution
            contract_text = case_def.get("contract_text", "")
            eval_contract_id = f"EVAL-{cid}"

            try:
                mesh_output = await cas_director.orchestrate_mesh(
                    contract_text=contract_text,
                    contract_id=eval_contract_id,
                    commercial_objective="Protect Customer liability and ensure bilateral commercial terms."
                )

                # Fetch real ExecutionTracker events
                exec_state = execution_tracker.get_execution(eval_contract_id)
                events = exec_state.get("events", []) if exec_state else []

                duration = time.time() - case_start
                return CaseEvaluator.evaluate_contract_case(
                    case_def=case_def,
                    actual_output=mesh_output,
                    execution_events=events,
                    duration_seconds=duration
                )
            except Exception as e:
                logger.error(f"Execution failed for case {cid}: {e}")
                duration = time.time() - case_start
                return {
                    "case_id": cid,
                    "title": case_def.get("title", cid),
                    "category": cat,
                    "status": "FAILED",
                    "workflow_score": 0.0,
                    "execution_time_seconds": round(duration, 2),
                    "expected_risk_level": case_def.get("expected", {}).get("risk_level", "low"),
                    "actual_risk_level": "unknown",
                    "hitl_correct": False,
                    "routing_correct": False,
                    "expected_societies": case_def.get("expected", {}).get("expected_societies", []),
                    "actual_societies": [],
                    "missing_steps": [f"Pipeline execution crashed: {str(e)}"],
                    "failure_record": {
                        "case_id": cid,
                        "status": "FAILED",
                        "category": cat,
                        "expected": "Normal execution",
                        "actual": "Crash / Exception",
                        "failure_reason": str(e),
                        "society": "cas_director"
                    },
                    "execution_events": []
                }

    async def _persist_run(self, run_id: str, summary: Dict[str, Any], results: List[Dict[str, Any]]):
        """Persists the evaluation run and case records in PostgreSQL/SQLite."""
        try:
            await init_db()
            async with AsyncSessionLocal() as session:
                # Determine run number
                stmt = select(EvaluationRunModel).order_by(desc(EvaluationRunModel.run_number)).limit(1)
                last_run = (await session.execute(stmt)).scalars().first()
                run_num = (last_run.run_number + 1) if last_run else 1

                run_rec = EvaluationRunModel(
                    run_id=run_id,
                    run_number=run_num,
                    dataset_version=summary.get("dataset_version", "1.0.0"),
                    number_of_cases=summary.get("total_cases", 0),
                    passed=summary.get("passed", 0),
                    failed=summary.get("failed", 0),
                    metrics_json=summary,
                    model_provider=summary.get("model_provider", "Google Gemini"),
                    cas_version=summary.get("cas_version", "1.0.0"),
                    duration_seconds=summary.get("duration_seconds", 0.0)
                )
                session.add(run_rec)

                for r in results:
                    case_rec = EvaluationCaseResultModel(
                        run_id=run_id,
                        case_id=r.get("case_id", "UNKNOWN"),
                        title=r.get("title", ""),
                        category=r.get("category", "normal"),
                        status=r.get("status", "PASSED"),
                        expected_json={
                            "risk_level": r.get("expected_risk_level"),
                            "hitl": r.get("expected_hitl"),
                            "compliance": r.get("expected_compliance"),
                            "societies": r.get("expected_societies"),
                        },
                        actual_json={
                            "risk_level": r.get("actual_risk_level"),
                            "risk_score": r.get("actual_risk_score"),
                            "hitl": r.get("actual_hitl"),
                            "compliance": r.get("actual_compliance"),
                            "societies": r.get("actual_societies"),
                        },
                        failure_reason=r.get("failure_record", {}).get("failure_reason") if r.get("failure_record") else None,
                        society=r.get("failure_record", {}).get("society") if r.get("failure_record") else None,
                        workflow_score=r.get("workflow_score", 100.0),
                        execution_time_seconds=r.get("execution_time_seconds", 0.0),
                        execution_trace_json=r.get("execution_events", [])
                    )
                    session.add(case_rec)

                await session.commit()
                logger.info(f"Successfully persisted Evaluation Run #{run_num} ({run_id}) to database.")
        except Exception as e:
            logger.error(f"Failed to persist evaluation run to database: {e}")


evaluation_runner = EvaluationRunner()
