import React from "react";
import { Check, AlertTriangle, XCircle, Clock } from "lucide-react";

export type MilestoneStatus = "COMPLETED" | "RUNNING" | "PAUSED_FOR_HUMAN" | "FAILED" | "WAITING";

export interface MilestoneItem {
  id: string;
  name: string;
  code: string;
  societyKey: string;
  status: MilestoneStatus;
  summary?: string;
  completedAt?: string;
}

interface JourneyDestinationProps {
  milestone: MilestoneItem;
  index: number;
  isActive: boolean;
  onClick?: () => void;
}

export function JourneyDestination({
  milestone,
  index,
  isActive,
  onClick,
}: JourneyDestinationProps) {
  const isCompleted = milestone.status === "COMPLETED";
  const isRunning = milestone.status === "RUNNING";
  const isPaused = milestone.status === "PAUSED_FOR_HUMAN";
  const isFailed = milestone.status === "FAILED";
  const isWaiting = milestone.status === "WAITING";

  return (
    <div
      onClick={onClick}
      className={`relative flex flex-col items-center text-center p-2.5 rounded-lg border transition-all cursor-pointer select-none min-w-[105px] max-w-[125px] ${
        isActive
          ? "bg-blue-50/80 border-blue-500 shadow-sm ring-2 ring-blue-500/20"
          : isCompleted
          ? "bg-white border-emerald-200 hover:border-emerald-300"
          : isPaused
          ? "bg-amber-50/60 border-amber-300 ring-2 ring-amber-400/20"
          : isFailed
          ? "bg-rose-50/60 border-rose-300 ring-2 ring-rose-400/20"
          : "bg-white/80 border-slate-200 hover:border-slate-300"
      }`}
    >
      {/* Guide Board Top Tab / Mile marker */}
      <div className="flex items-center justify-between w-full mb-1.5 px-0.5">
        <span className="text-[9px] font-mono font-bold text-slate-400">
          0{index + 1}
        </span>
        {isCompleted && (
          <span className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-emerald-100 text-emerald-700">
            <Check className="w-2.5 h-2.5 stroke-[3]" />
          </span>
        )}
        {isRunning && (
          <span className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-blue-100 text-blue-700">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
          </span>
        )}
        {isPaused && (
          <span className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-amber-100 text-amber-700">
            <AlertTriangle className="w-2.5 h-2.5" />
          </span>
        )}
        {isFailed && (
          <span className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-rose-100 text-rose-700">
            <XCircle className="w-2.5 h-2.5" />
          </span>
        )}
        {isWaiting && (
          <span className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-slate-100 text-slate-400">
            <Clock className="w-2 h-2" />
          </span>
        )}
      </div>

      {/* Guide Board Title */}
      <div className="text-xs font-semibold text-slate-900 leading-tight mb-1">
        {milestone.name}
      </div>

      {/* Status Pill */}
      <div
        className={`text-[9px] font-medium px-1.5 py-0.5 rounded ${
          isCompleted
            ? "bg-emerald-50 text-emerald-700 font-semibold"
            : isRunning
            ? "bg-blue-100 text-blue-800 font-bold"
            : isPaused
            ? "bg-amber-100 text-amber-800 font-bold"
            : isFailed
            ? "bg-rose-100 text-rose-800 font-bold"
            : "bg-slate-100 text-slate-500"
        }`}
      >
        {milestone.status === "PAUSED_FOR_HUMAN"
          ? "HUMAN GATE"
          : milestone.status.replace(/_/g, " ")}
      </div>
    </div>
  );
}
