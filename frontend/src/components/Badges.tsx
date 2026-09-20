import React from "react";

export function StatusBadge({ status }: { status: string }) {
  const s = (status || "INTAKE").toUpperCase();

  let styles = "bg-slate-50 text-slate-700 border-slate-200";
  if (s === "SIGNED" || s === "ACTIVE" || s === "APPROVED" || s === "COMPLIANT") {
    styles = "bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold";
  } else if (s === "ANALYZED" || s === "ACCEPTED") {
    styles = "bg-blue-50 text-blue-800 border-blue-200 font-semibold";
  } else if (s === "PENDING" || s === "RENEWAL_DUE" || s === "IN_REVIEW") {
    styles = "bg-amber-50 text-amber-900 border-amber-300 font-semibold";
  } else if (s === "REJECTED" || s === "NON_COMPLIANT" || s === "BREACH" || s === "HIGH" || s === "CRITICAL") {
    styles = "bg-rose-50 text-rose-800 border-rose-200 font-semibold";
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono border tracking-wide uppercase ${styles}`}>
      {s}
    </span>
  );
}

export function RiskBadge({ score, level }: { score?: number | null; level?: string }) {
  let display = level || "UNKNOWN";
  let styles = "bg-slate-50 text-slate-600 border-slate-200";

  if (score !== undefined && score !== null) {
    if (score >= 0.75) {
      display = `CRITICAL (${(score * 100).toFixed(0)}%)`;
      styles = "bg-rose-50 text-rose-800 border-rose-200 font-semibold";
    } else if (score >= 0.5) {
      display = `HIGH (${(score * 100).toFixed(0)}%)`;
      styles = "bg-orange-50 text-orange-800 border-orange-200 font-semibold";
    } else if (score >= 0.3) {
      display = `MEDIUM (${(score * 100).toFixed(0)}%)`;
      styles = "bg-amber-50 text-amber-800 border-amber-200 font-semibold";
    } else {
      display = `LOW (${(score * 100).toFixed(0)}%)`;
      styles = "bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold";
    }
  } else if (level) {
    const l = level.toUpperCase();
    if (l === "CRITICAL" || l === "HIGH") {
      styles = "bg-rose-50 text-rose-800 border-rose-200 font-semibold";
    } else if (l === "MEDIUM") {
      styles = "bg-amber-50 text-amber-800 border-amber-200 font-semibold";
    } else {
      styles = "bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold";
    }
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono border ${styles}`}>
      {display}
    </span>
  );
}
