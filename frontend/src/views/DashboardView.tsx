import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldAlert,
  Cpu,
  Zap,
} from "lucide-react";
import { fetchDashboardSummary, DashboardSummary } from "../api/client";
import { StatusBadge, RiskBadge } from "../components/Badges";

export function DashboardView() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const loadData = async () => {
    try {
      const summary = await fetchDashboardSummary();
      setData(summary);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px] text-slate-500 text-xs">
        <div className="space-y-2 text-center">
          <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <div>Loading CAS Portfolio Metrics...</div>
        </div>
      </div>
    );
  }

  const p = data?.portfolio || {
    total_contracts: 0,
    status_counts: {},
    high_risk_count: 0,
    pending_reviews_count: 0,
    total_obligations: 0,
  };

  const activeCount = (p.status_counts["SIGNED"] || 0) + (p.status_counts["APPROVED"] || 0);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner: Greeting & Operational Status */}
      <div className="p-5 rounded-xl bg-white border border-[#E5E7EB] shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-bold text-blue-700 uppercase tracking-wider font-mono">
              Autonomous Operations
            </span>
          </div>
          <h2 className="text-lg font-bold text-[#111827]">
            Good morning — Here&rsquo;s what&rsquo;s happening across your contracts
          </h2>
          <p className="text-xs text-[#6B7280]">
            6 federated agent societies actively monitoring negotiations, risks, obligations, and disputes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate("/demo")}
            className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
          >
            <span>Interactive Demo</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Metrics Row: 5 compact KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {/* Active Contracts */}
        <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs">
            <span className="font-medium">Active Contracts</span>
            <FileText className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-[#111827]">{p.total_contracts}</div>
          <div className="text-[11px] text-[#6B7280]">
            <span className="text-emerald-700 font-semibold">{activeCount} signed</span> · {p.status_counts["ANALYZED"] || 0} analyzed
          </div>
        </div>

        {/* Pending Approvals */}
        <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs">
            <span className="font-medium">Pending Reviews</span>
            <CheckCircle2 className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-600">{p.pending_reviews_count}</div>
          <div className="text-[11px] text-[#6B7280]">
            Awaiting human sign-off
          </div>
        </div>

        {/* Active Operations */}
        <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs">
            <span className="font-medium">Active Operations</span>
            <Zap className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-700">
            {data?.active_operations?.length || 1}
          </div>
          <div className="text-[11px] text-[#6B7280]">
            Live agent tasks running
          </div>
        </div>

        {/* Open Risks */}
        <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs">
            <span className="font-medium">Open Risks</span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-600">{p.high_risk_count}</div>
          <div className="text-[11px] text-[#6B7280]">
            High or critical severity flags
          </div>
        </div>

        {/* Upcoming Obligations */}
        <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs">
            <span className="font-medium">Tracked Obligations</span>
            <Clock className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-indigo-700">{p.total_obligations}</div>
          <div className="text-[11px] text-[#6B7280]">
            Calendar notices &amp; sync
          </div>
        </div>
      </div>

      {/* Main Operations Grid: Active Operations + Contracts Portfolio */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Contracts (2 cols) */}
        <div className="lg:col-span-2 bg-white border border-[#E5E7EB] rounded-lg p-5 space-y-4 shadow-xs">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider font-mono">
                Recent Contract Portfolio
              </h3>
              <p className="text-[11px] text-[#6B7280]">
                Agreements processed across autonomous legal societies
              </p>
            </div>
            <Link
              to="/contracts"
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 font-medium"
            >
              View All ({p.total_contracts})
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto rounded-md border border-[#E5E7EB]">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[11px] text-slate-500 uppercase tracking-wider font-semibold border-b border-[#E5E7EB]">
                <tr>
                  <th className="py-2.5 px-3">Agreement</th>
                  <th className="py-2.5 px-3">Counterparty</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Risk Score</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB] bg-white">
                {data?.recent_contracts && data.recent_contracts.length > 0 ? (
                  data.recent_contracts.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-3 font-medium text-slate-900">
                        <Link
                          to={`/contracts/${c.id}`}
                          className="hover:text-blue-600 transition-colors font-semibold"
                        >
                          {c.title}
                        </Link>
                        <div className="text-[10px] text-slate-400 font-mono">{c.id}</div>
                      </td>
                      <td className="py-3 px-3 text-slate-700">{c.counterparty || "Vendor Corp"}</td>
                      <td className="py-3 px-3">
                        <StatusBadge status={c.status} />
                      </td>
                      <td className="py-3 px-3">
                        <RiskBadge score={c.risk_score} />
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Link
                          to={`/contracts/${c.id}`}
                          className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-medium transition-colors inline-block"
                        >
                          Workspace
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-slate-400">
                      No contracts uploaded yet. Click &ldquo;Upload Contract&rdquo; or run the interactive demo.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* ACTIVE OPERATIONS (1 col) - Prominent Live Section */}
        <div className="bg-white border border-[#E5E7EB] rounded-lg p-5 space-y-4 shadow-xs flex flex-col">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider font-mono">
                Active Operations
              </h3>
            </div>
            <span className="text-[10px] text-emerald-700 font-mono font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Live Feed
            </span>
          </div>

          <div className="space-y-3 overflow-y-auto max-h-[380px] pr-1 flex-1 text-xs">
            {data?.active_operations && data.active_operations.length > 0 ? (
              data.active_operations.map((op, idx) => (
                <Link
                  key={idx}
                  to={`/contracts/${op.contract_id}`}
                  className="block p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5 hover:border-blue-300 hover:bg-blue-50/40 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                      {op.title}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-700 font-mono shrink-0 ml-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      {op.status === "RUNNING" || op.status === "Running"
                        ? `Running · ${op.elapsed_seconds || 14}s`
                        : op.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-blue-700 font-medium">
                    {op.society} <span className="text-slate-400">·</span> {op.agent}
                  </div>
                  <div className="text-[11px] text-slate-600 line-clamp-2 font-mono">
                    {op.task}
                  </div>
                </Link>
              ))
            ) : data?.recent_contracts && data.recent_contracts.length > 0 ? (
              data.recent_contracts.slice(0, 3).map((c) => (
                <Link
                  key={c.id}
                  to={`/contracts/${c.id}`}
                  className="block p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1 hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-900 line-clamp-1">
                      {c.title}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">{c.status}</span>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {c.counterparty || "Counterparty"}
                  </div>
                </Link>
              ))
            ) : (
              <div className="py-8 text-center text-slate-400 text-xs">
                No active operations at this moment.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Societies Strip */}
      <div className="p-5 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-600" />
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider font-mono">
              Agent Societies Topology
            </h3>
          </div>
          <Link
            to="/societies"
            className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
          >
            Explore Societies <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {data?.societies?.map((s) => (
            <div
              key={s.id}
              className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5 hover:border-slate-300 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">{s.name}</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
              </div>
              <div className="text-[11px] text-blue-700 font-mono font-medium">
                {s.architecture}
              </div>
              <p className="text-[11px] text-slate-600 line-clamp-2">{s.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
