import React from "react";
import { ArrowRight, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { EvaluationCase } from "../../api/client";

interface WorkflowComparisonProps {
  evaluationCase: EvaluationCase;
}

export function WorkflowComparison({ evaluationCase }: WorkflowComparisonProps) {
  const isPassed = evaluationCase.status === "PASSED";
  const expectedSteps = evaluationCase.expected_workflow || [];
  const actualSteps = evaluationCase.actual_workflow || [];
  const divergenceStep = evaluationCase.divergence_step;

  return (
    <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
          Workflow Path &amp; Execution Step Comparison
        </h4>
        <span
          className={`text-xs font-mono font-semibold px-2 py-0.5 rounded ${
            isPassed
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
              : "bg-rose-50 text-rose-700 border border-rose-200"
          }`}
        >
          {isPassed ? "Workflow Matched" : "Workflow Diverged"}
        </span>
      </div>

      {/* Side-by-side or stacked workflow trajectories */}
      <div className="space-y-3">
        {/* 1. Expected Workflow */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Expected Trajectory (Ground Truth)</span>
          </div>
          <div className="flex flex-wrap items-center gap-1.5 p-3 rounded-lg bg-slate-50 border border-slate-200">
            {expectedSteps.map((step: string, idx: number) => (
              <React.Fragment key={idx}>
                <div className="px-2.5 py-1 rounded bg-white border border-slate-300 text-xs font-medium text-slate-800 shadow-2xs">
                  <span className="text-[10px] font-mono text-slate-400 mr-1.5">
                    {idx + 1}.
                  </span>
                  {step}
                </div>
                {idx < expectedSteps.length - 1 && (
                  <ArrowRight className="w-3 h-3 text-slate-400 shrink-0" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* 2. Actual Workflow */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
            {isPassed ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            ) : (
              <XCircle className="w-3.5 h-3.5 text-rose-600" />
            )}
            <span>Actual Execution Trajectory</span>
          </div>
          <div
            className={`flex flex-wrap items-center gap-1.5 p-3 rounded-lg border ${
              isPassed
                ? "bg-emerald-50/40 border-emerald-200"
                : "bg-rose-50/40 border-rose-200"
            }`}
          >
            {actualSteps.map((step: string, idx: number) => {
              const isDivergence = step === divergenceStep;

              return (
                <React.Fragment key={idx}>
                  <div
                    className={`px-2.5 py-1 rounded text-xs font-medium shadow-2xs ${
                      isDivergence
                        ? "bg-rose-600 text-white font-bold ring-2 ring-rose-400"
                        : "bg-white border border-slate-300 text-slate-800"
                    }`}
                  >
                    <span
                      className={`text-[10px] font-mono mr-1.5 ${
                        isDivergence ? "text-rose-100" : "text-slate-400"
                      }`}
                    >
                      {idx + 1}.
                    </span>
                    {step}
                    {isDivergence && " (Divergence Point)"}
                  </div>
                  {idx < actualSteps.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-slate-400 shrink-0" />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. Divergence Analysis / Failure Diagnostic */}
      {evaluationCase.failure_analysis && (
        <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-300 text-amber-900 text-xs space-y-1">
          <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[10px] text-amber-800">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Root Cause &amp; Divergence Analysis</span>
          </div>
          <p className="text-xs text-amber-900 leading-relaxed font-mono">
            {evaluationCase.failure_analysis}
          </p>
        </div>
      )}
    </div>
  );
}
