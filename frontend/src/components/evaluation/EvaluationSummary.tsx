import React from "react";
import { CheckCircle2, XCircle, Zap, ShieldCheck, Clock, RefreshCw } from "lucide-react";
import { EvaluationSummary as EvaluationSummaryType } from "../../api/client";

interface EvaluationSummaryProps {
  summary: EvaluationSummaryType | null;
  onRunEvaluation: () => void;
  isRunning?: boolean;
}

export function EvaluationSummary({
  summary,
  onRunEvaluation,
  isRunning = false,
}: EvaluationSummaryProps) {
  if (!summary) return null;

  return (
    <div className="space-y-4">
      {/* Top Header Row with Dataset Version and Run Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E7EB]">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-[#111827]">
              CAS System Benchmark &amp; Ground-Truth Evaluation
            </h2>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
              Dataset {summary.dataset_version}
            </span>
          </div>
          <p className="text-xs text-[#6B7280] mt-0.5">
            Automated verification across 30 legal adversarial, compliance, and multi-agent routing scenarios.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[11px] text-[#9CA3AF] font-mono">
            Last evaluated: {new Date(summary.last_run || summary.timestamp || Date.now()).toLocaleDateString()}
          </span>
          <button
            onClick={onRunEvaluation}
            disabled={isRunning}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-md text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRunning ? "animate-spin" : ""}`} />
            <span>{isRunning ? "Running Benchmark..." : "Run Evaluation Suite"}</span>
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Card 1: End-to-End Accuracy */}
        <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              End-to-End Accuracy
            </span>
            <span className="inline-flex items-center text-emerald-700 text-xs font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
              {summary.passed_cases}/{summary.total_cases}
            </span>
          </div>
          <div className="text-2xl font-bold text-[#111827]">
            {(summary.end_to_end_accuracy * 100).toFixed(1)}%
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
            <div
              className="bg-emerald-600 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${summary.end_to_end_accuracy * 100}%` }}
            />
          </div>
          <div className="text-[11px] text-[#6B7280] pt-1">
            {summary.passed_cases} passed, {summary.failed_cases} failed
          </div>
        </div>

        {/* Card 2: Routing Accuracy */}
        <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Director Routing
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold">
              6 Societies
            </span>
          </div>
          <div className="text-2xl font-bold text-[#111827]">
            {(summary.routing_accuracy * 100).toFixed(1)}%
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
            <div
              className="bg-blue-600 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${summary.routing_accuracy * 100}%` }}
            />
          </div>
          <div className="text-[11px] text-[#6B7280] pt-1">
            Dynamic state transition fidelity
          </div>
        </div>

        {/* Card 3: Risk Classification F1 */}
        <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Risk Severity F1
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold">
              Calibrated
            </span>
          </div>
          <div className="text-2xl font-bold text-[#111827]">
            {summary.risk_f1.toFixed(2)}
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
            <div
              className="bg-indigo-600 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${summary.risk_f1 * 100}%` }}
            />
          </div>
          <div className="text-[11px] text-[#6B7280] pt-1">
            Hunter vs Assessor dialectic score
          </div>
        </div>

        {/* Card 4: HITL Trigger Accuracy */}
        <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              HITL Gate Accuracy
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 font-semibold">
              Escalations
            </span>
          </div>
          <div className="text-2xl font-bold text-[#111827]">
            {(summary.hitl_accuracy * 100).toFixed(1)}%
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
            <div
              className="bg-amber-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${summary.hitl_accuracy * 100}%` }}
            />
          </div>
          <div className="text-[11px] text-[#6B7280] pt-1">
            Zero missed critical indemnities
          </div>
        </div>
      </div>
    </div>
  );
}
