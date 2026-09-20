import React, { useState, useEffect } from "react";
import { X, ChevronDown, ChevronRight, CheckCircle2, Clock, AlertTriangle, FileText } from "lucide-react";
import { ExecutionAgent, ExecutionStage } from "../../api/client";

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
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-50 border border-emerald-200 text-emerald-700">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Completed
          </span>
        );
      case "RUNNING":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold bg-blue-50 border border-blue-200 text-blue-700">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
            Running
          </span>
        );
      case "PAUSED_FOR_HUMAN":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-50 border border-amber-300 text-amber-800">
            <AlertTriangle className="w-3.5 h-3.5" />
            Paused for Human
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-medium bg-slate-100 border border-slate-200 text-slate-600">
            <Clock className="w-3.5 h-3.5" />
            Waiting
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/30 backdrop-blur-xs transition-opacity cursor-pointer"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-lg bg-white border-l border-[#E5E7EB] shadow-2xl flex flex-col h-full z-10 text-slate-800 animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="p-5 border-b border-[#E5E7EB] flex items-start justify-between gap-4 bg-slate-50/70">
          <div className="space-y-1">
            <div className="text-[11px] uppercase font-bold tracking-wider text-blue-600 font-mono">
              {stage?.society || "Federated Society"}
            </div>
            <h2 className="text-base font-bold text-[#111827]">{agent.name}</h2>
            <p className="text-xs text-slate-600 leading-relaxed">{agent.task}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Status & Duration Meta */}
          <div className="grid grid-cols-2 gap-3 p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
            <div>
              <div className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider mb-1">
                Status
              </div>
              {getStatusBadge(agent.status)}
            </div>
            <div>
              <div className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider mb-1">
                Execution Mode
              </div>
              <div className="text-slate-700 font-mono text-xs font-medium">
                {agent.is_parallel ? "Parallel Branch" : "Sequential"}
              </div>
            </div>
          </div>

          {/* Active / Current Task */}
          <div className="space-y-1.5">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Assigned Objective
            </h3>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-800 leading-relaxed font-mono">
              {agent.task}
            </div>
          </div>

          {/* Result (Only when available) */}
          {agent.result_summary && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Execution Output
              </h3>
              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 leading-relaxed">
                <div className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span>{agent.result_summary}</span>
                </div>
              </div>
            </div>
          )}

          {/* Evidence Citations */}
          {agent.evidence && agent.evidence.length > 0 && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Contract Evidence & Grounding
              </h3>
              <div className="space-y-2">
                {agent.evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1 font-mono"
                  >
                    <div className="flex items-center gap-1 text-[10px] text-blue-700 font-semibold">
                      <FileText className="w-3.5 h-3.5" />
                      <span>Evidence Reference #{idx + 1}</span>
                    </div>
                    <p className="text-[11px] text-slate-700 leading-relaxed">{ev}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Technical Details (Collapsed by default) */}
          <div className="border-t border-slate-200 pt-4">
            <button
              onClick={() => setShowTechnical(!showTechnical)}
              className="flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900 transition-colors cursor-pointer w-full text-left"
            >
              {showTechnical ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5" />
              )}
              <span className="font-semibold uppercase tracking-wider text-[10px]">
                Technical Metadata & Protocol
              </span>
            </button>

            {showTechnical && (
              <div className="mt-3 p-3 rounded-lg bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-600 space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">Agent ID:</span>
                  <span className="text-slate-800 font-semibold">{agent.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Event ID:</span>
                  <span className="text-slate-800">{agent.event_id || "EVT-CORE-TRACE"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Execution ID:</span>
                  <span className="text-slate-800">{executionId || "EXEC-LIVE"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Society:</span>
                  <span className="text-slate-800">{stage?.society || "CAS Mesh"}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#E5E7EB] bg-slate-50/80 flex justify-end">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-md bg-white border border-slate-300 hover:bg-slate-100 text-xs text-slate-700 font-medium transition-colors cursor-pointer"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
}
