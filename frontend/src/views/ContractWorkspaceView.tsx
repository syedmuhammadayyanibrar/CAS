import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Sparkles,
  ShieldAlert,
  CheckCircle2,
  FileText,
  Clock,
  Scale,
  Send,
  Play,
  Check,
  AlertTriangle,
  Activity,
  Layers,
} from "lucide-react";
import {
  fetchContractDetail,
  fetchContractAnalysis,
  triggerMeshAnalysis,
  signContract,
  askContractQuestion,
  fetchEvents,
  fetchContractExecution,
  subscribeContractExecution,
  ContractDetail,
  FullAnalysis,
  ContractExecutionState,
} from "../api/client";
import { StatusBadge, RiskBadge } from "../components/Badges";
import { AgentJourney } from "../components/execution/AgentJourney";

type TabKey =
  | "overview"
  | "clauses"
  | "risks"
  | "compliance"
  | "negotiation"
  | "obligations"
  | "disputes"
  | "activity"
  | "ask";

export function ContractWorkspaceView() {
  const { id } = useParams<{ id: string }>();
  const contractId = id || "";
  const navigate = useNavigate();

  const [contract, setContract] = useState<ContractDetail | null>(null);
  const [analysis, setAnalysis] = useState<FullAnalysis | null>(null);
  const [execution, setExecution] = useState<ContractExecutionState | null>(null);
  const [showExecutionPanel, setShowExecutionPanel] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [signing, setSigning] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Q&A State
  const [question, setQuestion] = useState("");
  const [qaLoading, setQaLoading] = useState(false);
  const [qaHistory, setQaHistory] = useState<Array<{ q: string; a: string; model?: string }>>([
    {
      q: "What is our primary financial exposure under this agreement?",
      a: "Under Section 7 (Limitation of Liability), Customer's aggregate liability is completely UNCAPPED, while Vendor's liability is capped at fees paid in the preceding 1 month. In addition, Section 6 imposes an uncapped indemnity obligation on Customer. This creates catastrophic, non-mutual commercial exposure.",
    },
  ]);

  const loadData = async () => {
    if (!contractId) return;
    try {
      const [cData, aData, eData, execData] = await Promise.all([
        fetchContractDetail(contractId),
        fetchContractAnalysis(contractId).catch(() => null),
        fetchEvents(contractId).catch(() => []),
        fetchContractExecution(contractId).catch(() => null),
      ]);
      setContract(cData);
      if (aData) setAnalysis(aData);
      if (eData) setEvents(eData);
      if (execData) setExecution(execData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [contractId]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setShowExecutionPanel(true);
    setSuccessMsg(null);

    const unsubscribe = subscribeContractExecution(contractId, (data) => {
      if (data.execution) {
        setExecution(data.execution);
      }
    });

    try {
      await triggerMeshAnalysis(contractId, undefined, contract?.raw_text, contract?.title);
      await loadData();
      setSuccessMsg("Dynamic Multi-Society analysis completed.");
      setActiveTab("risks");
    } catch (err: any) {
      alert("Analysis failed: " + err.message);
    } finally {
      unsubscribe();
      setAnalyzing(false);
    }
  };

  const handleSign = async () => {
    setSigning(true);
    try {
      await signContract(contractId);
      await loadData();
      setSuccessMsg("Contract signed and obligations registered.");
      setActiveTab("obligations");
    } catch (err: any) {
      alert("Failed to sign: " + err.message);
    } finally {
      setSigning(false);
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    const q = question;
    setQuestion("");
    setQaLoading(true);

    try {
      const res = await askContractQuestion(contractId, q);
      setQaHistory((prev) => [...prev, { q, a: res.answer, model: res.model }]);
    } catch (err: any) {
      setQaHistory((prev) => [
        ...prev,
        { q, a: "Error answering: " + err.message, model: "gemini" },
      ]);
    } finally {
      setQaLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500 text-xs">
        Loading Contract Workspace...
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="p-12 text-center text-rose-600 text-xs">
        Contract {contractId} not found.
      </div>
    );
  }

  const stages = ["INTAKE", "ANALYZED", "APPROVED", "SIGNED", "ACTIVE"];
  const currentStageIndex = stages.indexOf(contract.status.toUpperCase());

  const tabs: Array<{ key: TabKey; label: string; icon: any; count?: number }> = [
    { key: "overview", label: "Overview", icon: FileText },
    {
      key: "clauses",
      label: "Graph Clauses",
      icon: Layers,
      count: analysis?.graph?.clauses?.length,
    },
    {
      key: "risks",
      label: "Risk Debate",
      icon: ShieldAlert,
      count: analysis?.risk_report?.findings?.length,
    },
    {
      key: "compliance",
      label: "Compliance Audit",
      icon: CheckCircle2,
      count: analysis?.compliance_report?.violations_count,
    },
    {
      key: "negotiation",
      label: "Negotiation Redlines",
      icon: Scale,
      count: analysis?.negotiation_strategy?.positions?.length,
    },
    {
      key: "obligations",
      label: "Obligations & Deadlines",
      icon: Clock,
      count: analysis?.obligation_schedule?.total_obligations,
    },
    {
      key: "disputes",
      label: "Dispute Simulation",
      icon: AlertTriangle,
      count: analysis?.dispute_assessment?.scenarios?.length,
    },
    { key: "activity", label: "Event Trail", icon: Activity, count: events.length },
    { key: "ask", label: "Ask CAS", icon: Sparkles },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/contracts"
            className="p-1.5 rounded-md bg-white border border-[#E5E7EB] text-slate-600 hover:text-slate-900 transition-colors shadow-2xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-[#111827]">{contract.title}</h1>
              <StatusBadge status={contract.status} />
              <RiskBadge score={contract.risk_score} />
            </div>
            <div className="text-xs text-[#6B7280] flex items-center gap-3 mt-0.5 font-mono">
              <span>Ref: {contract.id}</span>
              <span>•</span>
              <span>Counterparty: {contract.metadata?.counterparty || "Vendor Corp"}</span>
              <span>•</span>
              <span>Jurisdiction: {contract.governing_law || "Delaware"}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowExecutionPanel(!showExecutionPanel)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border transition-colors cursor-pointer ${
              showExecutionPanel
                ? "bg-blue-50 border-blue-300 text-blue-700 shadow-2xs font-semibold"
                : "bg-white hover:bg-slate-50 text-slate-700 border-[#E5E7EB]"
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-blue-600" />
            <span>{showExecutionPanel ? "Hide Agent Trace" : "Agent Journey Trace"}</span>
          </button>

          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{analyzing ? "Analyzing..." : "Analyze with Mesh"}</span>
          </button>

          {contract.status !== "SIGNED" && (
            <button
              onClick={handleSign}
              disabled={signing}
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
            >
              <Check className="w-3.5 h-3.5" />
              <span>{signing ? "Signing..." : "Sign Contract"}</span>
            </button>
          )}

          <button
            onClick={() => setActiveTab("ask")}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 rounded-md text-xs font-medium border border-[#E5E7EB] transition-colors cursor-pointer shadow-2xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Ask CAS</span>
          </button>
        </div>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-md flex items-center justify-between">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-600 hover:text-emerald-900 cursor-pointer">
            ×
          </button>
        </div>
      )}

      {/* Current Analysis Banner */}
      {(analyzing || execution?.status === "RUNNING") && (
        <div className="p-3.5 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-between shadow-2xs">
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
            <span className="text-xs font-semibold text-blue-900">
              {execution?.current_step
                ? `${execution.current_step.society} is analyzing agreement — ${execution.current_step.agent}: ${execution.current_step.task}`
                : "CAS Director is orchestrating multi-society assessment"}
            </span>
          </div>
          <button
            onClick={() => setShowExecutionPanel(true)}
            className="text-[11px] font-mono text-blue-700 hover:text-blue-900 underline cursor-pointer font-semibold"
          >
            Inspect Vector Road
          </button>
        </div>
      )}

      {/* Animated Vector AgentJourney Trace */}
      {(showExecutionPanel || analyzing || execution?.status === "RUNNING" || execution?.status === "PAUSED_FOR_HUMAN") && execution && (
        <AgentJourney
          execution={execution}
          isAnalyzing={analyzing}
          onReviewDecision={() => navigate("/approvals")}
        />
      )}

      {/* Lifecycle Progress Bar */}
      <div className="bg-white border border-[#E5E7EB] rounded-lg p-3 shadow-xs">
        <div className="flex items-center justify-between">
          {stages.map((stg, idx) => {
            const isCompleted = idx <= currentStageIndex;
            const isCurrent = idx === currentStageIndex;
            return (
              <div key={stg} className="flex-1 flex items-center">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border transition-colors ${
                      isCurrent
                        ? "bg-blue-600 text-white border-blue-600 shadow-xs"
                        : isCompleted
                        ? "bg-emerald-50 text-emerald-700 border-emerald-300 font-bold"
                        : "bg-slate-100 text-slate-400 border-slate-200"
                    }`}
                  >
                    {isCompleted && !isCurrent ? "✓" : idx + 1}
                  </div>
                  <span
                    className={`text-[10px] uppercase font-semibold mt-1 font-mono ${
                      isCurrent
                        ? "text-blue-700"
                        : isCompleted
                        ? "text-slate-700"
                        : "text-slate-400"
                    }`}
                  >
                    {stg}
                  </span>
                </div>
                {idx < stages.length - 1 && (
                  <div
                    className={`h-0.5 flex-1 -mt-4 transition-colors ${
                      idx < currentStageIndex ? "bg-emerald-500" : "bg-slate-200"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Workspace Tabs Navigation */}
      <div className="border-b border-[#E5E7EB] flex items-center gap-1 overflow-x-auto bg-white rounded-t-lg px-2 pt-1">
        {tabs.map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`flex items-center gap-1.5 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors whitespace-nowrap cursor-pointer ${
                isActive
                  ? "border-blue-600 text-blue-700 font-semibold bg-blue-50/50 rounded-t"
                  : "border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <Icon className="w-3.5 h-3.5 shrink-0 text-current" />
              <span>{t.label}</span>
              {t.count !== undefined && (
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                    isActive ? "bg-blue-100 text-blue-800 font-bold" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {t.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="space-y-4">
        {/* 1. OVERVIEW TAB */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
                <span className="text-[11px] text-slate-500 uppercase font-semibold font-mono">
                  Parties Bound
                </span>
                <div className="text-xs text-slate-900 font-semibold">
                  {contract.metadata?.customer || "Acme Global"} ↔ {contract.metadata?.counterparty || "NovaCloud Inc."}
                </div>
                <div className="text-[11px] text-[#6B7280]">Customer ↔ Vendor Relationship</div>
              </div>
              <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
                <span className="text-[11px] text-slate-500 uppercase font-semibold font-mono">
                  Governing Law
                </span>
                <div className="text-xs text-slate-900 font-semibold">
                  {contract.governing_law || "State of Delaware"}
                </div>
                <div className="text-[11px] text-[#6B7280]">Exclusive Jurisdiction</div>
              </div>
              <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
                <span className="text-[11px] text-slate-500 uppercase font-semibold font-mono">
                  Effective Period
                </span>
                <div className="text-xs text-slate-900 font-semibold">
                  {contract.effective_date || "2026-10-01"} → {contract.expiration_date || "2027-10-01"}
                </div>
                <div className="text-[11px] text-[#6B7280]">60-day Non-Renewal Notice Window</div>
              </div>
            </div>

            {/* Verbatim Contract Text Preview */}
            <div className="bg-white border border-[#E5E7EB] rounded-lg p-4 space-y-2 shadow-xs">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider font-mono">
                  Contract Document Source (Verbatim Text)
                </h3>
                <span className="text-[11px] font-mono text-slate-500">
                  {contract.raw_text.length} characters
                </span>
              </div>
              <pre className="p-4 rounded-lg bg-slate-50 font-mono text-xs text-slate-800 leading-relaxed overflow-x-auto max-h-[400px] border border-slate-200 whitespace-pre-wrap">
                {contract.raw_text}
              </pre>
            </div>
          </div>
        )}

        {/* 2. GRAPH CLAUSES TAB */}
        {activeTab === "clauses" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider font-mono">
                  Contract Intelligence: Typed Relational Clauses
                </h3>
                <p className="text-[11px] text-[#6B7280]">
                  Extracted and verified by Parallel + Verification agents
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {analysis?.graph?.clauses && analysis.graph.clauses.length > 0 ? (
                analysis.graph.clauses.map((c) => (
                  <div
                    key={c.clause_id}
                    className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900">{c.title}</span>
                        <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-mono font-medium">
                          {c.category}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-500">
                        ID: {c.clause_id}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 font-mono bg-slate-50 p-2.5 rounded border border-slate-200 leading-relaxed">
                      {c.text}
                    </p>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs bg-white rounded-lg border border-[#E5E7EB]">
                  No clauses analyzed yet. Click &ldquo;Analyze with Mesh&rdquo; above to extract graph clauses.
                </div>
              )}
            </div>
          </div>
        )}

        {/* 3. RISKS TAB (ADVERSARIAL DEBATE) */}
        {activeTab === "risks" && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider font-mono">
                  Adversarial Risk Debate Breakdown
                </h3>
                <p className="text-[11px] text-[#6B7280]">
                  Dialectic adjudication: Risk Hunter vs. Counterargument vs. Synthesis Assessor
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Overall Score:</span>
                <RiskBadge score={analysis?.risk_report?.overall_risk_score} />
                {analysis?.risk_report?.requires_human_escalation && (
                  <span className="px-2 py-0.5 rounded bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold">
                    Escalation Required
                  </span>
                )}
              </div>
            </div>

            <div className="space-y-4">
              {analysis?.risk_report?.findings && analysis.risk_report.findings.length > 0 ? (
                analysis.risk_report.findings.map((f) => (
                  <div
                    key={f.finding_id}
                    className="p-5 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-4"
                  >
                    <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900">{f.risk_type}</span>
                        <RiskBadge level={f.severity} />
                        <span className="text-[10px] font-mono text-slate-500">Clause: {f.clause_id}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">{f.finding_id}</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      {/* Hunter Claim */}
                      <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-200 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-rose-700 tracking-wider">
                          Risk Hunter Claim
                        </span>
                        <p className="text-slate-800 leading-relaxed">{f.hunter_claim}</p>
                      </div>

                      {/* Counterargument */}
                      <div className="p-3 rounded-lg bg-blue-50/60 border border-blue-200 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-blue-700 tracking-wider">
                          Counterargument Defense
                        </span>
                        <p className="text-slate-800 leading-relaxed">{f.counterargument}</p>
                      </div>
                    </div>

                    {/* Assessor Conclusion */}
                    <div className="p-3 rounded-lg bg-amber-50/60 border border-amber-200 space-y-1 text-xs">
                      <span className="text-[10px] uppercase font-bold text-amber-800 tracking-wider">
                        Assessor Adjudication &amp; Consequence
                      </span>
                      <p className="text-slate-900 font-medium leading-relaxed">{f.assessor_conclusion}</p>
                      {f.consequence && (
                        <p className="text-slate-600 text-[11px] mt-1">Consequence: {f.consequence}</p>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs bg-white rounded-lg border border-[#E5E7EB]">
                  No risk debate findings recorded yet. Run mesh analysis to evaluate adversarial risk vectors.
                </div>
              )}
            </div>
          </div>
        )}

        {/* 4. COMPLIANCE TAB */}
        {activeTab === "compliance" && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider font-mono">
                  Corporate Policy Compliance Audit
                </h3>
                <p className="text-[11px] text-[#6B7280]">
                  Grounded against corporate compliance rules and statutory mandates
                </p>
              </div>
              <StatusBadge status={analysis?.compliance_report?.overall_status || "AUDITED"} />
            </div>

            <div className="space-y-3">
              {analysis?.compliance_report?.findings && analysis.compliance_report.findings.length > 0 ? (
                analysis.compliance_report.findings.map((cf) => (
                  <div
                    key={cf.rule_id}
                    className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900">{cf.rule_name}</span>
                        <StatusBadge status={cf.status} />
                      </div>
                      <span className="text-[10px] font-mono text-slate-500">Rule: {cf.rule_id}</span>
                    </div>

                    <p className="text-xs text-slate-700 leading-relaxed">{cf.reasoning}</p>

                    {cf.evidence && (
                      <div className="p-2.5 rounded bg-slate-50 border border-slate-200 text-[11px] text-slate-600 font-mono">
                        <span className="font-semibold text-slate-700 font-sans mr-1">Evidence:</span>
                        &ldquo;{cf.evidence}&rdquo;
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs bg-white rounded-lg border border-[#E5E7EB]">
                  No compliance audit generated yet.
                </div>
              )}
            </div>
          </div>
        )}

        {/* 5. NEGOTIATION TAB */}
        {activeTab === "negotiation" && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs">
              <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider font-mono">
                Autonomous Redline Counter-Positions &amp; Trade-offs
              </h3>
              <p className="text-[11px] text-[#6B7280] mt-1">
                Objective: {analysis?.negotiation_strategy?.primary_objective || "Cap liability and delete uncapped indemnity."}
              </p>
            </div>

            <div className="space-y-4">
              {analysis?.negotiation_strategy?.positions && analysis.negotiation_strategy.positions.length > 0 ? (
                analysis.negotiation_strategy.positions.map((pos, idx) => (
                  <div
                    key={idx}
                    className="p-5 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-3"
                  >
                    <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-2">
                      <span className="text-xs font-bold text-blue-700">Target Clause: {pos.clause_id}</span>
                      <span className="text-[10px] uppercase font-bold text-amber-700 tracking-wider bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        Priority: {pos.priority}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-200 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-rose-700">
                          Current Language (Vendor Draft)
                        </span>
                        <p className="font-mono text-slate-800 text-[11px] leading-relaxed">
                          {pos.current_language}
                        </p>
                      </div>

                      <div className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-emerald-700">
                          Proposed CAS Redline Amendment
                        </span>
                        <p className="font-mono text-emerald-900 text-[11px] leading-relaxed font-semibold">
                          {pos.proposed_redline}
                        </p>
                      </div>
                    </div>

                    {pos.concession_strategy && (
                      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
                        <span className="font-semibold text-slate-900 mr-1.5">Concession Strategy:</span>
                        {pos.concession_strategy}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs bg-white rounded-lg border border-[#E5E7EB]">
                  No negotiation strategy generated yet.
                </div>
              )}
            </div>
          </div>
        )}

        {/* 6. OBLIGATIONS TAB */}
        {activeTab === "obligations" && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider font-mono">
                  Post-Signature Obligations &amp; Milestones
                </h3>
                <p className="text-[11px] text-[#6B7280]">
                  Monitored continuously for operational commitments and delivery dates
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(analysis?.obligation_schedule?.items || analysis?.obligation_schedule?.obligations || []).length > 0 ? (
                (analysis?.obligation_schedule?.items || analysis?.obligation_schedule?.obligations || []).map((ob: any) => (
                  <div
                    key={ob.obligation_id}
                    className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900">{ob.title}</span>
                      <span className="px-2 py-0.5 rounded bg-indigo-50 border border-indigo-200 text-indigo-700 text-[10px] font-mono font-semibold">
                        {ob.obligation_type || ob.type || "DELIVERABLE"}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600 flex items-center justify-between">
                      <span>Responsible Party:</span>
                      <span className="text-slate-900 font-semibold">{ob.party}</span>
                    </div>

                    <div className="text-xs text-slate-600 flex items-center justify-between">
                      <span>Due Date:</span>
                      <span className="text-amber-800 font-mono font-bold">{ob.due_date}</span>
                    </div>

                    {ob.notice_period_days && (
                      <div className="text-[11px] text-slate-500 flex items-center justify-between">
                        <span>Advance Notice Window:</span>
                        <span>{ob.notice_period_days} days</span>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="col-span-2 p-8 text-center text-slate-500 text-xs bg-white rounded-lg border border-[#E5E7EB]">
                  Contract is not yet signed or obligations are not registered. Click &ldquo;Sign Contract&rdquo; above to activate monitoring.
                </div>
              )}
            </div>
          </div>
        )}

        {/* 7. DISPUTES TAB */}
        {activeTab === "disputes" && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider font-mono">
                  Dispute Intelligence &amp; Ambiguity Stress-Testing
                </h3>
                <p className="text-[11px] text-[#6B7280]">
                  Multi-Perspective simulation: Party A vs. Party B conflicting litigation interpretations
                </p>
              </div>
              <RiskBadge level={analysis?.dispute_assessment?.overall_dispute_risk} />
            </div>

            <div className="space-y-4">
              {analysis?.dispute_assessment?.scenarios && analysis.dispute_assessment.scenarios.length > 0 ? (
                analysis.dispute_assessment.scenarios.map((ds) => (
                  <div
                    key={ds.scenario_id}
                    className="p-5 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-3"
                  >
                    <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-2">
                      <span className="text-xs font-bold text-rose-700">
                        Ambiguity Vector: {ds.ambiguity_type} ({ds.clause_id})
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        Court Dispute Likelihood: {ds.court_likelihood}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="p-3 rounded-lg bg-blue-50/60 border border-blue-200 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-blue-700">
                          Customer View (Party A)
                        </span>
                        <p className="text-slate-800 leading-relaxed">{ds.party_a_interpretation}</p>
                      </div>

                      <div className="p-3 rounded-lg bg-purple-50/60 border border-purple-200 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-purple-700">
                          Vendor View (Party B)
                        </span>
                        <p className="text-slate-800 leading-relaxed">{ds.party_b_interpretation}</p>
                      </div>
                    </div>

                    {ds.preventative_redline && (
                      <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 space-y-1 text-xs">
                        <span className="text-[10px] uppercase font-bold text-emerald-800">
                          Preventative Redline Amendment to Preempt Litigation
                        </span>
                        <p className="font-mono text-emerald-900 text-[11px] leading-relaxed font-semibold">
                          {ds.preventative_redline}
                        </p>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs bg-white rounded-lg border border-[#E5E7EB]">
                  No dispute simulations generated yet. Run mesh analysis to stress-test contractual ambiguities.
                </div>
              )}
            </div>
          </div>
        )}

        {/* 8. ACTIVITY TAB */}
        {activeTab === "activity" && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs">
              <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider font-mono">
                Contract Event Bus Trail
              </h3>
              <p className="text-[11px] text-[#6B7280]">
                Audited chronological CASMessage protocol events recorded for this contract
              </p>
            </div>

            <div className="space-y-2">
              {events && events.length > 0 ? (
                events.map((ev) => (
                  <div
                    key={ev.event_id}
                    className="p-3 rounded-lg bg-white border border-[#E5E7EB] flex items-center justify-between text-xs shadow-2xs"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-blue-700">{ev.event_type}</span>
                        <span className="text-slate-500 text-[11px]">
                          ({ev.source} → {ev.target})
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        Event ID: {ev.event_id}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-mono font-medium">
                        Priority: {ev.priority}
                      </span>
                      <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                        {ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : ""}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs bg-white rounded-lg border border-[#E5E7EB]">
                  No events logged for this contract yet.
                </div>
              )}
            </div>
          </div>
        )}

        {/* 9. ASK CAS TAB */}
        {activeTab === "ask" && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <Sparkles className="w-4 h-4 text-blue-600" />
                  Grounded Legal Intelligence
                </h3>
                <p className="text-[11px] text-[#6B7280]">
                  Ask precise legal questions grounded in this agreement&rsquo;s clauses, risk findings, and obligations
                </p>
              </div>
            </div>

            {/* Suggested Prompts */}
            <div className="flex flex-wrap gap-2">
              {[
                "What is our primary financial exposure under this agreement?",
                "Can we terminate without penalty if SLA drops below 99%?",
                "What are the notice requirements for non-renewal?",
                "Are the indemnification obligations bilateral?",
              ].map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setQuestion(suggestion)}
                  className="px-2.5 py-1 rounded bg-slate-50 border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 text-slate-700 text-[11px] transition-colors cursor-pointer text-left"
                >
                  {suggestion}
                </button>
              ))}
            </div>

            {/* Conversation Log */}
            <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
              {qaHistory.map((item, idx) => (
                <div key={idx} className="space-y-2">
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded bg-blue-100 text-blue-700 flex items-center justify-center text-[11px] font-bold shrink-0 mt-0.5">
                      Q
                    </span>
                    <p className="text-xs text-slate-800 font-semibold">{item.q}</p>
                  </div>

                  <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-2xs flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                      CAS
                    </span>
                    <div className="space-y-1 flex-1">
                      <p className="text-xs text-slate-800 leading-relaxed whitespace-pre-wrap">
                        {item.a}
                      </p>
                      <div className="text-[10px] text-slate-400 font-mono pt-1">
                        Grounded in agreement text
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Question Input Form */}
            <form onSubmit={handleAsk} className="flex gap-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about liability caps, indemnity, termination, SLAs, or compliance..."
                className="flex-1 bg-white border border-[#E5E7EB] rounded-md px-3 py-2 text-xs text-[#111827] placeholder:text-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
              <button
                type="submit"
                disabled={qaLoading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{qaLoading ? "Reasoning..." : "Ask"}</span>
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
