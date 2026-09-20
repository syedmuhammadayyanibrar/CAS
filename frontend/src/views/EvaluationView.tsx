import React, { useState, useEffect } from "react";
import {
  EvaluationSummary as EvaluationSummaryType,
  EvaluationCase,
  EvaluationHistoryItem,
  fetchEvaluationSummary,
  fetchEvaluationCases,
  fetchEvaluationHistory,
  runEvaluation,
} from "../api/client";
import { EvaluationSummary } from "../components/evaluation/EvaluationSummary";
import { EvaluationMetrics } from "../components/evaluation/EvaluationMetrics";
import { EvaluationTable } from "../components/evaluation/EvaluationTable";
import { EvaluationDetailDrawer } from "../components/evaluation/EvaluationDetailDrawer";
import { CheckCircle2, History, TrendingUp, AlertCircle } from "lucide-react";

export function EvaluationView() {
  const [summary, setSummary] = useState<EvaluationSummaryType | null>(null);
  const [cases, setCases] = useState<EvaluationCase[]>([]);
  const [history, setHistory] = useState<EvaluationHistoryItem[]>([]);
  const [selectedCase, setSelectedCase] = useState<EvaluationCase | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [sumData, casesData, histData] = await Promise.all([
        fetchEvaluationSummary(),
        fetchEvaluationCases(),
        fetchEvaluationHistory(),
      ]);
      setSummary(sumData);
      setCases((Array.isArray(casesData) ? casesData : (casesData as any).cases || []) as any);
      setHistory(histData.runs);
    } catch (err: any) {
      console.error("Evaluation load error:", err);
      setError(err.message || "Failed to load evaluation benchmark suite");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunEvaluation = async () => {
    try {
      setIsRunning(true);
      await runEvaluation();
      await loadData();
    } catch (err: any) {
      console.error("Run evaluation error:", err);
      alert(`Evaluation run failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-8 text-center text-xs text-slate-500 flex items-center justify-center min-h-[400px]">
        <div className="space-y-2">
          <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <div>Loading CAS Evaluation Benchmark Suite...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 1. Summary Cards */}
      <EvaluationSummary
        summary={summary}
        onRunEvaluation={handleRunEvaluation}
        isRunning={isRunning}
      />

      {/* 2. Subsystem & Category Precision Breakdown */}
      {summary && <EvaluationMetrics summary={summary} cases={cases} />}

      {/* 3. Filterable 30 Ground-Truth Cases Table */}
      <EvaluationTable
        cases={cases}
        onSelectCase={(c) => setSelectedCase(c)}
      />

      {/* 4. Historical Evaluation Runs */}
      {history.length > 0 && (
        <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-slate-500" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
                Historical Benchmark Regressions &amp; Runs
              </h3>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              Continuous Evaluation Pipeline
            </span>
          </div>

          <div className="divide-y divide-[#E5E7EB] border border-[#E5E7EB] rounded-md overflow-hidden">
            {history.map((run) => (
              <div
                key={run.run_id}
                className="p-3 bg-white hover:bg-slate-50 flex items-center justify-between text-xs transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono font-bold text-slate-900 px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                    {run.run_id}
                  </span>
                  <div>
                    <span className="font-semibold text-slate-800 mr-2">
                      Dataset {run.dataset_version}
                    </span>
                    <span className="text-slate-400 text-[11px]">
                      {new Date(run.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4 font-mono text-xs">
                  <span className="text-emerald-700 font-bold">
                    {run.accuracy_pct}% Accuracy
                  </span>
                  <span className="text-slate-500">
                    Routing: {run.routing_accuracy_pct}%
                  </span>
                  <span className="text-slate-500">
                    Risk F1: {run.risk_f1}
                  </span>
                  <span className="text-slate-500">
                    HITL: {run.hitl_accuracy_pct}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Slide-out Case Detail Inspector */}
      <EvaluationDetailDrawer
        isOpen={!!selectedCase}
        onClose={() => setSelectedCase(null)}
        evaluationCase={selectedCase}
      />
    </div>
  );
}
