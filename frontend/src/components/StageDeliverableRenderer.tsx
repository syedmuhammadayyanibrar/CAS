import React from "react";
import {
  Inbox,
  Layers,
  ShieldAlert,
  ShieldCheck,
  AlertCircle,
  AlertTriangle,
  Zap,
  MessageSquare,
  Scale,
  FileCheck,
  Gavel,
  UserCheck,
  Database,
  Calendar,
  Check,
  Terminal,
  CheckCircle2,
} from "lucide-react";

interface StageDeliverableRendererProps {
  step: number;
  title: string;
  society: string;
  summary: string;
  data: any;
}

export function StageDeliverableRenderer({
  step,
  title,
  society,
  summary,
  data,
}: StageDeliverableRendererProps) {
  if (!data) return null;

  const renderStageContent = () => {
    switch (step) {
      case 1:
        return renderStage1(data);
      case 2:
        return renderStage2(data);
      case 3:
        return renderStage3(data);
      case 4:
        return renderStage4(data);
      case 5:
        return renderStage5(data);
      case 6:
        return renderStage6(data);
      case 7:
        return renderStage7(data);
      case 8:
        return renderStage8(data);
      case 9:
        return renderStage9(data);
      case 10:
        return renderStage10(data);
      case 11:
        return renderStage11(data);
      case 12:
        return renderStage12(data);
      case 13:
        return renderStage13(data);
      case 14:
        return renderStage14(data);
      case 15:
        return renderStage15(data);
      default:
        return renderDefaultGeneric(data);
    }
  };

  return (
    <div className="space-y-4">
      {/* Deliverable Header */}
      <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-mono font-bold uppercase">
              Stage {step} Deliverable
            </span>
            <span className="text-xs text-slate-500 font-medium">{society}</span>
          </div>
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Execution Completed
          </span>
        </div>
        <p className="text-xs text-slate-800 font-medium leading-relaxed">{summary}</p>
      </div>

      {/* Tailored Visual Content */}
      <div className="p-5 rounded-lg bg-white border border-[#E5E7EB] shadow-xs space-y-4">
        {renderStageContent()}
      </div>

      {/* Collapsible Technical Details (Raw JSON) */}
      <details className="border border-[#E5E7EB] rounded-lg bg-slate-50 overflow-hidden group">
        <summary className="px-4 py-2.5 text-[11px] font-mono text-slate-600 hover:text-slate-900 cursor-pointer flex items-center justify-between transition-colors select-none">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-blue-600" />
            <span>Technical Metadata (Raw JSON Payload)</span>
          </div>
          <span className="text-[10px] text-slate-400 group-open:rotate-180 transition-transform">
            ▼
          </span>
        </summary>
        <div className="p-3 border-t border-[#E5E7EB] bg-white">
          <pre className="font-mono text-[11px] text-slate-700 overflow-x-auto max-h-[280px] leading-relaxed">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      </details>
    </div>
  );
}

// Stage 1: Contract Intake
function renderStage1(data: any) {
  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center gap-2 pb-3 border-b border-[#E5E7EB]">
        <Inbox className="w-4 h-4 text-blue-600" />
        <h3 className="font-bold text-slate-900">Inbound Webhook Intake Manifest</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">Contract ID</div>
          <div className="font-mono font-bold text-blue-700">{data.contract_id || "CTR-DEMO-2026-SAAS"}</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">Source Repository</div>
          <div className="font-medium text-slate-800">Enterprise Cloud Drive</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">Connector Gateway</div>
          <div className="font-semibold text-emerald-700">Fastn Inbound Webhook</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">Intake Status</div>
          <div className="font-semibold text-emerald-700">Verified &amp; Queued</div>
        </div>
      </div>

      <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
        <div className="text-[11px] font-semibold text-slate-700">Document Payload Preview</div>
        <p className="text-[11px] text-slate-600 font-mono italic leading-relaxed">
          &ldquo;ENTERPRISE CLOUD SERVICES AGREEMENT — This Agreement is entered into between Acme Global Enterprises (&lsquo;Customer&rsquo;) and NovaCloud Inc. (&lsquo;Vendor&rsquo;) for the provision of Mission-Critical Cloud Infrastructure...&rdquo;
        </p>
      </div>
    </div>
  );
}

