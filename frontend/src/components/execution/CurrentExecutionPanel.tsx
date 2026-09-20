import React from "react";
import { ContractExecutionState } from "../../api/client";
import { ArrowRight, Bot, Compass, ShieldAlert } from "lucide-react";

interface CurrentExecutionPanelProps {
  execution: ContractExecutionState | null;
  elapsedSeconds: number;
}

export function CurrentExecutionPanel({
  execution,
  elapsedSeconds,
}: CurrentExecutionPanelProps) {
  if (!execution) return null;

  const currentStep = execution.current_step;
  const nextStep = execution.next_step;
  const isCompleted = execution.status === "COMPLETED";
  const isPaused = execution.status === "PAUSED_FOR_HUMAN";
  const isRunning = execution.status === "RUNNING";

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Current Step (Society vs Agent Distinction - 2 cols on md) */}
      <div className="md:col-span-2 p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-2 relative">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200 font-mono">
              CURRENT AGENT
            </span>
            <span className="text-slate-300">•</span>
            <span className="text-xs font-semibold text-slate-700 flex items-center gap-1">
              <Compass className="w-3.5 h-3.5 text-blue-600" />
              <span>
                {currentStep?.society ||
                  (isCompleted
                    ? "CAS Director"
                    : isPaused
                    ? "Human Review Gate"
                    : "Intake Society")}
              </span>
            </span>
          </div>

          {isRunning && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-xs font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
              <span>Active · {elapsedSeconds}s</span>
            </div>
          )}
          {isCompleted && (
            <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-mono font-semibold">
              ✓ Done
            </span>
          )}
          {isPaused && (
            <span className="px-2 py-0.5 rounded bg-amber-50 border border-amber-300 text-amber-800 text-xs font-mono font-semibold">
              Paused (Review)
            </span>
          )}
        </div>

        <div className="text-sm font-bold text-[#111827] flex items-center gap-2">
          <Bot className="w-4 h-4 text-blue-600" />
          <span>
            {currentStep?.agent ||
              (isCompleted
                ? "Autonomous Pipeline Synthesis"
                : isPaused
                ? "General Counsel Reviewer"
                : "Awaiting Next Agent")}
          </span>
        </div>

        <p className="text-xs text-[#4B5563] font-mono leading-relaxed bg-slate-50 p-2.5 rounded border border-slate-200">
          {currentStep?.task ||
            (isCompleted
              ? "Synthesis, conflict arbitration, redlining, and obligation extraction complete."
              : isPaused
              ? "Critical risk detected. Execution paused until human reviewer submits a decision."
              : "System ready.")}
        </p>
      </div>

      {/* Next Step (Secondary - 1 col) */}
      <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-2 flex flex-col justify-between">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 font-mono mb-1">
            NEXT STAGE IN QUEUE
          </div>
          <div className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
            <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
            <span>
              {nextStep?.agent ||
                (isRunning
                  ? "Subsequent Society Agent"
                  : isCompleted
                  ? "Archive & Synchronize"
                  : "Pending Human Sign-off")}
            </span>
          </div>
        </div>

        <div className="text-xs text-slate-500 leading-snug bg-slate-50 p-2 rounded border border-slate-200">
          {nextStep?.waiting_reason ||
            (isRunning
              ? "Waiting for current agent task to yield findings."
              : "Pipeline complete.")}
        </div>
      </div>
    </div>
  );
}
