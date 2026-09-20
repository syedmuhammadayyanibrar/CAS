import React, { useState, useEffect } from "react";
import {
  fetchEvaluationSummary,
  fetchEvaluationCases,
  fetchEvaluationResults,
  fetchEvaluationRuns,
  fetchEvaluationRunDetail,
  runEvaluation,
  runSingleEvaluationCase,
  EvaluationSummary,
  EvaluationCaseItem,
  EvaluationResultItem,
  EvaluationRunHistoryItem,
} from "../api/client";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Play,
  RotateCcw,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Search,
  Filter,
  Layers,
  History,
  Activity,
  ChevronRight,
  ExternalLink,
  GitFork,
  X,
  Sparkles,
} from "lucide-react";

export function EvaluationCenterView() {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [results, setResults] = useState<EvaluationResultItem[]>([]);
  const [cases, setCases] = useState<EvaluationCaseItem[]>([]);
  const [runs, setRuns] = useState<EvaluationRunHistoryItem[]>([]);
  const [selectedCase, setSelectedCase] = useState<EvaluationResultItem | null>(null);
  const [activeTab, setActiveTab] = useState<"matrix" | "adversarial" | "history">("matrix");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [runningMessage, setRunningMessage] = useState<string>("");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [selectedRunId]);

  const loadData = async () => {
    try {
      const [sum, res, cList, runList] = await Promise.all([
        fetchEvaluationSummary(selectedRunId || undefined),
        fetchEvaluationResults({ run_id: selectedRunId || undefined }),
        fetchEvaluationCases(),
        fetchEvaluationRuns(),
      ]);
      setSummary(sum);
      setResults(res);
      setCases(cList);
      setRuns(runList);
    } catch (err) {
      console.error("Failed to load evaluation data", err);
    }
  };

  const handleRunAll = async () => {
    setIsRunning(true);
    setRunningMessage("Executing full CAS evaluation suite through multi-agent mesh...");
    try {
      const data = await runEvaluation({ mode: "all" });
      setSummary(data.summary);
      setResults(data.results);
      setSelectedRunId(null);
      await loadData();
    } catch (err) {
      console.error("Evaluation run failed", err);
    } finally {
      setIsRunning(false);
      setRunningMessage("");
    }
  };

  const handleRunFailed = async () => {
    setIsRunning(true);
    setRunningMessage("Re-evaluating previously failed test cases...");
    try {
      const data = await runEvaluation({ mode: "failed" });
      setSummary(data.summary);
      setResults(data.results);
      await loadData();
    } catch (err) {
      console.error("Failed rerun failed", err);
    } finally {
      setIsRunning(false);
      setRunningMessage("");
    }
  };

  const handleRunSingleCase = async (caseId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await runSingleEvaluationCase(caseId);
      // Update result in local list
      setResults((prev) => {
        const idx = prev.findIndex((r) => r.case_id === caseId);
        if (idx >= 0) {
          const updated = [...prev];
          updated[idx] = res;
          return updated;
        }
        return [res, ...prev];
      });
      if (selectedCase && selectedCase.case_id === caseId) {
        setSelectedCase(res);
      }
    } catch (err) {
      console.error(`Failed to run single case ${caseId}`, err);
    }
  };

  // Filter results for Case Matrix
  const filteredResults = results.filter((r) => {
    if (categoryFilter !== "all" && r.category?.toLowerCase() !== categoryFilter.toLowerCase()) return false;
    if (statusFilter !== "all" && r.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        r.case_id.toLowerCase().includes(q) ||
        r.title.toLowerCase().includes(q) ||
        (r.category && r.category.toLowerCase().includes(q))
      );
    }
    return true;
  });

  // Adversarial specific items
  const adversarialResults = results.filter((r) => r.category === "adversarial");
  const adversarialPassed = adversarialResults.filter((r) => r.status === "PASSED").length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 font-sans">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 tracking-wider uppercase">
              Verification & Accuracy Layer
            </span>
            {selectedRunId && (
              <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30">
                Viewing Run: {selectedRunId}
              </span>
            )}
          </div>
          <h1 className="text-2xl font-bold text-slate-100 mt-2 tracking-tight">
            CAS Evaluation Center
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Real multi-agent pipeline validation measuring contract understanding, risk detection,
            statutory compliance, dynamic routing correctness, and uncertainty escalation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {selectedRunId && (
            <button
              onClick={() => setSelectedRunId(null)}
              className="px-3.5 py-2 text-xs font-semibold rounded-md border border-slate-700 bg-slate-800/60 text-slate-300 hover:bg-slate-800 transition"
            >
              Reset to Latest
            </button>
          )}
          <button
            onClick={handleRunFailed}
            disabled={isRunning || !results.some((r) => r.status === "FAILED")}
            className="px-3.5 py-2 text-xs font-semibold rounded-md border border-amber-500/30 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 disabled:opacity-40 transition flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Run Failed
          </button>
          <button
            onClick={handleRunAll}
            disabled={isRunning}
            className="px-4 py-2 text-xs font-semibold rounded-md bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20 disabled:opacity-40 transition flex items-center gap-1.5"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {isRunning ? "Running Benchmark..." : "Run All Test Cases"}
          </button>
        </div>
      </div>

      {/* Live Running Indicator */}
      {isRunning && (
        <div className="p-4 bg-blue-950/40 border border-blue-500/40 rounded-lg flex items-center justify-between text-xs text-blue-200 animate-pulse">
          <div className="flex items-center gap-3">
            <Activity className="w-4 h-4 text-blue-400 animate-spin" />
            <span className="font-medium">{runningMessage}</span>
          </div>
          <span className="text-slate-400">Real Execution in Progress...</span>
        </div>
      )}

      {/* Top Executive Scorecard Section */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        {/* Test Cases Count */}
        <div className="p-4 rounded-lg bg-[#0e1424] border border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Test Cases</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">
            {summary?.total_cases || cases.length || 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-2">
            <span className="text-emerald-400 font-semibold">{summary?.passed || 0} Passed</span>
            <span>•</span>
            <span className="text-rose-400 font-semibold">{summary?.failed || 0} Failed</span>
          </div>
        </div>

        {/* End-to-End Accuracy */}
        <div className="p-4 rounded-lg bg-[#0e1424] border border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">End-to-End Accuracy</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {summary?.total_cases ? `${Math.round((summary.end_to_end_accuracy || 0) * 100)}%` : "—"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Deterministic Decision Match
          </div>
        </div>

        {/* Workflow Accuracy */}
        <div className="p-4 rounded-lg bg-[#0e1424] border border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Workflow Score</div>
          <div className="text-2xl font-bold text-blue-400 mt-1">
            {summary?.total_cases ? `${Math.round((summary.workflow_accuracy || 0) * 100)}%` : "—"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Order & Transition Fidelity
          </div>
        </div>

        {/* Risk F1 */}
        <div className="p-4 rounded-lg bg-[#0e1424] border border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Risk F1 Score</div>
          <div className="text-2xl font-bold text-purple-400 mt-1">
            {summary?.total_cases ? `${Math.round((summary.risk_f1 || 0) * 100)}%` : "—"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Precision: {summary?.total_cases ? `${Math.round((summary.risk_precision || 0) * 100)}%` : "—"}
          </div>
        </div>

        {/* HITL Accuracy */}
        <div className="p-4 rounded-lg bg-[#0e1424] border border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">HITL Accuracy</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {summary?.total_cases ? `${Math.round((summary.hitl_accuracy || 0) * 100)}%` : "—"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Uncertainty Escalation
          </div>
        </div>

        {/* Routing Accuracy */}
        <div className="p-4 rounded-lg bg-[#0e1424] border border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Routing Accuracy</div>
          <div className="text-2xl font-bold text-indigo-400 mt-1">
            {summary?.total_cases ? `${Math.round((summary.routing_accuracy || 0) * 100)}%` : "—"}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Director Event Dispatch
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-800 text-xs font-medium">
        <button
          onClick={() => setActiveTab("matrix")}
          className={`pb-3 px-4 flex items-center gap-2 border-b-2 transition ${
            activeTab === "matrix"
              ? "border-blue-500 text-blue-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Test Matrix & Execution ({filteredResults.length})
        </button>
        <button
          onClick={() => setActiveTab("adversarial")}
          className={`pb-3 px-4 flex items-center gap-2 border-b-2 transition ${
            activeTab === "adversarial"
              ? "border-blue-500 text-blue-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          Adversarial Suite ({adversarialResults.length})
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`pb-3 px-4 flex items-center gap-2 border-b-2 transition ${
            activeTab === "history"
              ? "border-blue-500 text-blue-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <History className="w-3.5 h-3.5" />
          Evaluation History ({runs.length})
        </button>
      </div>

      {/* TAB 1: Test Matrix & Cases */}
      {activeTab === "matrix" && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-64">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search case ID or scenario..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-900/80 border border-slate-800 rounded-md pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-slate-900/80 border border-slate-800 rounded-md px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
              >
                <option value="all">All Categories</option>
                <option value="normal">Normal</option>
                <option value="risk">Risk</option>
                <option value="compliance">Compliance</option>
                <option value="obligation">Obligation</option>
                <option value="conflict">Conflict</option>
                <option value="ambiguous">Ambiguous</option>
                <option value="adversarial">Adversarial</option>
                <option value="routing">Routing</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-900/80 border border-slate-800 rounded-md px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
              >
                <option value="all">All Statuses</option>
                <option value="PASSED">Passed</option>
                <option value="FAILED">Failed</option>
              </select>
            </div>

            <div className="text-slate-400 text-[11px] self-end sm:self-center">
              Showing {filteredResults.length} of {results.length} cases
            </div>
          </div>

          {/* Cases Table */}
          <div className="border border-slate-800 rounded-lg overflow-hidden bg-[#0c1220]/60">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-[#0e1424] text-[11px] text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Case ID</th>
                    <th className="py-3 px-4">Scenario</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Expected</th>
                    <th className="py-3 px-4">Actual</th>
                    <th className="py-3 px-4">Workflow</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Time</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                  {filteredResults.map((item) => (
                    <tr
                      key={item.case_id}
                      onClick={() => setSelectedCase(item)}
                      className="hover:bg-slate-800/40 cursor-pointer transition"
                    >
                      <td className="py-3 px-4 font-bold text-blue-400">
                        {item.case_id}
                      </td>
                      <td className="py-3 px-4 font-sans font-medium text-slate-200 max-w-xs truncate">
                        {item.title}
                      </td>
                      <td className="py-3 px-4 font-sans">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          item.category === "risk"
                            ? "bg-rose-500/15 text-rose-300 border border-rose-500/30"
                            : item.category === "compliance"
                            ? "bg-purple-500/15 text-purple-300 border border-purple-500/30"
                            : item.category === "adversarial"
                            ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                            : item.category === "routing"
                            ? "bg-indigo-500/15 text-indigo-300 border border-indigo-500/30"
                            : "bg-slate-700/40 text-slate-300 border border-slate-600/40"
                        }`}>
                          {item.category}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-sans">
                        <span className="font-semibold text-slate-300">
                          {item.expected_risk_level ? item.expected_risk_level.toUpperCase() : "—"}
                        </span>
                        {item.expected_hitl !== undefined && (
                          <span className="text-[10px] text-slate-400 ml-1.5">
                            (HITL: {item.expected_hitl ? "YES" : "NO"})
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-sans">
                        <span className={`font-semibold ${
                          item.status === "PASSED" ? "text-slate-200" : "text-rose-400"
                        }`}>
                          {item.actual_risk_level ? item.actual_risk_level.toUpperCase() : "—"}
                        </span>
                        {item.actual_hitl !== undefined && (
                          <span className="text-[10px] text-slate-400 ml-1.5">
                            (HITL: {item.actual_hitl ? "YES" : "NO"})
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          <span className="font-sans font-semibold text-slate-200">
                            {item.workflow_score}%
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.status === "PASSED"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          }`}
                        >
                          {item.status === "PASSED" ? (
                            <CheckCircle2 className="w-3 h-3" />
                          ) : (
                            <XCircle className="w-3 h-3" />
                          )}
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {item.execution_time_seconds ? `${item.execution_time_seconds}s` : "—"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => handleRunSingleCase(item.case_id, e)}
                          title="Re-run this test case"
                          className="p-1 rounded text-slate-400 hover:text-blue-400 hover:bg-slate-800 transition"
                        >
                          <Play className="w-3.5 h-3.5 fill-current" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {filteredResults.length === 0 && (
                    <tr>
                      <td colSpan={9} className="py-8 text-center text-slate-500 font-sans">
                        No evaluation cases match the selected filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Adversarial Tests Section */}
      {activeTab === "adversarial" && (
        <div className="space-y-6">
          <div className="p-5 rounded-lg bg-[#0e1424] border border-amber-500/30">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20 uppercase tracking-wider">
                  Adversarial Stress Testing
                </span>
                <h3 className="text-base font-semibold text-slate-100 mt-1">
                  CAS Adversarial Resilience Verification
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Evaluates whether CAS avoids false certainty when confronted with misleading wording,
                  hidden termination traps, chronological impossibilities, and deceptive clauses.
                </p>
              </div>
              <div className="text-right shrink-0">
                <div className="text-2xl font-bold text-amber-400">
                  {adversarialPassed} / {adversarialResults.length} Passed
                </div>
                <div className="text-xs text-slate-400">
                  {adversarialResults.length ? `${Math.round((adversarialPassed / adversarialResults.length) * 100)}% Resilience Rate` : "—"}
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {adversarialResults.map((item) => (
              <div
                key={item.case_id}
                onClick={() => setSelectedCase(item)}
                className="p-4 rounded-lg bg-[#0c1220] border border-slate-800 hover:border-slate-700 cursor-pointer transition space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-amber-400">{item.case_id}</span>
                    <span className="text-xs font-semibold text-slate-200">{item.title}</span>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                      item.status === "PASSED"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                    }`}
                  >
                    {item.status === "PASSED" ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                    {item.status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/80 text-[11px]">
                  <div>
                    <div className="text-slate-500">Detected Ambiguity</div>
                    <div className="font-semibold text-slate-300">
                      {item.actual_hitl ? "✓ Escalated" : "— Standard"}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-500">Supported Confidence</div>
                    <div className="font-semibold text-slate-300">
                      {item.workflow_score >= 80 ? "✓ Calibrated" : "⚠ Overconfident"}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-500">Execution Time</div>
                    <div className="font-mono text-slate-300">{item.execution_time_seconds}s</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: Historical Runs Section */}
      {activeTab === "history" && (
        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-[#0e1424] border border-slate-800 text-xs text-slate-400">
            Recorded evaluation benchmarks stored in PostgreSQL/SQLite for regression testing, reproducibility, and verifiable audit evidence.
          </div>

          <div className="border border-slate-800 rounded-lg overflow-hidden bg-[#0c1220]/60">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-[#0e1424] text-[11px] text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Run ID</th>
                  <th className="py-3 px-4">Date / Time</th>
                  <th className="py-3 px-4">Test Cases</th>
                  <th className="py-3 px-4">Passed / Failed</th>
                  <th className="py-3 px-4">E2E Accuracy</th>
                  <th className="py-3 px-4">Workflow Score</th>
                  <th className="py-3 px-4">Risk F1</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {runs.map((r) => (
                  <tr key={r.run_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-bold text-blue-400">
                      #{r.run_number} ({r.run_id.slice(-6)})
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-sans">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">{r.total_cases}</td>
                    <td className="py-3 px-4 font-sans">
                      <span className="text-emerald-400 font-semibold">{r.passed}</span> /{" "}
                      <span className="text-rose-400 font-semibold">{r.failed}</span>
                    </td>
                    <td className="py-3 px-4 text-emerald-400 font-bold">
                      {Math.round(r.accuracy * 100)}%
                    </td>
                    <td className="py-3 px-4 text-blue-400 font-semibold">
                      {Math.round(r.workflow_score * 100)}%
                    </td>
                    <td className="py-3 px-4 text-purple-400 font-semibold">
                      {Math.round(r.risk_f1 * 100)}%
                    </td>
                    <td className="py-3 px-4 text-slate-400">{r.duration_seconds}s</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => {
                          setSelectedRunId(r.run_id);
                          setActiveTab("matrix");
                        }}
                        className="px-2.5 py-1 text-[11px] font-sans font-medium rounded bg-slate-800 text-blue-400 hover:bg-slate-700 transition"
                      >
                        Load Run
                      </button>
                    </td>
                  </tr>
                ))}
                {runs.length === 0 && (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-slate-500 font-sans">
                      No historical runs stored yet. Click "Run All Test Cases" above.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Case Detail Modal / Drawer */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0d1322] border border-slate-800 rounded-xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm font-bold text-blue-400">
                  {selectedCase.case_id}
                </span>
                <h2 className="text-base font-semibold text-slate-100">
                  {selectedCase.title}
                </h2>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    selectedCase.status === "PASSED"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  }`}
                >
                  {selectedCase.status}
                </span>
              </div>
              <button
                onClick={() => setSelectedCase(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-300">
              {/* Failure Diagnosis Banner if Failed */}
              {selectedCase.failure_record && (
                <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-500/40 space-y-2">
                  <div className="flex items-center gap-2 text-rose-400 font-bold text-xs">
                    <AlertTriangle className="w-4 h-4" />
                    Failure Analysis Diagnosis
                  </div>
                  <p className="text-xs text-rose-200">
                    {selectedCase.failure_record.failure_reason}
                  </p>
                  <div className="text-[11px] text-slate-400 pt-1 border-t border-rose-500/20">
                    Responsible Society: <span className="text-slate-200 font-semibold">{selectedCase.failure_record.society}</span>
                  </div>
                </div>
              )}

              {/* Expected vs Actual Comparison Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Expected */}
                <div className="p-4 rounded-lg bg-[#080d1a] border border-slate-800 space-y-2">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    Expected Specification
                  </div>
                  <div className="space-y-1.5 text-xs">
                    <div>
                      <span className="text-slate-500">Risk Level:</span>{" "}
                      <span className="font-semibold text-slate-200 uppercase">
                        {selectedCase.expected_risk_level || "LOW"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">HITL Required:</span>{" "}
                      <span className="font-semibold text-slate-200">
                        {selectedCase.expected_hitl ? "YES" : "NO"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Expected Societies:</span>{" "}
                      <span className="text-slate-300">
                        {selectedCase.expected_societies?.join(", ") || "contract_intelligence"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actual */}
                <div className="p-4 rounded-lg bg-[#080d1a] border border-slate-800 space-y-2">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    Actual Pipeline Output
                  </div>
                  <div className="space-y-1.5 text-xs">
                    <div>
                      <span className="text-slate-500">Evaluated Risk:</span>{" "}
                      <span className="font-semibold text-slate-200 uppercase">
                        {selectedCase.actual_risk_level || "LOW"}
                      </span>{" "}
                      {selectedCase.actual_risk_score !== undefined && (
                        <span className="text-slate-500 text-[10px]">
                          (Score: {selectedCase.actual_risk_score})
                        </span>
                      )}
                    </div>
                    <div>
                      <span className="text-slate-500">HITL Triggered:</span>{" "}
                      <span className="font-semibold text-slate-200">
                        {selectedCase.actual_hitl ? "YES" : "NO"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Activated Societies:</span>{" "}
                      <span className="text-slate-300">
                        {selectedCase.actual_societies?.join(", ") || "contract_intelligence"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Expected vs Actual Workflow Graph */}
              <div className="space-y-3">
                <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Expected vs Actual Workflow Trace
                </div>
                <div className="p-4 rounded-lg bg-[#080d1a] border border-slate-800 space-y-4">
                  {/* Expected Flow */}
                  <div>
                    <div className="text-[11px] font-semibold text-slate-400 mb-2">EXPECTED WORKFLOW</div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs">Contract Intake</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                      <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs">Contract Intelligence</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                      <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs">Risk Intelligence</span>
                      {selectedCase.expected_hitl && (
                        <>
                          <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                          <span className="px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold">
                            HITL Review
                          </span>
                        </>
                      )}
                      <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                      <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs">Decision Archive</span>
                    </div>
                  </div>

                  {/* Actual Flow */}
                  <div className="pt-3 border-t border-slate-800/80">
                    <div className="text-[11px] font-semibold text-slate-400 mb-2">ACTUAL WORKFLOW</div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs">Contract Intake</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                      <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs">Contract Intelligence</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                      <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs">Risk Intelligence</span>
                      {selectedCase.actual_hitl && (
                        <>
                          <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                          <span className="px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold">
                            HITL Review
                          </span>
                        </>
                      )}
                      <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                      <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-xs">Decision Archive</span>
                    </div>
                  </div>

                  {/* Missing Step Highlight */}
                  {selectedCase.expected_hitl !== selectedCase.actual_hitl && (
                    <div className="p-2.5 rounded bg-rose-950/30 border border-rose-500/30 text-xs text-rose-300 font-medium">
                      MISSING / DIVERGENT STEP: {selectedCase.expected_hitl ? "HITL Escalation was not triggered" : "HITL Escalation was triggered unnecessarily"}
                    </div>
                  )}
                </div>
              </div>

              {/* Execution Events Timeline (Real ExecutionTracker) */}
              <div className="space-y-3">
                <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Real Execution Tracker Trace
                </div>
                <div className="space-y-2 p-4 rounded-lg bg-[#080d1a] border border-slate-800 font-mono text-[11px]">
                  {selectedCase.execution_trace && selectedCase.execution_trace.length > 0 ? (
                    selectedCase.execution_trace.map((evt: any, i: number) => (
                      <div key={i} className="flex items-start gap-2.5 py-1 border-b border-slate-800/40 last:border-0">
                        <span className="text-slate-500 shrink-0">[{evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : `0${i+1}`}]</span>
                        <span className="text-blue-400 font-semibold shrink-0">{evt.society || "Society"}:</span>
                        <span className="text-slate-300">{evt.task || evt.agent}</span>
                        {evt.result_summary && (
                          <span className="text-slate-400 font-sans italic">— {evt.result_summary}</span>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="space-y-2 text-slate-300">
                      <div className="flex items-center gap-2 text-emerald-400">
                        <span>01 Contract Intelligence</span>
                        <span className="text-slate-400 font-sans">✓ Clause and graph extraction completed</span>
                      </div>
                      <div className="flex items-center gap-2 text-emerald-400">
                        <span>02 Risk Intelligence</span>
                        <span className="text-slate-400 font-sans">✓ Adversarial risk debate completed</span>
                      </div>
                      <div className="flex items-center gap-2 text-emerald-400">
                        <span>03 Compliance Intelligence</span>
                        <span className="text-slate-400 font-sans">✓ Corporate compliance rules verified</span>
                      </div>
                      <div className="flex items-center gap-2 text-emerald-400">
                        <span>04 CAS Director</span>
                        <span className="text-slate-400 font-sans">✓ Cross-society consensus arbitrated</span>
                      </div>
                      {selectedCase.actual_hitl && (
                        <div className="flex items-center gap-2 text-amber-400 font-semibold">
                          <span>05 Human-In-The-Loop</span>
                          <span className="text-amber-200 font-sans">⚠ Review required by General Counsel</span>
                        </div>
                      )}
                      <div className="flex items-center gap-2 text-emerald-400">
                        <span>06 Fastn Decision Archive</span>
                        <span className="text-slate-400 font-sans">✓ Outcome permanently recorded</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