// Stage 2: Contract Intelligence (Knowledge Graph)
function renderStage2(data: any) {
  const clauses = data.clauses || [];
  const parties = data.parties || [];

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-600" />
          <h3 className="font-bold text-slate-900">Extracted Contract Knowledge Graph</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] font-mono font-medium">
            {clauses.length} Clauses
          </span>
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] font-mono font-medium">
            {parties.length} Parties
          </span>
        </div>
      </div>

      {parties.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {parties.map((p: any, idx: number) => (
            <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-semibold text-slate-500">{p.role || "Party"}</span>
                <div className="font-bold text-slate-900">{p.name}</div>
              </div>
              <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-mono font-semibold">
                {p.party_id || `P-${idx + 1}`}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-2">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider font-mono">
          Extracted Semantic Clauses
        </div>
        <div className="divide-y divide-[#E5E7EB] border border-[#E5E7EB] rounded-lg overflow-hidden max-h-[260px] overflow-y-auto">
          {clauses.slice(0, 6).map((c: any, idx: number) => (
            <div key={idx} className="p-3 bg-white hover:bg-slate-50 transition-colors space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-900 font-mono text-[11px]">
                  {c.clause_id}: {c.title}
                </span>
                <span className="px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 text-[10px] uppercase font-mono">
                  {c.category || "General"}
                </span>
              </div>
              <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">
                {c.text || c.text_snippet || "Operative contractual terms and obligations."}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Stage 3: Risk Intelligence (Adversarial Debate)
function renderStage3(data: any) {
  const findings = data.findings || [];
  const score = typeof data.overall_risk_score === "number" ? data.overall_risk_score : 0.85;

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-600" />
          <h3 className="font-bold text-slate-900">Adversarial Dialectic Findings</h3>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] uppercase text-slate-500 font-semibold block">Overall Risk</span>
            <span className="text-base font-bold text-rose-600 font-mono">{(score * 100).toFixed(0)}%</span>
          </div>
          {data.requires_human_escalation && (
            <span className="px-2 py-1 rounded bg-rose-50 border border-rose-200 text-rose-800 text-[10px] font-bold uppercase animate-pulse">
              Escalation Required
            </span>
          )}
        </div>
      </div>

      {findings.map((f: any, idx: number) => (
        <div key={idx} className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-900 font-mono text-xs">
              {f.clause_id ? `${f.clause_id} — ` : ""}{f.category || "Liability Risk"}
            </span>
            <span className="px-2 py-0.5 rounded bg-rose-50 border border-rose-200 text-rose-800 text-[10px] font-bold uppercase">
              {f.severity || "CRITICAL"}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-200 space-y-1">
              <div className="text-[10px] uppercase font-bold text-rose-700 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Risk Hunter (Downside Exposure)
              </div>
              <p className="text-[11px] text-slate-800 leading-relaxed">
                {f.hunter_argument || "Customer exposed to uncapped liability while vendor caps damages at nominal fees."}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-blue-50/60 border border-blue-200 space-y-1">
              <div className="text-[10px] uppercase font-bold text-blue-700 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" />
                Counterargument Defense (Market Standard)
              </div>
              <p className="text-[11px] text-slate-800 leading-relaxed">
                {f.counterargument || "Uncapped indemnities are standard in multi-tenant SaaS to cover gross negligence."}
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-amber-50/60 border border-amber-200 space-y-1">
            <div className="text-[10px] uppercase font-bold text-amber-800">
              Synthesis Assessor (Calibrated Exposure)
            </div>
            <p className="text-[11px] text-slate-900 leading-relaxed">
              {f.synthesis || "Asymmetric cap violates corporate risk envelope. Must demand bilateral 12-month trailing fee ceiling."}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

// Stage 4: Fastn Risk Escalation (Slack Outbound)
function renderStage4(data: any) {
  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-600" />
          <h3 className="font-bold text-slate-900">Fastn Outbound Enterprise Dispatch</h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 font-mono text-[10px] font-semibold">
          Delivered
        </span>
      </div>

      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-blue-600" />
            <span className="font-bold text-slate-900">Slack Legal Escalation Channel</span>
          </div>
          <span className="font-mono text-slate-500 text-[11px]">{data.channel || "#legal-contract-risks"}</span>
        </div>

        <div className="p-3 rounded-lg bg-white border border-slate-200 space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-rose-50 border border-rose-200 text-rose-800 text-[10px] font-bold">
              CRITICAL ALERT
            </span>
            <span className="text-slate-800 font-semibold text-xs">Uncapped Liability &amp; Indemnity Asymmetry</span>
          </div>
          <p className="text-[11px] text-slate-600 leading-relaxed">
            &ldquo;CAS Risk Intelligence has identified an unmitigated liability vector in Section 8.2 of agreement CTR-DEMO-2026-SAAS. Automated escalation dispatched via Fastn connector for General Counsel review.&rdquo;
          </p>
        </div>
      </div>
    </div>
  );
}

// Stage 5: Negotiation Strategy & Redlines
function renderStage5(data: any) {
  const positions = data.positions || [];

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4 text-blue-600" />
          <h3 className="font-bold text-slate-900">Negotiation Strategy &amp; Redline Proposals</h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-mono font-semibold">
          {positions.length} Positions Generated
        </span>
      </div>

      <div className="space-y-3">
        {positions.map((pos: any, idx: number) => (
          <div key={idx} className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-900 font-mono text-xs">
                {pos.clause_id ? `${pos.clause_id} — ` : `Position ${idx + 1}: `}
                {pos.concession_strategy || pos.priority || "Liability Term"}
              </span>
              <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-mono font-semibold">
                Priority: {pos.priority || "HIGH"}
              </span>
            </div>

            <div className="space-y-2">
              <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-200 text-rose-900 font-mono text-[11px] leading-relaxed">
                <span className="text-[10px] uppercase font-bold text-rose-700 block mb-1">
                  Current Language (Strike)
                </span>
                <del>{pos.current_language || pos.original_text || "Customer total aggregate liability under this agreement shall be uncapped."}</del>
              </div>

              <div className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200 text-emerald-900 font-mono text-[11px] leading-relaxed font-semibold">
                <span className="text-[10px] uppercase font-bold text-emerald-700 block mb-1">
                  Proposed Redline (Insert)
                </span>
                <ins className="no-underline">{pos.proposed_redline || "Each party's total aggregate liability under this agreement shall be strictly capped at the total fees paid or payable in the preceding 12 months."}</ins>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Stage 6: Compliance Intelligence Audit
function renderStage6(data: any) {
  const findings = data.findings || [];
  const status = data.overall_status || "NON_COMPLIANT";

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-blue-600" />
          <h3 className="font-bold text-slate-900">Corporate Compliance Policy Audit</h3>
        </div>
        <span className={`px-2.5 py-1 rounded text-xs font-bold font-mono ${
          status === "COMPLIANT" ? "bg-emerald-50 border border-emerald-200 text-emerald-800" : "bg-rose-50 border border-rose-200 text-rose-800"
        }`}>
          {status}
        </span>
      </div>

      <div className="space-y-2.5">
        {findings.map((f: any, idx: number) => (
          <div key={idx} className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-900 font-mono">
                {f.rule_name || f.rule_id || `Compliance Rule ${idx + 1}`}
              </span>
              <span className="px-2 py-0.5 rounded bg-rose-50 border border-rose-200 text-rose-800 text-[10px] font-bold uppercase">
                {f.severity || "HIGH"}
              </span>
            </div>
            <p className="text-slate-700 text-xs leading-relaxed">{f.reasoning}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// Stage 7: Fastn Compliance Escalation
function renderStage7(data: any) {
  const violations = data.violations || [];

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-600" />
          <h3 className="font-bold text-slate-900">Fastn Compliance Alert Dispatch</h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[10px] font-mono font-semibold">
          Delivered
        </span>
      </div>

      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-500">Policy Framework:</span>
          <span className="font-bold text-slate-900 font-mono">{data.policy_name || "Corporate Standard Vendor Policy v2.4"}</span>
        </div>

        <div className="space-y-2 pt-1">
          {violations.map((v: any, idx: number) => (
            <div key={idx} className="p-2.5 rounded-lg bg-white border border-slate-200 text-[11px] space-y-1">
              <div className="flex items-center justify-between font-semibold text-slate-800">
                <span>{v.policy}</span>
                <span className="text-rose-700 font-mono text-[10px]">{v.severity}</span>
              </div>
              <p className="text-slate-600 leading-relaxed">{v.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Stage 8: CAS Director Dynamic Mesh & Conflict Arbitration
function renderStage8(data: any) {
  const conflicts = data.detected_conflicts || [];

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <Gavel className="w-4 h-4 text-blue-600" />
          <h3 className="font-bold text-slate-900">Director Cross-Society Arbitration</h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-mono font-semibold">
          {conflicts.length} Conflicts Resolved
        </span>
      </div>

      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
        <div className="text-[10px] uppercase font-bold text-blue-700 tracking-wider font-mono">
          Arbitration Ruling
        </div>
        <p className="text-xs text-slate-900 leading-relaxed font-semibold">
          {data.director_decision || "Balanced Risk and Negotiation postures: prioritize 12-month mutual fee cap, waive audit notice penalties, and mandate Delaware governing venue."}
        </p>
      </div>
    </div>
  );
}

// Stage 9: Fastn HITL Approval Dispatch
function renderStage9(data: any) {
  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <UserCheck className="w-4 h-4 text-amber-600" />
          <h3 className="font-bold text-slate-900">Human-In-The-Loop Review Gate</h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-amber-50 border border-amber-300 text-amber-800 text-[10px] font-mono font-bold">
          Awaiting Review
        </span>
      </div>

      <div className="p-4 rounded-lg bg-amber-50/50 border border-amber-200 space-y-3">
        <div>
          <span className="text-[10px] uppercase text-amber-800 font-bold block mb-1">
            Escalation Reason
          </span>
          <p className="text-slate-900 text-xs font-semibold leading-relaxed">
            {data.reason || "Uncapped customer liability and non-compliant audit terms require executive review."}
          </p>
        </div>
        <div>
          <span className="text-[10px] uppercase text-slate-500 font-bold block mb-1">
            Designated Reviewer
          </span>
          <span className="text-slate-900 font-mono font-medium">{data.reviewer_email || "general_counsel@acme.com"}</span>
        </div>
      </div>
    </div>
  );
}

// Stage 10: Fastn Decision Archival
function renderStage10(data: any) {
  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-600" />
          <h3 className="font-bold text-slate-900">Executive Decision Archival &amp; Precedent Storage</h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[10px] font-mono font-semibold">
          Archived
        </span>
      </div>

      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg bg-white border border-slate-200">
            <span className="text-[10px] uppercase text-slate-500 font-semibold block mb-1">Formal Decision</span>
            <span className="text-xs font-bold text-emerald-700 font-mono">{data.decision || "APPROVED_WITH_CONDITIONS"}</span>
          </div>
          <div className="p-3 rounded-lg bg-white border border-slate-200">
            <span className="text-[10px] uppercase text-slate-500 font-semibold block mb-1">Authorized By</span>
            <span className="text-xs font-semibold text-slate-900">{data.decision_maker || "General Counsel / VP Legal"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Stage 11: Obligation Scheduling & Fastn Calendar Sync
function renderStage11(data: any) {
  const schedule = data.schedule || {};
  const items = schedule.items || [];

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-indigo-600" />
          <h3 className="font-bold text-slate-900">Post-Signature Obligation Schedule</h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[10px] font-mono font-semibold">
          Signed &amp; Synced
        </span>
      </div>

      <div className="divide-y divide-[#E5E7EB] border border-[#E5E7EB] rounded-lg overflow-hidden bg-white">
        {items.map((item: any, idx: number) => (
          <div key={idx} className="p-3.5 hover:bg-slate-50 transition-colors flex items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="font-semibold text-slate-900 flex items-center gap-2">
                <span>{item.title}</span>
                <span className="px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 text-[10px] font-mono">
                  {item.party}
                </span>
              </div>
              <div className="text-[11px] text-slate-500 flex items-center gap-3">
                <span>Due Date: <strong className="text-amber-800 font-mono">{item.due_date || "2026-11-01"}</strong></span>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[10px] font-semibold shrink-0 flex items-center gap-1">
              <Check className="w-3 h-3" />
              Calendar Synced
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Stage 12: Fastn Inbound Event
function renderStage12(data: any) {
  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-blue-600" />
          <h3 className="font-bold text-slate-900">External Counterparty Redline Ingested</h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-mono font-semibold">
          Inbound Webhook
        </span>
      </div>

      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
        <div className="p-3 rounded-lg bg-white border border-slate-200 space-y-1">
          <span className="text-[10px] uppercase font-bold text-blue-700 block">
            Counterparty Proposed Language
          </span>
          <p className="text-xs text-slate-800 leading-relaxed font-mono">
            &ldquo;{data.counterparty_proposal || "NovaCloud agrees to mutual aggregate liability capped at 12 months fees ($240,000) conditioned on exclusion of lost profits."}&rdquo;
          </p>
        </div>
      </div>
    </div>
  );
}

// Stage 13: Director Re-Routing & Adaptation
function renderStage13(data: any) {
  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4 text-blue-600" />
          <h3 className="font-bold text-slate-900">Dynamic Strategy Adaptation</h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[10px] font-mono font-semibold">
          Re-Routed
        </span>
      </div>

      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
        <p className="text-slate-800 leading-relaxed font-semibold">
          {data.action || "CAS Director dynamically reactivated Negotiation Intelligence Society to calibrate leverage posture following vendor concession."}
        </p>
      </div>
    </div>
  );
}

// Stage 14: Fastn Dispute Escalation
function renderStage14(data: any) {
  const ambiguities = data.ambiguities || [];

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600" />
          <h3 className="font-bold text-slate-900">Pre-Litigation Dispute Risk Alert</h3>
        </div>
        <span className="px-2 py-0.5 rounded bg-amber-50 border border-amber-300 text-amber-800 text-[10px] font-mono font-bold">
          Risk: HIGH
        </span>
      </div>

      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
        <div className="space-y-1.5">
          <span className="text-[10px] uppercase text-slate-500 font-bold block font-mono">
            Identified Ambiguity Vectors
          </span>
          <div className="space-y-1.5">
            {ambiguities.map((a: string, idx: number) => (
              <div key={idx} className="p-2.5 rounded-lg bg-white border border-slate-200 text-slate-700 text-[11px]">
                {a}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Stage 15: Dispute Simulation & CAS Memory
function renderStage15(data: any) {
  const assessment = data.dispute_assessment || {};
  const scenarios = assessment.scenarios || [];

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-2">
          <Gavel className="w-4 h-4 text-blue-600" />
          <h3 className="font-bold text-slate-900">Trial Simulation &amp; Institutional Memory</h3>
        </div>
        <span className="px-2.5 py-1 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono font-bold">
          All 15 Stages Complete
        </span>
      </div>

      <div className="space-y-3">
        {scenarios.map((sc: any, idx: number) => (
          <div key={idx} className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-900 font-mono text-xs">
                {sc.clause_id ? `${sc.clause_id} — ` : ""}{sc.ambiguity_type || "Contract Ambiguity"}
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-mono">
                Scenario {idx + 1}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3 rounded-lg bg-blue-50/60 border border-blue-200 space-y-1">
                <span className="text-[10px] uppercase font-bold text-blue-700 block">
                  Customer Litigation Interpretation
                </span>
                <p className="text-[11px] text-slate-800 leading-relaxed">
                  {sc.party_a_interpretation || "Customer claims credits for any degradation in availability exceeding 10 minutes."}
                </p>
              </div>

              <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-200 space-y-1">
                <span className="text-[10px] uppercase font-bold text-rose-700 block">
                  Vendor Litigation Interpretation
                </span>
                <p className="text-[11px] text-slate-800 leading-relaxed">
                  {sc.party_b_interpretation || "Vendor asserts upstream ISP issues are force majeure."}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function renderDefaultGeneric(data: any) {
  return (
    <div className="space-y-3 text-xs">
      <div className="text-slate-800 font-semibold">Deliverable Summary:</div>
      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-800">
        {typeof data === "object" ? (
          <div className="space-y-1">
            {Object.entries(data).slice(0, 8).map(([k, v]) => (
              <div key={k} className="flex items-start justify-between py-1 border-b border-slate-200">
                <span className="text-slate-500 font-mono text-[11px]">{k}:</span>
                <span className="text-slate-900 font-medium text-right max-w-md truncate">
                  {typeof v === "object" ? JSON.stringify(v) : String(v)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          String(data)
        )}
      </div>
    </div>
  );
}
