import React, { useState, useMemo } from "react";
import { Search, Filter, CheckCircle2, XCircle, ChevronRight, ArrowUpDown } from "lucide-react";
import { EvaluationCase } from "../../api/client";

interface EvaluationTableProps {
  cases: EvaluationCase[];
  onSelectCase: (c: EvaluationCase) => void;
}

export function EvaluationTable({ cases, onSelectCase }: EvaluationTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [sortField, setSortField] = useState<"case_id" | "execution_time_ms" | "status">("case_id");
  const [sortAsc, setSortAsc] = useState(true);

  const categories = ["ALL", "Risk", "Compliance", "Adversarial", "Obligation", "Routing", "Dispute"];

  const filteredCases = useMemo(() => {
    return cases
      .filter((c) => {
        if (categoryFilter !== "ALL" && c.category.toLowerCase() !== categoryFilter.toLowerCase()) {
          return false;
        }
        if (statusFilter !== "ALL" && c.status.toLowerCase() !== statusFilter.toLowerCase()) {
          return false;
        }
        if (searchTerm.trim()) {
          const term = searchTerm.toLowerCase();
          const matchId = c.case_id.toLowerCase().includes(term);
          const matchScenario = c.scenario.toLowerCase().includes(term);
          const matchContract = c.contract_id.toLowerCase().includes(term);
          if (!matchId && !matchScenario && !matchContract) return false;
        }
        return true;
      })
      .sort((a, b) => {
        let cmp = 0;
        if (sortField === "case_id") {
          cmp = a.case_id.localeCompare(b.case_id);
        } else if (sortField === "execution_time_ms") {
          cmp = a.execution_time_ms - b.execution_time_ms;
        } else if (sortField === "status") {
          cmp = a.status.localeCompare(b.status);
        }
        return sortAsc ? cmp : -cmp;
      });
  }, [cases, searchTerm, categoryFilter, statusFilter, sortField, sortAsc]);

  const toggleSort = (field: "case_id" | "execution_time_ms" | "status") => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  return (
    <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-4">
      {/* Controls: Search and Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search benchmark cases by ID, scenario, or contract..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-md border border-[#E5E7EB] bg-white text-xs text-[#111827] placeholder:text-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
          {/* Status Filter */}
          <div className="flex items-center rounded-md border border-[#E5E7EB] p-0.5 bg-slate-50 text-xs">
            <button
              onClick={() => setStatusFilter("ALL")}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
                statusFilter === "ALL" ? "bg-white text-slate-900 shadow-2xs font-semibold" : "text-slate-600"
              }`}
            >
              All ({cases.length})
            </button>
            <button
              onClick={() => setStatusFilter("PASSED")}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
                statusFilter === "PASSED" ? "bg-emerald-50 text-emerald-800 shadow-2xs font-semibold" : "text-slate-600"
              }`}
            >
              Passed ({cases.filter((c) => c.status === "PASSED").length})
            </button>
            <button
              onClick={() => setStatusFilter("FAILED")}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
                statusFilter === "FAILED" ? "bg-rose-50 text-rose-800 shadow-2xs font-semibold" : "text-slate-600"
              }`}
            >
              Failed ({cases.filter((c) => c.status === "FAILED").length})
            </button>
          </div>

          {/* Category Dropdown */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-md border border-[#E5E7EB] bg-white text-xs text-slate-700 focus:outline-hidden focus:border-blue-500 cursor-pointer"
          >
            {categories.map((c) => (
              <option key={c} value={c}>
                {c === "ALL" ? "All Categories" : c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-md border border-[#E5E7EB]">
        <table className="w-full text-left text-xs text-slate-700">
          <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500 font-semibold border-b border-[#E5E7EB]">
            <tr>
              <th
                onClick={() => toggleSort("case_id")}
                className="py-2.5 px-3 cursor-pointer hover:text-slate-800"
              >
                <div className="flex items-center gap-1 font-mono">
                  <span>Case ID</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th className="py-2.5 px-3">Scenario &amp; Ground Truth Objective</th>
              <th className="py-2.5 px-3">Category</th>
              <th
                onClick={() => toggleSort("execution_time_ms")}
                className="py-2.5 px-3 cursor-pointer hover:text-slate-800"
              >
                <div className="flex items-center gap-1 font-mono">
                  <span>Latency</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th
                onClick={() => toggleSort("status")}
                className="py-2.5 px-3 cursor-pointer hover:text-slate-800"
              >
                <div className="flex items-center gap-1">
                  <span>Result</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th className="py-2.5 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E5E7EB] bg-white">
            {filteredCases.map((c) => {
              const isPassed = c.status === "PASSED";

              return (
                <tr
                  key={c.case_id}
                  onClick={() => onSelectCase(c)}
                  className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                >
                  <td className="py-3 px-3 font-mono font-bold text-slate-900">
                    {c.case_id}
                  </td>
                  <td className="py-3 px-3">
                    <div className="font-semibold text-[#111827]">{c.scenario}</div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      {c.contract_id}
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 text-[11px] font-medium">
                      {c.category}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-500">
                    {c.execution_time_ms}ms
                  </td>
                  <td className="py-3 px-3">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold ${
                        isPassed
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                          : "bg-rose-50 text-rose-800 border border-rose-200"
                      }`}
                    >
                      {isPassed ? (
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      ) : (
                        <XCircle className="w-3 h-3 text-rose-600" />
                      )}
                      <span>{c.status}</span>
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCase(c);
                      }}
                      className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium cursor-pointer"
                    >
                      <span>Inspect</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500 px-1">
        <span>
          Showing {filteredCases.length} of {cases.length} benchmark scenarios
        </span>
        <span>
          Ground-truth validation set v1.0
        </span>
      </div>
    </div>
  );
}
