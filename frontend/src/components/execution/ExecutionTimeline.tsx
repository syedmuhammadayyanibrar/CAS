import React from "react";
import {
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  Zap,
} from "lucide-react";
import {
  ExecutionAgent,
  ExecutionStage,
} from "../../api/client";

interface ExecutionTimelineProps {
  stages: ExecutionStage[];
  onSelectAgent: (agent: ExecutionAgent, stage: ExecutionStage) => void;
}

export function ExecutionTimeline({
  stages,
  onSelectAgent,
}: ExecutionTimelineProps) {
  const fastnStage = stages.find((s) => s.id === "fastn_automation");
  const showFastn = fastnStage && fastnStage.status === "COMPLETED";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
          Detailed Execution Stages
        </span>
        <span className="text-[11px] text-slate-400">
          Click any agent to inspect raw message payloads & citations
        </span>
      </div>

      <div className="space-y-3">
        {stages.map((stage, sIdx) => {
          if (stage.id === "fastn_automation" && stage.status !== "COMPLETED") {
            return null;
          }
          if (stage.id === "human_review" && stage.status === "WAITING") {
            return null;
          }

          if (stage.is_transition) {
            return (
              <div
                key={stage.id || sIdx}
                className="pl-6 py-1 flex items-center gap-2.5 text-xs font-mono text-slate-500"
              >
                <span className="text-blue-500">↓</span>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-700">
                    {stage.title}
                  </span>
                  <span className="text-slate-300">—</span>
                  <span className="text-[11px] text-slate-500">
                    {stage.summary}
                  </span>
                </div>
              </div>
            );
          }

          const isRunning = stage.status === "RUNNING";
          const isCompleted = stage.status === "COMPLETED";
          const isPaused = stage.status === "PAUSED_FOR_HUMAN";
          const isWaiting = stage.status === "WAITING";

          return (
            <div
              key={stage.id || sIdx}
              className={`rounded-lg border transition-all p-4 space-y-3 ${
                isRunning
                  ? "bg-blue-50/40 border-blue-300 shadow-xs"
                  : isCompleted
                  ? "bg-white border-[#E5E7EB]"
                  : isPaused
                  ? "bg-amber-50/60 border-amber-300"
                  : "bg-slate-50/50 border-slate-200 opacity-60"
              }`}
            >
              {/* Stage Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    {stage.number && (
                      <span className="text-[10px] font-mono text-slate-500 font-bold">
                        {stage.number}
                      </span>
                    )}
                    {isCompleted && (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    )}
                    {isRunning && (
                      <span className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-pulse shrink-0" />
                    )}
                    {isPaused && (
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    )}
                    {isWaiting && (
                      <span className="w-2.5 h-2.5 rounded-full border border-slate-400 shrink-0" />
                    )}
                  </div>

                  <div>
                    <h4
                      className={`text-xs font-bold ${
                        isRunning
                          ? "text-blue-900"
                          : isCompleted
                          ? "text-slate-900"
                          : isPaused
                          ? "text-amber-900"
                          : "text-slate-600"
                      }`}
                    >
                      {stage.title}
                    </h4>
                    <p className="text-[11px] text-slate-500 leading-snug">
                      {stage.summary}
                    </p>
                  </div>
                </div>

                <span
                  className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded ${
                    isCompleted
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      : isRunning
                      ? "bg-blue-100 text-blue-800 border border-blue-200 font-semibold"
                      : isPaused
                      ? "bg-amber-100 text-amber-900 border border-amber-300 font-semibold"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {stage.status.replace(/_/g, " ")}
                </span>
              </div>

              {/* Sub-Agents Hierarchy */}
              {stage.agents && stage.agents.length > 0 && (
                <div className="mt-2 pl-4 border-l border-slate-200 space-y-2">
                  {stage.agents.map((ag, aIdx) => {
                    const isAgRunning = ag.status === "RUNNING";
                    const isAgDone = ag.status === "COMPLETED";
                    const isLast = aIdx === stage.agents.length - 1;

                    return (
                      <div
                        key={ag.id || aIdx}
                        onClick={() => onSelectAgent(ag, stage)}
                        className={`group p-2.5 rounded flex items-start justify-between gap-3 text-xs cursor-pointer transition-colors ${
                          isAgRunning
                            ? "bg-blue-50 border border-blue-200"
                            : "hover:bg-slate-50 border border-transparent"
                        }`}
                      >
                        <div className="flex items-start gap-2.5">
                          <span className="text-slate-400 font-mono select-none">
                            {stage.is_parallel ? (isLast ? "└─" : "├─") : "•"}
                          </span>

                          {isAgDone ? (
                            <span className="text-emerald-600 font-bold select-none">✓</span>
                          ) : isAgRunning ? (
                            <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse mt-1 select-none" />
                          ) : (
                            <span className="w-2 h-2 rounded-full border border-slate-400 mt-1 select-none" />
                          )}

                          <div>
                            <div className="font-semibold text-slate-800 group-hover:text-blue-600 transition-colors flex items-center gap-1.5">
                              <span>{ag.name}</span>
                              {ag.is_parallel && (
                                <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                                  Parallel
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                              {ag.task}
                            </div>
                            {ag.result_summary && (
                              <div className="mt-1 text-[11px] text-emerald-700 font-medium">
                                ✓ {ag.result_summary}
                              </div>
                            )}
                          </div>
                        </div>

                        <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-700 transition-colors shrink-0 mt-0.5" />
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Fastn External Automation Triggered */}
      {showFastn && (
        <div className="p-3.5 rounded-lg bg-amber-50/60 border border-amber-200 text-xs flex items-center justify-between text-slate-700">
          <div className="flex items-center gap-2 font-mono text-[11px]">
            <Zap className="w-3.5 h-3.5 text-amber-600" />
            <span className="text-slate-500">CAS Director</span>
            <span className="text-slate-400">→</span>
            <span className="text-amber-800 font-semibold">Fastn Adapter</span>
            <span className="text-slate-400">→</span>
            <span className="text-slate-700">External Slack Webhook</span>
          </div>
          <div className="text-emerald-700 text-xs font-medium">
            ✓ {fastnStage.summary}
          </div>
        </div>
      )}
    </div>
  );
}
