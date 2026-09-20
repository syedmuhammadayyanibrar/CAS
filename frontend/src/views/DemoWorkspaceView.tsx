import React, { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Play,
  RotateCcw,
  FastForward,
  CheckCircle2,
  ExternalLink,
  Zap,
  Radio,
} from "lucide-react";
import { resetDemo, runDemoStep, ContractExecutionState } from "../api/client";
import { StageDeliverableRenderer } from "../components/StageDeliverableRenderer";
import { AgentJourney } from "../components/execution/AgentJourney";

interface StepResult {
  step: number;
  title: string;
  society: string;
  summary: string;
  data: any;
}

const STAGES = [
  { step: 1, title: "Fastn Inbound Intake", society: "Fastn Inbound Webhook", key: "contract_intake" },
  { step: 2, title: "Contract Graph Construction", society: "Contract Intelligence (System 1)", key: "contract_intelligence" },
  { step: 3, title: "Adversarial Risk Debate", society: "Risk Intelligence (System 2)", key: "risk_intelligence" },
  { step: 4, title: "Fastn Risk Escalation", society: "Fastn Outbound (Slack #legal-contract-risks)", key: "risk_intelligence" },
  { step: 5, title: "Negotiation Redlining", society: "Negotiation Intelligence (System 3)", key: "negotiation_intelligence" },
  { step: 6, title: "Compliance Policy Audit", society: "Compliance Intelligence (System 4)", key: "compliance_intelligence" },
  { step: 7, title: "Fastn Compliance Escalation", society: "Fastn Outbound (Compliance Alert)", key: "compliance_intelligence" },
  { step: 8, title: "Director Mesh Orchestration", society: "CAS Director Dynamic Mesh Core", key: "negotiation_intelligence" },
  { step: 9, title: "Fastn HITL Approval Dispatch", society: "Fastn Outbound (Slack + Email Dispatch)", key: "decision_archive" },
  { step: 10, title: "Fastn Decision Archival", society: "Fastn Outbound (Google Drive & Airtable)", key: "decision_archive" },
  { step: 11, title: "Obligation Calendar Sync", society: "Obligation Intelligence & Fastn (System 5)", key: "obligation_intelligence" },
  { step: 12, title: "Fastn Inbound Redline Event", society: "Fastn Inbound (External Counterparty Portal)", key: "negotiation_intelligence" },
  { step: 13, title: "Director Re-Routing & Adaptation", society: "CAS Director & Negotiation Society", key: "negotiation_intelligence" },
  { step: 14, title: "Fastn Dispute Escalation", society: "Fastn Outbound (Litigation Alert)", key: "dispute_intelligence" },
  { step: 15, title: "Dispute Simulation & CAS Memory", society: "Dispute Intelligence (System 6) & Memory", key: "dispute_intelligence" },
];

