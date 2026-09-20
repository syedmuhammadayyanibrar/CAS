import React, { useState, useEffect, useMemo } from "react";
import {
  ContractExecutionState,
  ExecutionAgent,
  ExecutionStage,
} from "../../api/client";
import { JourneyStatus } from "./JourneyStatus";
import { JourneyRoad } from "./JourneyRoad";
import { JourneyDestination, MilestoneItem, MilestoneStatus } from "./JourneyDestination";
import { CurrentExecutionPanel } from "./CurrentExecutionPanel";
import { ExecutionTimeline } from "./ExecutionTimeline";
import { ExecutionDetailDrawer } from "./ExecutionDetailDrawer";

interface AgentJourneyProps {
  execution: ContractExecutionState | null;
  isAnalyzing?: boolean;
  onReviewDecision?: () => void;
  className?: string;
  defaultExpandedTimeline?: boolean;
}

const BASE_DESTINATIONS = [
  { id: "dest-1", name: "Contract Received", code: "INTAKE", societyKey: "contract_intake" },
  { id: "dest-2", name: "Contract Intelligence", code: "INTEL", societyKey: "contract_intelligence" },
  { id: "dest-3", name: "Risk Intelligence", code: "RISK", societyKey: "risk_intelligence" },
  { id: "dest-4", name: "Compliance Intelligence", code: "COMPLIANCE", societyKey: "compliance_intelligence" },
  { id: "dest-5", name: "Negotiation Intelligence", code: "NEGOTIATION", societyKey: "negotiation_intelligence" },
  { id: "dest-6", name: "Obligation Intelligence", code: "OBLIGATION", societyKey: "obligation_intelligence" },
  { id: "dest-7", name: "Dispute Intelligence", code: "DISPUTE", societyKey: "dispute_intelligence" },
  { id: "dest-8", name: "Decision & Archive", code: "DECISION", societyKey: "decision_archive" },
];

export function AgentJourney({
  execution,
  isAnalyzing = false,
  onReviewDecision,
  className = "",
  defaultExpandedTimeline = true,
}: AgentJourneyProps) {
  const [selectedItem, setSelectedItem] = useState<{
    agent: ExecutionAgent;
    stage: ExecutionStage;
  } | null>(null);

  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!execution || execution.status !== "RUNNING") {
      setElapsedSeconds(0);
      return;
    }

    const startTs = execution.current_step?.started_at_ts || Date.now() / 1000;
    const interval = setInterval(() => {
      const now = Date.now() / 1000;
      setElapsedSeconds(Math.max(1, Math.floor(now - startTs)));
    }, 1000);

    return () => clearInterval(interval);
  }, [execution?.status, execution?.current_step?.started_at_ts]);

  // Compute current milestone index and milestone statuses from execution state
  const { milestones, activeIndex } = useMemo(() => {
    if (!execution) {
      const blank: MilestoneItem[] = BASE_DESTINATIONS.map((d) => ({
        id: d.id,
        name: d.name,
        code: d.code,
        societyKey: d.societyKey,
        status: "WAITING",
      }));
      return { milestones: blank, activeIndex: 0 };
    }

    const currentSoc = (execution.current_step?.society || "").toLowerCase().replace(/\s+/g, "_");
    const isCompleted = execution.status === "COMPLETED";
    const isPaused =
      execution.status === "PAUSED_FOR_HUMAN" ||
      execution.stages.some((s) => s.status === "PAUSED_FOR_HUMAN");
    const isFailed = execution.status === "FAILED";

    // Match societies from stages
    const completedSocieties = new Set<string>();
    execution.stages.forEach((s) => {
      const key = (s.society || s.id || "").toLowerCase().replace(/\s+/g, "_");
      if (s.status === "COMPLETED") {
        completedSocieties.add(key);
      }
    });

    let currentIdx = 0;
    if (isCompleted) {
      currentIdx = BASE_DESTINATIONS.length - 1;
    } else {
      const matched = BASE_DESTINATIONS.findIndex(
        (d) => currentSoc.includes(d.societyKey) || d.societyKey.includes(currentSoc)
      );
      if (matched !== -1) {
        currentIdx = matched;
      } else {
        // Fallback based on completed count
        currentIdx = Math.min(completedSocieties.size, BASE_DESTINATIONS.length - 1);
      }
    }

    const list: MilestoneItem[] = BASE_DESTINATIONS.map((dest, idx) => {
      let status: MilestoneStatus = "WAITING";
      if (isCompleted) {
        status = "COMPLETED";
      } else if (idx < currentIdx) {
        status = "COMPLETED";
      } else if (idx === currentIdx) {
        if (isPaused) status = "PAUSED_FOR_HUMAN";
        else if (isFailed) status = "FAILED";
        else if (execution.status === "RUNNING") status = "RUNNING";
        else status = "WAITING";
      } else {
        status = "WAITING";
      }

      return {
        id: dest.id,
        name: dest.name,
        code: dest.code,
        societyKey: dest.societyKey,
        status,
      };
    });

    return { milestones: list, activeIndex: currentIdx };
  }, [execution]);

  if (!execution) {
    return (
      <div className="p-8 rounded-xl bg-white border border-[#E5E7EB] shadow-xs text-center text-xs text-slate-500">
        No active execution trace for this agreement. Click &ldquo;Analyze with Mesh&rdquo; to begin.
      </div>
    );
  }

  const activeMilestone = milestones[activeIndex] || milestones[0];

  return (
    <div
      className={`rounded-xl bg-white border border-[#E5E7EB] shadow-xs overflow-hidden space-y-5 p-5 ${className}`}
    >
      {/* 1. Header Journey Status Banner */}
      <JourneyStatus
        execution={execution}
        elapsedSeconds={elapsedSeconds}
        currentMilestoneTitle={activeMilestone.name}
        onReviewDecision={onReviewDecision}
      />

      {/* 2. Vector SVG Road with Traveling Vector Car */}
      <div className="bg-slate-50/70 border border-slate-200 rounded-lg p-3">
        <JourneyRoad
          milestones={milestones}
          currentIndex={activeIndex}
          isRunning={execution.status === "RUNNING"}
          isPaused={
            execution.status === "PAUSED_FOR_HUMAN" ||
            execution.stages.some((s) => s.status === "PAUSED_FOR_HUMAN")
          }
        />

        {/* 3. Roadside Guide Boards (8 Destinations) */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 pt-3 border-t border-slate-200">
          {milestones.map((m, idx) => (
            <JourneyDestination
              key={m.id}
              milestone={m}
              index={idx}
              isActive={idx === activeIndex}
            />
          ))}
        </div>
      </div>

      {/* 4. Current Execution Panel (Society vs Agent Distinction) */}
      <CurrentExecutionPanel
        execution={execution}
        elapsedSeconds={elapsedSeconds}
      />

      {/* 5. Detailed Execution Stages & Agent Timeline */}
      {defaultExpandedTimeline && (
        <div className="pt-2 border-t border-slate-200">
          <ExecutionTimeline
            stages={execution.stages}
            onSelectAgent={(agent, stage) => setSelectedItem({ agent, stage })}
          />
        </div>
      )}

      {/* Slide-out Execution Detail Drawer */}
      <ExecutionDetailDrawer
        isOpen={!!selectedItem}
        onClose={() => setSelectedItem(null)}
        agent={selectedItem?.agent || null}
        stage={selectedItem?.stage || null}
        executionId={execution.execution_id}
      />
    </div>
  );
}
