import React, { useEffect, useState } from "react";
import { Database, Search, Tag } from "lucide-react";
import { fetchMemories, CASMemoryItem } from "../api/client";

export function MemoryView() {
  const [memories, setMemories] = useState<CASMemoryItem[]>([]);
  const [tags, setTags] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const loadMemories = async () => {
    try {
      const data = await fetchMemories(tags, typeFilter || undefined);
      setMemories(data.memories || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
  }, [typeFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadMemories();
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-base font-bold text-[#111827]">
          Precedent &amp; Organizational Memory
        </h2>
        <p className="text-xs text-[#6B7280]">
          Institutional memory and learned patterns from past contract negotiations and dispute resolutions
        </p>
      </div>

      {/* Explanation Banner */}
      <div className="p-4 rounded-xl bg-white border border-[#E5E7EB] space-y-1 shadow-xs">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-purple-600" />
          <span className="text-xs font-bold text-slate-900 uppercase font-mono">
            Persistent Precedent Engine
          </span>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed">
          When General Counsel approves a compromise (e.g. 12-month mutual liability cap) or resolves
          a dispute ambiguity, CAS records the decision into persistent memory. Subsequent agent societies retrieve
          these precedents to suggest optimal redlines with higher confidence.
        </p>
      </div>

      {/* Search & Filter Bar */}
      <form
        onSubmit={handleSearch}
        className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs flex flex-col sm:flex-row gap-3 items-center justify-between"
      >
        <div className="relative w-full sm:w-96">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search tags (e.g. indemnity, liability, delaware)..."
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-white border border-[#E5E7EB] rounded-md text-xs text-[#111827] placeholder:text-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-white border border-[#E5E7EB] text-xs text-slate-700 rounded-md px-3 py-1.5 focus:outline-hidden focus:border-blue-500 cursor-pointer"
          >
            <option value="">All Memory Types</option>
            <option value="DECISION">Human Decisions</option>
            <option value="NEGOTIATION">Negotiation Outcomes</option>
            <option value="DISPUTE">Dispute Precedents</option>
            <option value="CONFLICT">Cross-Domain Arbitrations</option>
          </select>

          <button
            type="submit"
            className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer shadow-xs"
          >
            Search Precedents
          </button>
        </div>
      </form>

      {/* Suggested Tag Pills */}
      <div className="flex items-center gap-2 flex-wrap text-xs">
        <span className="text-slate-500 text-[11px] font-semibold">Quick Tags:</span>
        {["indemnity", "liability", "delaware", "termination", "sla", "gdpr"].map((tag) => (
          <button
            key={tag}
            type="button"
            onClick={() => {
              setTags(tag);
              fetchMemories(tag, typeFilter || undefined).then((d) => setMemories(d.memories || []));
            }}
            className="px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 hover:bg-slate-200 text-slate-700 text-[11px] font-mono transition-colors cursor-pointer"
          >
            #{tag}
          </button>
        ))}
      </div>

      {/* Precedent Cards List */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs">Loading precedent memories...</div>
        ) : memories.length > 0 ? (
          memories.map((m) => (
            <div
              key={m.id}
              className="p-5 rounded-lg bg-white border border-[#E5E7EB] space-y-3 shadow-xs"
            >
              <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-900">{m.title}</span>
                  <span className="px-2 py-0.5 rounded bg-purple-50 border border-purple-200 text-purple-700 text-[10px] font-mono font-semibold">
                    {m.memory_type}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">
                  Ref: {m.reference_id || "SYSTEM"}
                </span>
              </div>

              {/* Formatted Precedent Content */}
              {typeof m.content === "string" ? (
                <div className="text-xs text-slate-800 leading-relaxed bg-slate-50 p-3.5 rounded border border-slate-200">
                  {m.content}
                </div>
              ) : typeof m.content === "object" && m.content !== null ? (
                <div className="space-y-2 text-xs">
                  {m.content.resolution && (
                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 space-y-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block font-mono">
                        Precedent Ruling &amp; Standard
                      </span>
                      <p className="leading-relaxed">{m.content.resolution}</p>
                    </div>
                  )}

                  {m.content.reason && (
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 space-y-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 block font-mono">
                        Decision Rationale
                      </span>
                      <p className="leading-relaxed">{m.content.reason}</p>
                    </div>
                  )}

                  {/* Other fields */}
                  <div className="flex flex-wrap gap-2 pt-1">
                    {Object.entries(m.content)
                      .filter(([k]) => k !== "resolution" && k !== "reason")
                      .map(([k, v]) => (
                        <div
                          key={k}
                          className="px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-[11px] text-slate-700"
                        >
                          <span className="text-slate-500 mr-1 capitalize font-mono">{k.replace(/_/g, " ")}:</span>
                          <span className="font-semibold text-slate-900">
                            {typeof v === "object" ? JSON.stringify(v) : String(v)}
                          </span>
                        </div>
                      ))}
                  </div>

                  {/* Collapsible raw data */}
                  <details className="text-[11px] font-mono text-slate-500 pt-1 group">
                    <summary className="cursor-pointer hover:text-slate-800 select-none text-[10px] flex items-center gap-1">
                      <span>View Technical Payload</span>
                    </summary>
                    <pre className="p-2 mt-1 rounded bg-slate-50 border border-slate-200 text-[10px] text-slate-700 overflow-x-auto max-h-36">
                      {JSON.stringify(m.content, null, 2)}
                    </pre>
                  </details>
                </div>
              ) : (
                <div className="text-xs text-slate-700 font-mono bg-slate-50 p-3 rounded border border-slate-200">
                  {String(m.content)}
                </div>
              )}

              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                <div className="flex items-center gap-1.5">
                  <Tag className="w-3 h-3 text-slate-400" />
                  <span>Tags: {m.context_tags || "general"}</span>
                </div>
                <span className="font-mono">
                  Logged: {m.created_at ? new Date(m.created_at).toLocaleDateString() : "Historical"}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="p-12 text-center text-slate-500 text-xs bg-white rounded-lg border border-[#E5E7EB]">
            No precedents found matching your search.
          </div>
        )}
      </div>
    </div>
  );
}