export function DemoWorkspaceView() {
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [results, setResults] = useState<Record<number, StepResult>>({});
  const [running, setRunning] = useState(false);
  const [activeTabStep, setActiveTabStep] = useState<number>(1);
  const [demoStatus, setDemoStatus] = useState<string>("Ready to execute Stage 1");

  const handleReset = async () => {
    setRunning(true);
    try {
      await resetDemo();
      setCurrentStep(0);
      setResults({});
      setActiveTabStep(1);
      setDemoStatus("Demo reset. Ready to execute Stage 1.");
    } catch (err: any) {
      alert("Reset failed: " + err.message);
    } finally {
      setRunning(false);
    }
  };

  const handleRunStep = async (stepNum: number) => {
    setRunning(true);
    setDemoStatus(`Executing Stage ${stepNum}: ${STAGES[stepNum - 1].title}...`);
    try {
      const res = await runDemoStep(stepNum);
      setResults((prev) => ({ ...prev, [stepNum]: res }));
      setCurrentStep(stepNum);
      setActiveTabStep(stepNum);
      setDemoStatus(`Stage ${stepNum} complete.`);
    } catch (err: any) {
      alert(`Step ${stepNum} failed: ` + err.message);
      setDemoStatus(`Stage ${stepNum} halted with error.`);
    } finally {
      setRunning(false);
    }
  };

  const handleRunAll = async () => {
    setRunning(true);
    const start = currentStep < 15 ? currentStep + 1 : 1;
    for (let s = start; s <= 15; s++) {
      setDemoStatus(`Executing Stage ${s} of 15: ${STAGES[s - 1].title}...`);
      try {
        const res = await runDemoStep(s);
        setResults((prev) => ({ ...prev, [s]: res }));
        setCurrentStep(s);
        setActiveTabStep(s);
      } catch (err: any) {
        alert(`Stage ${s} failed: ` + err.message);
        break;
      }
    }
    setRunning(false);
    setDemoStatus("Full 15-Stage Federation Scenario Completed Successfully!");
  };

  // Build live Execution state for the AgentJourney road visualization
  const simulatedExecution: ContractExecutionState = useMemo(() => {
    const isDone = currentStep >= 15;
    const isPaused = currentStep === 9; // Stage 9 is HITL approval dispatch
    const activeStageDef = STAGES[Math.max(0, Math.min(currentStep - 1, 14))];

    return {
      execution_id: "EXEC-DEMO-SCENARIO",
      contract_id: "CTR-DEMO-2026-SAAS",
      title: "NovaCloud Enterprise Cloud Services Agreement",
      status: isDone ? "COMPLETED" : isPaused ? "PAUSED_FOR_HUMAN" : currentStep > 0 ? "RUNNING" : "WAITING",
      current_step: currentStep > 0 ? {
        society: activeStageDef.society,
        agent: activeStageDef.title,
        task: results[currentStep]?.summary || `Operating in ${activeStageDef.society}`,
        status: isDone ? "COMPLETED" : isPaused ? "PAUSED_FOR_HUMAN" : "RUNNING",
      } : null,
      next_step: currentStep < 15 ? {
        society: STAGES[currentStep].society,
        agent: STAGES[currentStep].title,
        task: "Next autonomous pipeline milestone",
        waiting_reason: "Awaiting stage execution",
      } : null,
      stages: STAGES.slice(0, Math.max(1, currentStep)).map((s) => ({
        id: `stage-${s.step}`,
        number: `0${s.step}`,
        title: s.title,
        society: s.society,
        status: s.step < currentStep ? "COMPLETED" : s.step === currentStep ? (isPaused ? "PAUSED_FOR_HUMAN" : "COMPLETED") : "WAITING",
        summary: results[s.step]?.summary || s.title,
        agents: [
          {
            id: `ag-${s.step}`,
            name: s.title,
            task: results[s.step]?.summary || `Execution of ${s.society}`,
            status: s.step <= currentStep ? "COMPLETED" : "WAITING",
            result_summary: results[s.step]?.summary,
          },
        ],
      })),
      events: [],
    };
  }, [currentStep, results]);

  const currentResult = results[activeTabStep];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-[#111827] flex items-center gap-2">
            <Radio className="w-4 h-4 text-blue-600" />
            <span>Interactive 15-Stage Federation Demo</span>
          </h2>
          <p className="text-xs text-[#6B7280]">
            End-to-End Bidirectional Orchestration: Acme Global &harr; Fastn Nervous System &harr; NovaCloud Inc.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            disabled={running}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 rounded-md text-xs font-medium border border-[#E5E7EB] transition-colors cursor-pointer disabled:opacity-50 shadow-2xs"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>

          <button
            onClick={() => handleRunStep(currentStep + 1)}
            disabled={running || currentStep >= 15}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{running ? "Running..." : `Run Stage ${currentStep + 1}`}</span>
          </button>

          <button
            onClick={handleRunAll}
            disabled={running || currentStep >= 15}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
          >
            <FastForward className="w-3.5 h-3.5" />
            <span>Run All 15 Stages</span>
          </button>
        </div>
      </div>

      {/* Scenario Overview Banner */}
      <div className="p-4 rounded-xl bg-white border border-[#E5E7EB] shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-900">
              Scenario: NovaCloud Enterprise Cloud Agreement ($480k ACV)
            </span>
            <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-mono font-semibold">
              CTR-DEMO-2026-SAAS
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[10px] font-mono font-semibold">
              15-Stage Lifecycle
            </span>
          </div>
          <p className="text-xs text-[#6B7280]">
            {demoStatus}
          </p>
        </div>

        <Link
          to="/contracts/CTR-DEMO-2026-SAAS"
          className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 font-medium shrink-0"
        >
          <span>Open Contract Workspace</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Animated Vector AgentJourney embedded across Demo */}
      <AgentJourney
        execution={simulatedExecution}
        isAnalyzing={running}
        defaultExpandedTimeline={false}
      />

      {/* 15-Stage Step Progress Rail */}
      <div className="bg-white border border-[#E5E7EB] rounded-lg p-3 overflow-x-auto shadow-xs">
        <div className="flex items-center min-w-[980px] justify-between gap-1">
          {STAGES.map((stg) => {
            const isCompleted = stg.step <= currentStep;
            const isCurrent = stg.step === currentStep + 1;
            const isSelected = activeTabStep === stg.step;

            return (
              <button
                key={stg.step}
                onClick={() => setActiveTabStep(stg.step)}
                className={`flex-1 flex flex-col items-center p-1.5 rounded-md transition-all cursor-pointer ${
                  isSelected
                    ? "bg-blue-50 border border-blue-300 font-semibold"
                    : "hover:bg-slate-50 border border-transparent"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border transition-colors ${
                    isCompleted
                      ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                      : isCurrent
                      ? "bg-blue-600 text-white border-blue-600 animate-pulse"
                      : "bg-slate-100 text-slate-400 border-slate-200"
                  }`}
                >
                  {isCompleted ? "✓" : stg.step}
                </div>
                <span
                  className={`text-[9px] mt-1 text-center truncate max-w-[65px] font-mono ${
                    isSelected
                      ? "text-blue-700 font-bold"
                      : isCompleted
                      ? "text-slate-800"
                      : "text-slate-400"
                  }`}
                >
                  S{stg.step}: {stg.title.split(" ")[0]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Stage Inspector Pane */}
      <div className="p-6 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E5E7EB] pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-xs font-mono font-bold">
                Stage {activeTabStep} / 15
              </span>
              <h3 className="text-sm font-bold text-[#111827]">
                {STAGES[activeTabStep - 1].title}
              </h3>
            </div>
            <div className="text-xs text-[#6B7280] mt-0.5">
              Operating Component:{" "}
              <span className="text-slate-900 font-semibold">
                {STAGES[activeTabStep - 1].society}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {results[activeTabStep] ? (
              <span className="px-2.5 py-1 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-1 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Completed
              </span>
            ) : (
              <button
                onClick={() => handleRunStep(activeTabStep)}
                disabled={running}
                className="px-3.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
              >
                Execute Stage {activeTabStep}
              </button>
            )}
          </div>
        </div>

        {/* Stage Content */}
        {currentResult ? (
          <StageDeliverableRenderer
            step={currentResult.step}
            title={currentResult.title}
            society={currentResult.society}
            summary={currentResult.summary}
            data={currentResult.data}
          />
        ) : (
          <div className="py-12 text-center text-slate-500 text-xs space-y-3">
            <p>Stage {activeTabStep} has not been executed yet.</p>
            <button
              onClick={() => handleRunStep(activeTabStep)}
              disabled={running}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
            >
              Run Stage {activeTabStep} Now
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
