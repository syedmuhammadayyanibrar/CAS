import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search, Plus, ArrowRight, FileText } from "lucide-react";
import { fetchContracts, ContractSummary } from "../api/client";
import { StatusBadge, RiskBadge } from "../components/Badges";
import { UploadModal } from "../components/UploadModal";

export function PortfolioView() {
  const [contracts, setContracts] = useState<ContractSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadContracts = async () => {
    try {
      const list = await fetchContracts();
      setContracts(list);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContracts();
  }, []);

  const filtered = contracts.filter((c) => {
    const matchesSearch =
      c.title.toLowerCase().includes(search.toLowerCase()) ||
      c.id.toLowerCase().includes(search.toLowerCase()) ||
      (c.counterparty && c.counterparty.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = statusFilter === "ALL" || c.status.toUpperCase() === statusFilter;

    let matchesRisk = true;
    if (riskFilter === "HIGH") {
      matchesRisk = (c.risk_score !== undefined && c.risk_score !== null && c.risk_score >= 0.6) || !!c.requires_escalation;
    } else if (riskFilter === "MEDIUM") {
      matchesRisk = c.risk_score !== undefined && c.risk_score !== null && c.risk_score >= 0.3 && c.risk_score < 0.6;
    } else if (riskFilter === "LOW") {
      matchesRisk = c.risk_score !== undefined && c.risk_score !== null && c.risk_score < 0.3;
    }

    return matchesSearch && matchesStatus && matchesRisk;
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-[#111827]">
            Contract Repository &amp; Portfolio
          </h2>
          <p className="text-xs text-[#6B7280]">
            Enterprise agreements managed across autonomous agent societies
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold shadow-xs transition-colors cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Upload Agreement</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by title, ID, or counterparty..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-white border border-[#E5E7EB] rounded-md text-xs text-[#111827] placeholder:text-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-[#E5E7EB] text-xs text-slate-700 rounded-md px-3 py-1.5 focus:outline-hidden focus:border-blue-500 cursor-pointer"
          >
            <option value="ALL">All Lifecycle Statuses</option>
            <option value="INTAKE">Intake</option>
            <option value="ANALYZED">Analyzed</option>
            <option value="APPROVED">Approved</option>
            <option value="SIGNED">Signed</option>
            <option value="RENEWAL_DUE">Renewal Due</option>
          </select>

          {/* Risk Filter */}
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="bg-white border border-[#E5E7EB] text-xs text-slate-700 rounded-md px-3 py-1.5 focus:outline-hidden focus:border-blue-500 cursor-pointer"
          >
            <option value="ALL">All Risk Levels</option>
            <option value="HIGH">High / Critical</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="LOW">Low Risk</option>
          </select>
        </div>
      </div>

      {/* Contracts Table */}
      <div className="bg-white border border-[#E5E7EB] rounded-lg overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-[#E5E7EB] text-slate-500 text-[11px] bg-slate-50 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Contract Title &amp; ID</th>
                <th className="py-3 px-4">Counterparty</th>
                <th className="py-3 px-4">Governing Law</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Adversarial Risk</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E7EB]">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    Loading contracts...
                  </td>
                </tr>
              ) : filtered.length > 0 ? (
                filtered.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <Link
                        to={`/contracts/${c.id}`}
                        className="font-semibold text-[#111827] hover:text-blue-600 transition-colors block"
                      >
                        {c.title}
                      </Link>
                      <span className="text-[10px] text-slate-400 font-mono">{c.id}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-700">{c.counterparty || "Vendor Corp"}</td>
                    <td className="py-3 px-4 text-slate-500">{c.governing_law || "Delaware"}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="py-3 px-4">
                      <RiskBadge score={c.risk_score} />
                      {c.requires_escalation && (
                        <span className="ml-1.5 text-[10px] text-rose-700 font-semibold bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                          Escalated
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/contracts/${c.id}`}
                        className="inline-flex items-center gap-1 px-3 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition-colors"
                      >
                        <span>Workspace</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    No matching contracts found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <UploadModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={(cid) => {
          loadContracts();
        }}
      />
    </div>
  );
}
