import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  XCircle,
  FileEdit,
  ExternalLink,
  Check,
} from "lucide-react";
import { fetchReviews, resolveReview, HumanReview } from "../api/client";
import { StatusBadge } from "../components/Badges";

export function ApprovalsView() {
  const [reviews, setReviews] = useState<HumanReview[]>([]);
  const [filter, setFilter] = useState<"PENDING" | "RESOLVED" | "ALL">("PENDING");
  const [loading, setLoading] = useState(true);
  const [actionNotes, setActionNotes] = useState<Record<string, string>>({});
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadReviews = async () => {
    try {
      const data = await fetchReviews(filter === "ALL" ? undefined : filter);
      setReviews(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReviews();
  }, [filter]);

  const handleResolve = async (reviewId: string, decision: "APPROVE" | "REJECT" | "REQUEST_REDLINE") => {
    setActionLoading(reviewId);
    const notes = actionNotes[reviewId] || `Decision ${decision} submitted via CAS Operations Approval Center.`;

    try {
      await resolveReview(reviewId, decision, "general_counsel@acme.com", notes);
      await loadReviews();
    } catch (err: any) {
      alert("Failed to submit decision: " + err.message);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-[#111827]">
            Pending Reviews &amp; Escalations
          </h2>
          <p className="text-xs text-[#6B7280]">
            Human-in-the-loop decisions requiring organizational authorization and counsel sign-off
          </p>
        </div>

        {/* Filter Toggle */}
        <div className="flex items-center gap-1 bg-white border border-[#E5E7EB] p-1 rounded-lg self-start sm:self-auto shadow-2xs">
          {(["PENDING", "RESOLVED", "ALL"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded text-xs font-semibold transition-colors cursor-pointer ${
                filter === f
                  ? "bg-blue-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {f === "ALL" ? "All Reviews" : f.charAt(0) + f.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Review Cards */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            Loading approval requests...
          </div>
        ) : reviews.length > 0 ? (
          reviews.map((r) => {
            const isPending = r.status === "PENDING";
            const reviewData = r.review_data || {};
            const conclusions = reviewData.agentConclusions || [];

            return (
              <div
                key={r.review_id}
                className="p-5 rounded-lg bg-white border border-[#E5E7EB] space-y-4 shadow-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E5E7EB] pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-xs font-bold text-blue-700">
                      {r.review_id}
                    </span>
                    <StatusBadge status={r.status} />
                    <Link
                      to={`/contracts/${r.contract_id}`}
                      className="text-xs text-slate-700 hover:text-blue-600 font-semibold flex items-center gap-1"
                    >
                      <span>Contract: {r.contract_id}</span>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </Link>
                  </div>

                  <div className="text-[11px] text-slate-400 font-mono">
                    Created: {r.created_at ? new Date(r.created_at).toLocaleString() : ""}
                  </div>
                </div>

                {/* Reason & Findings */}
                <div className="space-y-2">
                  <div className="text-xs">
                    <span className="text-slate-500 font-medium mr-2">Escalation Trigger:</span>
                    <span className="text-slate-900 font-semibold">{r.reason}</span>
                  </div>

                  {conclusions.length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {conclusions.map((c: string, idx: number) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-[11px] text-slate-700 font-mono"
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Resolution History or Action Controls */}
                {isPending ? (
                  <div className="pt-3 border-t border-[#E5E7EB] space-y-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                        General Counsel Decision Notes / Mandated Amendments:
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Mandate 12-month mutual liability cap and strike Section 7.2 indemnity..."
                        value={actionNotes[r.review_id] || ""}
                        onChange={(e) =>
                          setActionNotes((prev) => ({ ...prev, [r.review_id]: e.target.value }))
                        }
                        className="w-full bg-white border border-[#E5E7EB] rounded px-3 py-1.5 text-xs text-[#111827] placeholder:text-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                      />
                    </div>

                    <div className="flex items-center gap-2 justify-end">
                      <button
                        onClick={() => handleResolve(r.review_id, "REJECT")}
                        disabled={actionLoading === r.review_id}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-800 rounded text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Reject Contract</span>
                      </button>

                      <button
                        onClick={() => handleResolve(r.review_id, "REQUEST_REDLINE")}
                        disabled={actionLoading === r.review_id}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 hover:bg-amber-100 border border-amber-300 text-amber-900 rounded text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
                      >
                        <FileEdit className="w-3.5 h-3.5" />
                        <span>Request Redline Revision</span>
                      </button>

                      <button
                        onClick={() => handleResolve(r.review_id, "APPROVE")}
                        disabled={actionLoading === r.review_id}
                        className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold shadow-xs transition-colors cursor-pointer disabled:opacity-50"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Approve Redline Strategy</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="pt-2 border-t border-[#E5E7EB] flex items-center justify-between text-xs text-slate-500">
                    <div>
                      <span className="text-slate-500 mr-1">Resolved by:</span>
                      <span className="text-slate-800 font-mono font-semibold">{r.reviewer_id}</span>
                      {r.decision_notes && (
                        <p className="text-slate-700 text-[11px] mt-0.5 italic">
                          &ldquo;{r.decision_notes}&rdquo;
                        </p>
                      )}
                    </div>
                    <span className="font-mono text-[10px] text-slate-400">
                      {r.resolved_at ? new Date(r.resolved_at).toLocaleString() : ""}
                    </span>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="p-12 text-center text-slate-500 text-xs bg-white rounded-lg border border-[#E5E7EB]">
            No {filter.toLowerCase()} review requests found.
          </div>
        )}
      </div>
    </div>
  );
}
