import React from "react";
import { AlertTriangle, CheckCircle2, Clock, Play, ArrowRight } from "lucide-react";
import { ContractExecutionState } from "../../api/client";

interface JourneyStatusProps {
  execution: ContractExecutionState | null;
  elapsedSeconds: number;
  currentMilestoneTitle: string;
  onReviewDecision?: () => void;
}

export function JourneyStatus({
  execution,
  elapsedSeconds,
  currentMilestoneTitle,
  onReviewDecision,
}: JourneyStatusProps) {
  if (!execution) {
    return (
      <div className="flex items-center justify-between p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500">
        <span>No active contract execution session</span>
        <span className="text-[11px] font-mono">Idle</span>
      </div>
    );
  }

  const isCompleted = execution.status === "COMPLETED";
  const isRunning = execution.status === "RUNNING";
  const isPaused =
    execution.status === "PAUSED_FOR_HUMAN" ||
    execution.stages.some((s) => s.status === "PAUSED_FOR_HUMAN");
  const isFailed = execution.status === "FAILED";

  const getStatusText = () => {
    if (isCompleted) return "Contract Orchestration Complete";
    if (isPaused) return "Human Review Required — Orchestration Paused";
    if (isFailed) return "Execution Stopped with Errors";
    if (isRunning) {
      if (execution.current_step?.society && execution.current_step?.agent) {
        return `Executing: ${execution.current_step.society} → ${execution.current_step.agent}`;
      }
      return `Processing Stage: ${currentMilestoneTitle}`;
    }
    return "Ready for Orchestration";
  };

  return (
    <div
      className={`p-4 rounded-lg border transition-all ${
        isPaused
          ? "bg-amber-50/70 border-amber-300 text-amber-900"
          : isCompleted
          ? "bg-emerald-50/60 border-emerald-300 text-emerald-900"
          : isFailed
          ? "bg-rose-50/60 border-rose-300 text-rose-900"
          : isRunning
          ? "bg-blue-50/60 border-blue-200 text-blue-950"
          : "bg-white border-slate-200 text-slate-800"
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-start sm:items-center gap-3">
          <div className="shrink-0 mt-0.5 sm:mt-0">
            {isCompleted && (
              <div className="w-8 h-8 rounded-lg bg-emerald-100 border border-emerald-300 flex items-center justify-center text-emerald-700">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            )}
            {isRunning && (
              <div className="w-8 h-8 rounded-lg bg-blue-100 border border-blue-300 flex items-center justify-center text-blue-700">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-pulse" />
              </div>
            )}
            {isPaused && (
              <div className="w-8 h-8 rounded-lg bg-amber-100 border border-amber-300 flex items-center justify-center text-amber-800 animate-bounce">
                <AlertTriangle className="w-4 h-4" />
              </div>
            )}
            {isFailed && (
              <div className="w-8 h-8 rounded-lg bg-rose-100 border border-rose-300 flex items-center justify-center text-rose-700">
                <AlertTriangle className="w-4 h-4" />
              </div>
            )}
            {!isCompleted && !isRunning && !isPaused && !isFailed && (
              <div className="w-8 h-8 rounded-lg bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-500">
                <Clock className="w-4 h-4" />
              </div>
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
                {isPaused ? "HITL GATE" : "STAGE"}
              </span>
              <span className="text-slate-300">•</span>
              <span className="text-sm font-semibold text-slate-900">
                {getStatusText()}
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-0.5 leading-snug">
              {execution.current_step?.task ||
                (isCompleted
                  ? "All societies completed synthesis, risk audit, and obligation extraction."
                  : isPaused
                  ? "Critical indemnity or high liability clause flagged. Explicit General Counsel sign-off required."
                  : "Awaiting execution trigger.")}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
          {isRunning && (
            <span className="px-2.5 py-1 rounded bg-blue-100/80 border border-blue-200 text-blue-800 text-xs font-mono font-medium">
              Elapsed: {elapsedSeconds}s
            </span>
          )}

          {isPaused && onReviewDecision && (
            <button
              onClick={onReviewDecision}
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-md text-xs font-semibold shadow-xs transition-colors cursor-pointer"
            >
              <span>Review Decision</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}

          <span
            className={`px-2.5 py-1 rounded text-xs font-semibold font-mono ${
              isCompleted
                ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                : isRunning
                ? "bg-blue-100 text-blue-800 border border-blue-200"
                : isPaused
                ? "bg-amber-100 text-amber-900 border border-amber-300"
                : isFailed
                ? "bg-rose-100 text-rose-800 border border-rose-200"
                : "bg-slate-100 text-slate-600 border border-slate-200"
            }`}
          >
            {execution.status.replace(/_/g, " ")}
          </span>
        </div>
      </div>
    </div>
  );
}
