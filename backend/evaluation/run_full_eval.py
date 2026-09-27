import os
import sys
import asyncio
import json

sys.path.insert(0, os.path.abspath("."))
os.environ["TESTING"] = "1"
from backend.evaluation.runner import EvaluationRunner

async def main():
    runner = EvaluationRunner()
    result = await runner.run(mode="all", persist=True)
    summary = result.get("summary", {})
    print("=== BENCHMARK SUITE RESULTS ===")
    print("Total Cases:", summary.get("total_cases"))
    print("Passed:", summary.get("passed"))
    print("Failed:", summary.get("failed"))
    print("Accuracy:", f"{summary.get('end_to_end_accuracy', 0.0) * 100:.1f}%")
    print("Workflow Score:", f"{summary.get('overall_workflow_score', 0.0):.1f}")
    print("HITL Accuracy:", f"{summary.get('hitl_accuracy', 0.0) * 100:.1f}%")
    print("Routing Accuracy:", f"{summary.get('routing_accuracy', 0.0) * 100:.1f}%")
    
    failed_cases = [r for r in result.get("results", []) if r.get("status") == "FAILED"]
    if failed_cases:
        print("\nFailed cases count:", len(failed_cases))
        for fc in failed_cases:
            print(f"  - {fc.get('case_id')}: {fc.get('failure_record')}")
    else:
        print("\nALL 50 CASES PASSED WITH 100% ACCURACY!")
        
        # Save baseline dataset for cold start and initial display
        formatted_results = []
        for r in result.get("results", []):
            formatted_results.append({
                "case_id": r.get("case_id", "UNKNOWN"),
                "title": r.get("title", ""),
                "category": r.get("category", "normal"),
                "status": r.get("status", "PASSED"),
                "workflow_score": r.get("workflow_score", 100.0),
                "expected_json": r.get("expected", {}),
                "actual_json": r.get("actual", {}),
                "failure_reason": r.get("failure_record", {}).get("failure_reason") if r.get("failure_record") else None,
                "society": r.get("failure_record", {}).get("society") if r.get("failure_record") else None,
                "execution_time_seconds": r.get("execution_time_seconds", 0.0),
                "execution_trace_json": r.get("execution_events", []),
            })

        baseline_data = {
            "run_id": summary.get("run_id"),
            "run_number": 1,
            "dataset_version": summary.get("dataset_version", "1.0.0"),
            "number_of_cases": summary.get("total_cases", len(formatted_results)),
            "passed": summary.get("passed", 50),
            "failed": summary.get("failed", 0),
            "metrics_json": summary,
            "model_provider": summary.get("model_provider", "Google Gemini 2.5 Flash (Sole Provider)"),
            "cas_version": summary.get("cas_version", "1.0.0"),
            "duration_seconds": summary.get("duration_seconds", 0.0),
            "results": formatted_results
        }
        for dest in ["backend/evaluation/datasets/baseline_benchmark.json", "evaluation/datasets/baseline_benchmark.json"]:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(baseline_data, f, indent=2)
            print(f"Updated baseline benchmark at: {dest}")

if __name__ == "__main__":
    asyncio.run(main())

