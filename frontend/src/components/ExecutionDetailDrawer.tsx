import React, { useState, useEffect } from "react";
import { X, ChevronDown, ChevronRight, CheckCircle2, Clock, AlertTriangle, ShieldCheck, FileText } from "lucide-react";
import { ExecutionAgent, ExecutionStage } from "../api/client";

interface ExecutionDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  agent: ExecutionAgent | null;
  stage: ExecutionStage | null;
  executionId?: string;
}

export function ExecutionDetailDrawer({
  isOpen,
  onClose,
  agent,
  stage,
  executionId,
}: ExecutionDetailDrawerProps) {
  const [showTechnical, setShowTechnical] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !agent) return null;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950/80 border border-emerald-800 text-emerald-300">
            <CheckCircle2 className="w-3 h-3" />
            Completed
          </span>
        );
      case "RUNNING":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium bg-blue-950/80 border border-blue-800 text-blue-300">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            Running
          </span>
        );
      case "PAUSED_FOR_HUMAN":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-amber-950/80 border border-amber-800 text-amber-300">
            <AlertTriangle className="w-3 h-3" />
            Paused for Human
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-900 border border-slate-800 text-slate-400">
            <Clock className="w-3 h-3" />
            Waiting
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity cursor-pointer"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-lg bg-[#0d121f] border-l border-slate-800 shadow-2xl flex flex-col h-full z-10 text-slate-200 animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-800 flex items-start justify-between gap-4 bg-[#090d16]">
          <div className="space-y-1">
            <div className="text-[11px] uppercase font-semibold tracking-wider text-blue-400">
              {stage?.society || "Federated Society"}
            </div>
            <h2 className="text-base font-bold text-slate-100">{agent.name}</h2>
            <p className="text-xs text-slate-400 leading-relaxed">{agent.task}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Status & Duration Meta */}
          <div className="grid grid-cols-2 gap-3 p-3.5 rounded bg-slate-900/60 border border-slate-800/80 text-xs">
            <div>
              <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mb-1">
                Status
              </div>
              {getStatusBadge(agent.status)}
            </div>
            <div>
              <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mb-1">
                Execution Mode
              </div>
              <div className="text-slate-300 font-mono text-xs">
                {agent.is_parallel ? "Parallel Branch" : "Sequential"}
              </div>
            </div>
          </div>

          {/* Active / Current Task */}
          <div className="space-y-1.5">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Assigned Task
            </h3>
            <div className="p-3 rounded bg-slate-900/40 border border-slate-800 text-xs text-slate-200 leading-relaxed font-mono">
              {agent.task}
            </div>
          </div>

          {/* Result (Only when available) */}
          {agent.result_summary && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Execution Result
              </h3>
              <div className="p-3 rounded bg-emerald-950/20 border border-emerald-900/40 text-xs text-emerald-300 leading-relaxed">
                <div className="flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>{agent.result_summary}</span>
                </div>
              </div>
            </div>
          )}

          {/* Evidence Citations */}
          {agent.evidence && agent.evidence.length > 0 && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Contract Evidence
              </h3>
              <div className="space-y-2">
                {agent.evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded bg-slate-950/80 border border-slate-800/80 text-xs text-slate-300 space-y-1 font-mono"
                  >
                    <div className="flex items-center gap-1 text-[10px] text-blue-400">
                      <FileText className="w-3 h-3" />
                      <span>Evidence Reference #{idx + 1}</span>
                    </div>
                    <p className="text-[11px] text-slate-300 leading-relaxed">{ev}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Technical Details (Collapsed by default) */}
          <div className="border-t border-slate-800/80 pt-4">
            <button
              onClick={() => setShowTechnical(!showTechnical)}
              className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer w-full text-left"
            >
              {showTechnical ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5" />
              )}
              <span className="font-semibold uppercase tracking-wider text-[10px]">
                Technical Details
              </span>
            </button>

            {showTechnical && (
              <div className="mt-3 p-3 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-400 space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">Agent ID:</span>
                  <span className="text-slate-300">{agent.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Event ID:</span>
                  <span className="text-slate-300">{agent.event_id || "EVT-CORE-TRACE"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Execution ID:</span>
                  <span className="text-slate-300">{executionId || "EXEC-LIVE"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Society:</span>
                  <span className="text-slate-300">{stage?.society || "CAS Mesh"}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-[#090d16] flex justify-end">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors cursor-pointer"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
}
