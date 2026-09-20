import React, { useEffect, useState } from "react";
import {
  Zap,
  Play,
  Copy,
  Check,
  CheckCircle2,
  ArrowDownLeft,
  ArrowUpRight,
  Radio,
  Terminal,
  Activity,
  Filter,
  RefreshCw,
  Sliders,
  Code2,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import {
  fetchAutomations,
  executeAutomation,
  fetchFastnExecutions,
  FastnWorkflow,
  FastnExecution,
} from "../api/client";

export function AutomationsView() {
  const [workflows, setWorkflows] = useState<FastnWorkflow[]>([]);
  const [executions, setExecutions] = useState<FastnExecution[]>([]);
  const [orgId, setOrgId] = useState<string>("personal_867cccac2ec39658a401");
  const [loading, setLoading] = useState(true);
  const [loadingExecutions, setLoadingExecutions] = useState(false);
  const [executingSlug, setExecutingSlug] = useState<string | null>(null);
  const [executionResults, setExecutionResults] = useState<Record<string, any>>({});
  const [copiedWebhook, setCopiedWebhook] = useState<string | null>(null);
  const [directionFilter, setDirectionFilter] = useState<"ALL" | "INBOUND" | "OUTBOUND">("ALL");
  const [activeTab, setActiveTab] = useState<"catalog" | "trace">("catalog");

  // Custom Payload Editor State
  const [openPayloadSlug, setOpenPayloadSlug] = useState<string | null>(null);
  const [customPayloads, setCustomPayloads] = useState<Record<string, string>>({});
  const [jsonErrors, setJsonErrors] = useState<Record<string, string | null>>({});

  const loadData = async () => {
    try {
      const data = await fetchAutomations();
      setWorkflows(data.workflows);
      setOrgId(data.org_id);

      // Initialize default payloads in custom payload state
      const initialPayloads: Record<string, string> = {};
      data.workflows.forEach((wf) => {
        initialPayloads[wf.slug] = JSON.stringify(wf.default_payload || {}, null, 2);
      });
      setCustomPayloads((prev) => ({ ...initialPayloads, ...prev }));
    } catch (err) {
      console.error("Failed to load Fastn catalog:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadExecutions = async () => {
    setLoadingExecutions(true);
    try {
      const data = await fetchFastnExecutions({ limit: 40 });
      setExecutions(data.executions);
    } catch (err) {
      console.error("Failed to load Fastn execution traces:", err);
    } finally {
      setLoadingExecutions(false);
    }
  };

  useEffect(() => {
    loadData();
    loadExecutions();
  }, []);

  const handleExecute = async (wf: FastnWorkflow) => {
    setExecutingSlug(wf.slug);
    try {
      const res = await executeAutomation(wf.slug, wf.default_payload);
      setExecutionResults((prev) => ({ ...prev, [wf.slug]: res }));
      loadExecutions();
    } catch (err: any) {
      setExecutionResults((prev) => ({
        ...prev,
        [wf.slug]: { error: err.message || "Failed to execute" },
      }));
    } finally {
      setExecutingSlug(null);
    }
  };

  const handleExecuteCustom = async (wf: FastnWorkflow) => {
    const rawPayload = customPayloads[wf.slug] || "{}";
    let parsed: any;
    try {
      parsed = JSON.parse(rawPayload);
    } catch (err: any) {
      setJsonErrors((prev) => ({ ...prev, [wf.slug]: err.message }));
      return;
    }

    setExecutingSlug(wf.slug);
    try {
      const res = await executeAutomation(wf.slug, parsed);
      setExecutionResults((prev) => ({ ...prev, [wf.slug]: res }));
      loadExecutions();
    } catch (err: any) {
      setExecutionResults((prev) => ({
        ...prev,
        [wf.slug]: { error: err.message || "Failed to execute" },
      }));
    } finally {
      setExecutingSlug(null);
    }
  };

  const togglePayloadEditor = (wf: FastnWorkflow) => {
    if (openPayloadSlug === wf.slug) {
      setOpenPayloadSlug(null);
    } else {
      setOpenPayloadSlug(wf.slug);
      if (!customPayloads[wf.slug]) {
        setCustomPayloads((prev) => ({
          ...prev,
          [wf.slug]: JSON.stringify(wf.default_payload || {}, null, 2),
        }));
      }
    }
  };

  const handlePayloadChange = (slug: string, value: string) => {
    setCustomPayloads((prev) => ({ ...prev, [slug]: value }));
    try {
      JSON.parse(value);
      setJsonErrors((prev) => ({ ...prev, [slug]: null }));
    } catch (err: any) {
      setJsonErrors((prev) => ({ ...prev, [slug]: err.message }));
    }
  };

  const handleResetPayload = (wf: FastnWorkflow) => {
    const defaultStr = JSON.stringify(wf.default_payload || {}, null, 2);
    setCustomPayloads((prev) => ({ ...prev, [wf.slug]: defaultStr }));
    setJsonErrors((prev) => ({ ...prev, [wf.slug]: null }));
  };

  const handleFormatPayload = (slug: string) => {
    try {
      const current = customPayloads[slug] || "{}";
      const parsed = JSON.parse(current);
      setCustomPayloads((prev) => ({ ...prev, [slug]: JSON.stringify(parsed, null, 2) }));
      setJsonErrors((prev) => ({ ...prev, [slug]: null }));
    } catch {
      // ignore
    }
  };

  const handleCopyWebhook = (url: string, id: string) => {
    navigator.clipboard.writeText(url);
    setCopiedWebhook(id);
    setTimeout(() => setCopiedWebhook(null), 2000);
  };

  const filteredWorkflows = workflows.filter((wf) => {
    if (directionFilter === "ALL") return true;
    return (wf.direction || "OUTBOUND").toUpperCase() === directionFilter;
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-[#111827] flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-600" />
            <span>Fastn Automation Center</span>
          </h2>
          <p className="text-xs text-[#6B7280]">
            External automations connecting CAS with enterprise integrations, webhooks, and notifications
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1 p-1 bg-white border border-[#E5E7EB] rounded-lg shadow-2xs">
          <button
            onClick={() => setActiveTab("catalog")}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-colors cursor-pointer ${
              activeTab === "catalog"
                ? "bg-blue-600 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Workflow Catalog ({workflows.length})
          </button>
          <button
            onClick={() => {
              setActiveTab("trace");
              loadExecutions();
            }}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer ${
              activeTab === "trace"
                ? "bg-blue-600 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Live Execution Traces ({executions.length})
          </button>
        </div>
      </div>

      {/* Fastn Organization Banner */}
      <div className="p-5 rounded-xl bg-white border border-[#E5E7EB] shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-amber-600 animate-pulse" />
            <span className="text-xs font-bold text-slate-900 uppercase font-mono">
              Fastn Connected Gateway
            </span>
          </div>
          <div className="text-xs text-slate-700">
            Organization Domain: <span className="font-mono font-semibold text-blue-700">{orgId}</span> • Workflows:{" "}
            <span className="text-emerald-700 font-bold font-mono">Active</span>
          </div>
          <p className="text-[11px] text-[#6B7280]">
            Automated workflows for contract events, Slack notifications, calendar sync, and interactive testing with custom data
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="px-2.5 py-1 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            {workflows.length || 10} Workflows Configured
          </span>
        </div>
      </div>

      {activeTab === "catalog" ? (
        <>
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-[#E5E7EB] pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-slate-400" /> Direction:
              </span>
              <div className="flex items-center gap-1 bg-white p-0.5 rounded border border-[#E5E7EB] text-xs">
                <button
                  onClick={() => setDirectionFilter("ALL")}
                  className={`px-2.5 py-1 rounded transition-colors cursor-pointer ${
                    directionFilter === "ALL"
                      ? "bg-slate-100 text-slate-900 font-bold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  All ({workflows.length})
                </button>
                <button
                  onClick={() => setDirectionFilter("OUTBOUND")}
                  className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1 cursor-pointer ${
                    directionFilter === "OUTBOUND"
                      ? "bg-blue-50 text-blue-700 font-bold border border-blue-200"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <ArrowUpRight className="w-3 h-3 text-blue-600" />
                  Outbound
                </button>
                <button
                  onClick={() => setDirectionFilter("INBOUND")}
                  className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1 cursor-pointer ${
                    directionFilter === "INBOUND"
                      ? "bg-emerald-50 text-emerald-800 font-bold border border-emerald-200"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <ArrowDownLeft className="w-3 h-3 text-emerald-600" />
                  Inbound
                </button>
              </div>
            </div>

            <button
              onClick={loadData}
              className="px-3 py-1 rounded-md bg-white border border-[#E5E7EB] hover:bg-slate-50 text-slate-700 text-xs flex items-center gap-1.5 transition-colors cursor-pointer font-medium"
            >
              <RefreshCw className="w-3 h-3" />
              Refresh Catalog
            </button>
          </div>

          {/* Workflows List */}
          <div className="space-y-4">
            {loading ? (
              <div className="p-12 text-center text-slate-500 text-xs">
                Loading Fastn workflow catalog...
              </div>
            ) : filteredWorkflows.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs border border-dashed border-slate-300 rounded-lg">
                No workflows match filter &ldquo;{directionFilter}&rdquo;.
              </div>
            ) : (
              filteredWorkflows.map((wf) => {
                const hasResult = !!executionResults[wf.slug];
                const isExecuting = executingSlug === wf.slug;
                const isInbound = (wf.direction || "OUTBOUND").toUpperCase() === "INBOUND";
                const targetUrl = wf.webhook_url || wf.trigger_url;
                const isEditorOpen = openPayloadSlug === wf.slug;

                return (
                  <div
                    key={wf.id || wf.slug}
                    className="p-5 rounded-lg bg-white border border-[#E5E7EB] space-y-4 shadow-xs hover:border-slate-300 transition-all"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E5E7EB] pb-3">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2.5">
                          <span className="text-sm font-bold text-[#111827]">{wf.name}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold flex items-center gap-1 ${
                              isInbound
                                ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
                                : "bg-blue-50 border border-blue-200 text-blue-700"
                            }`}
                          >
                            {isInbound ? (
                              <ArrowDownLeft className="w-3 h-3 text-emerald-600" />
                            ) : (
                              <ArrowUpRight className="w-3 h-3 text-blue-600" />
                            )}
                            {wf.direction || "OUTBOUND"}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 text-[10px] font-mono">
                            {wf.trigger_type || wf.trigger || "DIRECT"}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-800 text-[10px] font-mono">
                            {wf.connector || "custom"}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          Workflow ID: <span className="text-slate-800 font-semibold">{wf.id}</span>
                          {wf.target_system && (
                            <>
                              {" "}• Target: <span className="text-slate-800 font-semibold">{wf.target_system}</span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Action Buttons: Test Quick vs Customize & Run */}
                      <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
                        <button
                          onClick={() => togglePayloadEditor(wf)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors cursor-pointer border shadow-2xs ${
                            isEditorOpen
                              ? "bg-slate-200 border-slate-400 text-slate-900"
                              : "bg-slate-50 border-slate-300 hover:bg-slate-100 text-slate-700"
                          }`}
                        >
                          <Sliders className="w-3.5 h-3.5 text-slate-600" />
                          <span>{isEditorOpen ? "Hide Custom Data" : "Custom Data"}</span>
                        </button>

                        <button
                          onClick={() => handleExecute(wf)}
                          disabled={isExecuting}
                          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
                        >
                          <Play className="w-3.5 h-3.5" />
                          <span>{isExecuting ? "Executing Fastn..." : "Quick Test"}</span>
                        </button>
                      </div>
                    </div>

                    <p className="text-xs text-slate-700 leading-relaxed">{wf.description}</p>

                    {/* Expandable Custom Payload Drawer */}
                    {isEditorOpen && (
                      <div className="p-4 rounded-lg bg-slate-50 border border-blue-200 space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-2.5">
                          <div className="space-y-0.5">
                            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                              <Code2 className="w-3.5 h-3.5 text-blue-600" />
                              Custom Data Editor for {wf.name}
                            </span>
                            <p className="text-[11px] text-slate-500">
                              Edit JSON payload parameters below to trigger this Fastn automation with your own contract data.
                            </p>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => handleResetPayload(wf)}
                              className="px-2 py-1 text-[11px] rounded bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-mono flex items-center gap-1 transition-colors cursor-pointer"
                              title="Reset payload to default"
                            >
                              <RotateCcw className="w-3 h-3 text-slate-500" />
                              Reset
                            </button>
                            <button
                              onClick={() => handleFormatPayload(wf.slug)}
                              className="px-2 py-1 text-[11px] rounded bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-mono transition-colors cursor-pointer"
                              title="Format and validate JSON"
                            >
                              Format JSON
                            </button>
                          </div>
                        </div>

                        {/* JSON Input Area */}
                        <div className="space-y-1">
                          <textarea
                            rows={7}
                            value={customPayloads[wf.slug] || ""}
                            onChange={(e) => handlePayloadChange(wf.slug, e.target.value)}
                            placeholder="Enter valid JSON payload..."
                            className={`w-full p-3 font-mono text-xs bg-white border rounded-md text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 leading-relaxed ${
                              jsonErrors[wf.slug] ? "border-rose-300 focus:ring-rose-500" : "border-slate-300"
                            }`}
                          />
                          {jsonErrors[wf.slug] && (
                            <div className="text-[11px] text-rose-600 font-medium flex items-center gap-1">
                              <AlertTriangle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                              <span>JSON Syntax Error: {jsonErrors[wf.slug]}</span>
                            </div>
                          )}
                        </div>

                        {/* Custom Run Action */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1">
                          <span className="text-[11px] text-slate-500 font-mono">
                            Connector target: <strong className="text-blue-700">{wf.connector || "custom"}</strong>
                          </span>
                          <button
                            onClick={() => handleExecuteCustom(wf)}
                            disabled={isExecuting || !!jsonErrors[wf.slug]}
                            className="flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 shadow-xs self-end"
                          >
                            <Play className="w-3.5 h-3.5" />
                            <span>{isExecuting ? "Executing Fastn..." : "Run with Custom Data"}</span>
                          </button>
                        </div>
                      </div>
                    )}

                    {targetUrl && (
                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between gap-2 text-xs">
                        <div className="flex items-center gap-2 overflow-hidden">
                          <span className="text-[10px] uppercase font-bold text-amber-800 shrink-0 flex items-center gap-1 font-mono">
                            <Radio className="w-3 h-3 text-amber-600" />
                            Public Fastn Webhook URL:
                          </span>
                          <span className="font-mono text-slate-700 text-[11px] truncate">
                            {targetUrl}
                          </span>
                        </div>
                        <button
                          onClick={() => handleCopyWebhook(targetUrl, wf.slug)}
                          className="p-1.5 rounded bg-white border border-slate-300 hover:bg-slate-100 text-slate-600 transition-colors shrink-0 cursor-pointer"
                          title="Copy Webhook URL"
                        >
                          {copiedWebhook === wf.slug ? (
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    )}

                    {hasResult && (
                      <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span className="font-bold text-emerald-800">
                              Workflow Execution Succeeded
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-slate-500 font-mono">
                              Status: {executionResults[wf.slug]?.status || "SUCCESS"}
                            </span>
                            <button
                              onClick={() => {
                                setActiveTab("trace");
                                loadExecutions();
                              }}
                              className="text-[10px] text-blue-600 hover:text-blue-800 font-semibold underline cursor-pointer"
                            >
                              View in Traces &rarr;
                            </button>
                          </div>
                        </div>

                        <div className="p-2.5 rounded bg-white border border-slate-200 space-y-1">
                          {executionResults[wf.slug]?.execution_id && (
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-500 font-mono">Execution ID:</span>
                              <span className="font-mono text-slate-800 font-semibold">{executionResults[wf.slug].execution_id}</span>
                            </div>
                          )}
                          {executionResults[wf.slug]?.message && (
                            <div className="text-[11px] text-slate-700 pt-0.5 font-medium">
                              {executionResults[wf.slug].message}
                            </div>
                          )}
                        </div>

                        <details className="text-[11px] font-mono text-slate-500 pt-1 group">
                          <summary className="cursor-pointer hover:text-slate-800 select-none flex items-center gap-1 text-[10px]">
                            <Terminal className="w-3 h-3 text-slate-400" />
                            <span>View Raw Technical Payload</span>
                          </summary>
                          <pre className="font-mono text-[10px] text-slate-700 overflow-x-auto max-h-48 p-2 mt-1 rounded bg-white border border-slate-200">
                            {JSON.stringify(executionResults[wf.slug], null, 2)}
                          </pre>
                        </details>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </>
      ) : (
        /* Live Execution Trace Tab */
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-3">
            <div>
              <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider font-mono">
                Fastn Integration Traces
              </h3>
              <p className="text-[11px] text-[#6B7280]">
                End-to-end audit trace of all inbound webhooks and outbound SaaS dispatches
              </p>
            </div>
            <button
              onClick={loadExecutions}
              disabled={loadingExecutions}
              className="px-3 py-1 rounded-md bg-white border border-[#E5E7EB] hover:bg-slate-50 text-slate-700 text-xs flex items-center gap-1.5 transition-colors cursor-pointer font-medium"
            >
              <RefreshCw className={`w-3 h-3 ${loadingExecutions ? "animate-spin" : ""}`} />
              Refresh Traces
            </button>
          </div>

          {executions.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs border border-dashed border-slate-300 rounded-lg">
              No executions recorded yet. Run a test workflow above or trigger the demo scenario.
            </div>
          ) : (
            <div className="space-y-3">
              {executions.map((ex) => (
                <div
                  key={ex.execution_id}
                  className="p-4 rounded-lg bg-white border border-[#E5E7EB] space-y-2 text-xs shadow-2xs"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-2">
                    <div className="flex items-center gap-2 font-mono">
                      <span className="font-bold text-slate-900">{ex.workflow_slug}</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                          ex.direction === "INBOUND"
                            ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
                            : "bg-blue-50 border border-blue-200 text-blue-700"
                        }`}
                      >
                        {ex.direction}
                      </span>
                      <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px]">
                        {ex.connector}
                      </span>
                      {ex.contract_id && (
                        <span className="text-amber-800 text-[11px] font-semibold">
                          [{ex.contract_id}]
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          ex.status === "SUCCESS" || ex.status === "ARCHIVED" || ex.status === "SYNCED"
                            ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
                            : ex.status === "FAILED"
                            ? "bg-rose-50 border border-rose-200 text-rose-800"
                            : "bg-amber-50 border border-amber-300 text-amber-900"
                        }`}
                      >
                        {ex.status}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {ex.created_at ? new Date(ex.created_at).toLocaleTimeString() : "Just now"}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                    <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                      <span className="text-slate-500 block text-[10px] uppercase font-bold font-mono">
                        Input Parameters
                      </span>
                      {typeof ex.input_summary === "object" && ex.input_summary !== null ? (
                        <div className="space-y-0.5">
                          {Object.entries(ex.input_summary).slice(0, 4).map(([k, v]) => (
                            <div key={k} className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-500 font-mono capitalize">{k.replace(/_/g, " ")}:</span>
                              <span className="text-slate-800 font-semibold truncate max-w-[200px]">
                                {typeof v === "object" ? JSON.stringify(v) : String(v)}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-slate-700">{String(ex.input_summary || "None")}</div>
                      )}
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                      <span className="text-slate-500 block text-[10px] uppercase font-bold font-mono">
                        Output Deliverable
                      </span>
                      {typeof ex.output_summary === "object" && ex.output_summary !== null ? (
                        <div className="space-y-0.5">
                          {Object.entries(ex.output_summary).slice(0, 4).map(([k, v]) => (
                            <div key={k} className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-500 font-mono capitalize">{k.replace(/_/g, " ")}:</span>
                              <span className="text-slate-800 font-semibold truncate max-w-[200px]">
                                {typeof v === "object" ? JSON.stringify(v) : String(v)}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-slate-700">{String(ex.output_summary || "Completed")}</div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
