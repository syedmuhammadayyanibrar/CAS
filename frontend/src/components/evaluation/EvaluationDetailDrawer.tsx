import React, { useEffect } from "react";
import { X, CheckCircle2, XCircle, Clock, FileText } from "lucide-react";
import { EvaluationCase } from "../../api/client";
import { WorkflowComparison } from "./WorkflowComparison";

interface EvaluationDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  evaluationCase: EvaluationCase | null;
}

export function EvaluationDetailDrawer({
  isOpen,
  onClose,
  evaluationCase,
}: EvaluationDetailDrawerProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !evaluationCase) return null;

  const isPassed = evaluationCase.status === "PASSED";

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/30 backdrop-blur-xs transition-opacity cursor-pointer"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-2xl bg-white border-l border-[#E5E7EB] shadow-2xl flex flex-col h-full z-10 text-slate-800 animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-5 border-b border-[#E5E7EB] flex items-start justify-between gap-4 bg-slate-50/80">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-slate-500">
                {evaluationCase.case_id}
              </span>
              <span className="text-slate-300">•</span>
              <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {evaluationCase.category}
              </span>
              <span className="text-slate-300">•</span>
              <span
                className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                  isPassed
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-rose-100 text-rose-800"
                }`}
              >
                {evaluationCase.status}
              </span>
            </div>
            <h2 className="text-base font-bold text-[#111827]">
              {evaluationCase.scenario}
            </h2>
            <div className="text-xs text-slate-500 font-mono">
              Contract Ref: {evaluationCase.contract_id} · Latency: {evaluationCase.execution_time_ms}ms
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Visual Workflow Path Comparison */}
          <WorkflowComparison evaluationCase={evaluationCase} />

          {/* Expected vs Actual Ground Truth Assertions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Expected Values */}
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-800 uppercase tracking-wider font-mono">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Expected Ground Truth</span>
              </div>
              <pre className="text-xs font-mono bg-white p-3 rounded border border-slate-200 text-slate-800 overflow-x-auto">
                {JSON.stringify(evaluationCase.expected, null, 2)}
              </pre>
            </div>

            {/* Actual Output */}
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider font-mono">
                {isPassed ? (
                  <span className="text-emerald-800 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Actual Model Output</span>
                  </span>
                ) : (
                  <span className="text-rose-800 flex items-center gap-1.5">
                    <XCircle className="w-3.5 h-3.5 text-rose-600" />
                    <span>Actual Model Output (Diverged)</span>
                  </span>
                )}
              </div>
              <pre
                className={`text-xs font-mono p-3 rounded border overflow-x-auto ${
                  isPassed
                    ? "bg-white border-slate-200 text-slate-800"
                    : "bg-rose-50/60 border-rose-200 text-rose-950 font-semibold"
                }`}
              >
                {JSON.stringify(evaluationCase.actual, null, 2)}
              </pre>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#E5E7EB] bg-slate-50/80 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-md bg-white border border-slate-300 hover:bg-slate-100 text-xs text-slate-700 font-medium transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
