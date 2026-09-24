import React, { useState, useEffect, useRef } from "react";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sparkles,
  Cloud,
  File,
  ChevronDown,
  ChevronUp,
  X,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  Zap,
} from "lucide-react";
import {
  uploadContractDocument,
  fetchGoogleDriveFiles,
  importGoogleDriveDocument,
  GoogleDriveFile,
} from "../api/client";

export interface IngestedMetadata {
  title?: string;
  counterparty?: string;
  governingLaw?: string;
  filename?: string;
  source?: string;
  wordCount?: number;
  paragraphCount?: number;
  charCount?: number;
}

export interface DocumentIngestBarProps {
  contractText: string;
  onContractTextChange: (text: string, meta?: IngestedMetadata) => void;
  contractId?: string;
  onContractIdChange?: (id: string) => void;
  className?: string;
}

const TEMPLATES = [
  {
    id: "saas_msa",
    name: "NovaCloud Enterprise SaaS MSA (High Risk)",
    description: "Contains asymmetric liability cap, uncapped customer indemnity, and AI data training license.",
    counterparty: "NovaCloud Systems Inc.",
    governingLaw: "State of Delaware",
    text: `MASTER SAAS SERVICES AGREEMENT

This Master SaaS Services Agreement ("Agreement") is made effective as of October 1, 2026, by and between NovaCloud Systems Inc., a Delaware corporation ("Vendor"), and Acme Global Enterprises LLC, a Delaware corporation ("Customer").

SECTION 1: SUBSCRIPTION SERVICES & LICENSE
Vendor grants Customer a non-exclusive license to use the NovaCloud Platform. Authorized users are restricted to Customer employees.

SECTION 2: TERM AND AUTOMATIC RENEWAL
This Agreement shall commence on the Effective Date and continue for an initial term of twelve (12) months. Thereafter, it shall automatically renew for successive 12-month periods unless either Party delivers written notice of non-renewal at least sixty (60) days prior to the expiration of the then-current term. Vendor reserves the right to increase annual fees by up to fifteen percent (15%) upon each renewal without prior consent.

SECTION 3: FEES, BILLING & PAYMENT TERMS
Customer shall pay an annual subscription fee of $240,000 USD, billed quarterly in advance ($60,000 USD/quarter). All invoices are payable Net 30 days. Late payments accrue interest at 1.5% per month.

SECTION 4: SERVICE LEVEL AGREEMENT & PERFORMANCE
Vendor shall use commercially reasonable efforts to maintain 99.9% availability. Customer's sole and exclusive remedy for any outage shall be a service credit equal to 5% of monthly fees.

SECTION 5: DATA OWNERSHIP & DERIVATIVE WORKS
Customer retains ownership of Customer Data. Customer hereby grants Vendor a perpetual, irrevocable, worldwide, royalty-free license to use, aggregate, de-identify, and analyze Customer Data to train, improve, and deploy machine learning models and derivative analytics.

SECTION 6: INDEMNIFICATION
Vendor shall defend Customer against third-party claims alleging copyright infringement. Customer shall defend, indemnify, and hold harmless Vendor against any and all third-party claims, liabilities, and damages arising out of Customer's use of the Service or breach of this Agreement, without financial limitation.

SECTION 7: LIMITATION OF LIABILITY
IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR INDIRECT, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES.
VENDOR'S TOTAL AGGREGATE LIABILITY SHALL BE STRICTLY LIMITED TO THE FEES PAID BY CUSTOMER IN THE ONE (1) MONTH PRECEDING THE INCIDENT GIVING RISE TO LIABILITY.
CUSTOMER'S TOTAL AGGREGATE LIABILITY SHALL BE UNCAPPED.

SECTION 8: GOVERNING LAW & DISPUTE RESOLUTION
This Agreement shall be governed by the laws of the State of Delaware. Disputes shall be resolved through binding arbitration administered by JAMS in New York, NY.`,
  },
  {
    id: "vendor_it_msa",
    name: "Global Tech Solutions MSA (Balanced)",
    description: "Standard commercial agreement with Net 60 payment, 99.9% SLA, and bilateral indemnification.",
    counterparty: "Global Tech Solutions LLC",
    governingLaw: "State of New York",
    text: `MASTER SERVICES AGREEMENT

This Master Services Agreement is entered into as of September 15, 2026, by and between Global Tech Solutions LLC ("Vendor") and Acme Global Enterprises ("Customer").

1. SERVICES: Vendor shall provide enterprise software engineering and technical support services.
2. FEES: All fees are billed monthly and payable Net 60 days from invoice receipt.
3. MUTUAL INDEMNIFICATION: Each party shall defend, indemnify, and hold harmless the other party from any third-party claims resulting from gross negligence or willful misconduct.
4. MUTUAL LIABILITY CAP: Total liability of each party under this Agreement shall not exceed the total fees paid or payable by Customer in the preceding twelve (12) months.
5. GOVERNING LAW: This Agreement is governed by the laws of the State of New York.`,
  },
  {
    id: "gdpr_dpa",
    name: "Data Processing Addendum (GDPR Article 28)",
    description: "Mandatory European data privacy terms, sub-processor 30-day notice, and 48-hr breach reporting.",
    counterparty: "Cloud Data Corp",
    governingLaw: "Republic of Ireland (EU GDPR)",
    text: `DATA PROCESSING ADDENDUM (GDPR ARTICLE 28 COMPLIANCE)

This Data Processing Addendum ("DPA") governs the processing of Personal Data by Vendor ("Data Processor") on behalf of Customer ("Data Controller").

1. SCOPE: Processor processes Personal Data solely on documented instructions from Controller.
2. SUB-PROCESSORS: Processor shall notify Controller at least thirty (30) days in advance of any intended changes concerning the addition or replacement of other processors.
3. SECURITY BREACH: Processor shall notify Controller without undue delay, and in any event within forty-eight (48) hours, of becoming aware of a personal data breach.
4. AUDIT RIGHTS: Processor shall allow for and contribute to audits conducted by Controller or an authorized auditor.
5. GOVERNING LAW: Governed by the laws of Ireland.`,
  },
];

export function DocumentIngestBar({
  contractText,
  onContractTextChange,
  contractId,
  onContractIdChange,
  className = "",
}: DocumentIngestBarProps) {
  const [activeTab, setActiveTab] = useState<"upload" | "gdrive" | "templates">("upload");
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Active loaded document metadata
  const [activeDocName, setActiveDocName] = useState<string>(
    contractText.includes("NovaCloud") ? "NovaCloud_Enterprise_SaaS_Agreement_2026.docx" : "Active_Contract.txt"
  );
  const [activeDocSource, setActiveDocSource] = useState<"upload" | "gdrive" | "template" | "direct">("template");
  const [previewOpen, setPreviewOpen] = useState(false);

  // Google Drive state
  const [gdriveFiles, setGdriveFiles] = useState<GoogleDriveFile[]>([]);
  const [loadingDriveFiles, setLoadingDriveFiles] = useState(false);
  const [customDriveUrl, setCustomDriveUrl] = useState("");
  const [importingDriveId, setImportingDriveId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load Google Drive files when tab is selected
  useEffect(() => {
    if (activeTab === "gdrive" && gdriveFiles.length === 0) {
      loadDriveFiles();
    }
  }, [activeTab]);

  const loadDriveFiles = async () => {
    setLoadingDriveFiles(true);
    try {
      const files = await fetchGoogleDriveFiles();
      setGdriveFiles(files);
    } catch (err: any) {
      console.error("Failed to load drive files:", err);
    } finally {
      setLoadingDriveFiles(false);
    }
  };

  // Handle native file drop or upload
  const handleFileProcess = async (file: File) => {
    setIsProcessing(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await uploadContractDocument(file, false);
      const newId = `CTR-${file.name.substring(0, 8).toUpperCase().replace(/[^A-Z0-9]/g, "")}-${Math.floor(1000 + Math.random() * 9000)}`;

      setActiveDocName(file.name);
      setActiveDocSource("upload");

      if (onContractIdChange) {
        onContractIdChange(newId);
      }

      onContractTextChange(res.content, {
        title: res.detected_title || file.name,
        counterparty: res.detected_parties?.[0],
        filename: file.name,
        source: "native_upload",
        wordCount: res.word_count,
        paragraphCount: res.paragraph_count,
        charCount: res.character_count,
      });

      setSuccessMessage(
        `Successfully uploaded & extracted ${file.name} (${res.word_count.toLocaleString()} words, ${res.paragraph_count} paragraphs).`
      );
    } catch (err: any) {
      if (file.name.endsWith('.txt') || file.name.endsWith('.md') || file.name.endsWith('.json')) {
        try {
          const rawText = await file.text();
          if (rawText && rawText.trim()) {
            const words = rawText.trim().split(/\s+/).length;
            const newId = `CTR-${file.name.substring(0, 8).toUpperCase().replace(/[^A-Z0-9]/g, "")}-${Math.floor(1000 + Math.random() * 9000)}`;
            setActiveDocName(file.name);
            setActiveDocSource("upload");
            if (onContractIdChange) onContractIdChange(newId);
            onContractTextChange(rawText.trim(), {
              title: file.name.replace(/\.[^.]+$/, "").replace(/[-_]/g, " "),
              filename: file.name,
              source: "native_upload",
              wordCount: words,
              paragraphCount: rawText.split('\n').filter(p => p.trim()).length,
              charCount: rawText.length,
            });
            setSuccessMessage(`Extracted ${file.name} (${words} words) via client text intake.`);
            return;
          }
        } catch {
          // ignore fallback error
        }
      }
      setErrorMessage(err.message || "Failed to parse document. Please check format.");
    } finally {
      setIsProcessing(false);
    }
  };

  // Drag & drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileProcess(e.dataTransfer.files[0]);
    }
  };

  // Handle Google Drive Import via Fastn
  const handleImportDrive = async (docId: string, customUrl?: string) => {
    setImportingDriveId(docId);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await importGoogleDriveDocument(docId, customUrl, false);

      setActiveDocName(res.filename);
      setActiveDocSource("gdrive");

      if (onContractIdChange && res.contract_id) {
        onContractIdChange(res.contract_id);
      }

      onContractTextChange(res.content, {
        title: res.title,
        counterparty: res.counterparty,
        governingLaw: res.governing_law,
        filename: res.filename,
        source: "google_drive",
        wordCount: res.word_count,
        paragraphCount: res.paragraph_count,
        charCount: res.character_count,
      });

      setSuccessMessage(
        `Synced from Google Drive via Fastn (${res.fastn_workflow_id}): ${res.filename} (${res.word_count.toLocaleString()} words).`
      );
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to import from Google Drive via Fastn.");
    } finally {
      setImportingDriveId(null);
    }
  };

  // Handle Template Selection
  const handleSelectTemplate = (tpl: typeof TEMPLATES[0]) => {
    setActiveDocName(`${tpl.id}.docx`);
    setActiveDocSource("template");
    const words = tpl.text.split(/\s+/).length;
    const paras = tpl.text.split("\n\n").length;

    onContractTextChange(tpl.text, {
      title: tpl.name,
      counterparty: tpl.counterparty,
      governingLaw: tpl.governingLaw,
      filename: `${tpl.id}.docx`,
      source: "template",
      wordCount: words,
      paragraphCount: paras,
      charCount: tpl.text.length,
    });

    setSuccessMessage(`Loaded template: ${tpl.name}`);
  };

  const wordCount = contractText.split(/\s+/).filter(Boolean).length;
  const paragraphCount = contractText.split("\n").filter((p) => p.trim()).length;

  return (
    <div className={`bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden ${className}`}>
      {/* Top Banner: Active Document Status */}
      <div className="px-4 py-3 bg-gradient-to-r from-slate-50 via-blue-50/40 to-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="p-1.5 rounded-lg bg-blue-600 text-white shadow-xs">
            <FileText className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-bold text-slate-900 truncate">{activeDocName}</span>
              <span
                className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full ${
                  activeDocSource === "gdrive"
                    ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                    : activeDocSource === "upload"
                    ? "bg-blue-100 text-blue-800 border border-blue-200"
                    : "bg-slate-200 text-slate-700"
                }`}
              >
                {activeDocSource === "gdrive"
                  ? "☁️ Google Drive (Fastn)"
                  : activeDocSource === "upload"
                  ? "📁 Local Upload"
                  : "📋 Sample Library"}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-mono">
              {wordCount.toLocaleString()} words • {paragraphCount} paragraphs • {contractText.length.toLocaleString()} chars
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPreviewOpen(!previewOpen)}
            className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer shadow-2xs"
          >
            {previewOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            <span>{previewOpen ? "Hide Clauses" : "View Extracted Text"}</span>
          </button>
        </div>
      </div>

      {/* Messages */}
      {errorMessage && (
        <div className="mx-4 mt-3 p-2.5 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{errorMessage}</span>
        </div>
      )}
      {successMessage && (
        <div className="mx-4 mt-3 p-2.5 bg-emerald-50 border border-emerald-200 rounded-md text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Mode Switcher Tabs */}
      <div className="px-4 pt-3 border-b border-slate-200 bg-slate-50/50 flex items-center gap-2">
        <button
          type="button"
          onClick={() => setActiveTab("upload")}
          className={`flex items-center gap-1.5 pb-2.5 px-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === "upload"
              ? "border-blue-600 text-blue-600 bg-white rounded-t-md shadow-2xs"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload Document (PDF, Word, TXT)</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("gdrive")}
          className={`flex items-center gap-1.5 pb-2.5 px-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === "gdrive"
              ? "border-emerald-600 text-emerald-700 bg-white rounded-t-md shadow-2xs"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Cloud className="w-4 h-4 text-emerald-600" />
          <span>Google Drive (Fastn Integration)</span>
          <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.2 rounded font-mono">LIVE</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("templates")}
          className={`flex items-center gap-1.5 pb-2.5 px-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === "templates"
              ? "border-indigo-600 text-indigo-600 bg-white rounded-t-md shadow-2xs"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Contract Templates &amp; Manual Edit</span>
        </button>
      </div>

      {/* Tab Panels */}
      <div className="p-4">
        {/* TAB 1: NATIVE FILE UPLOAD */}
        {activeTab === "upload" && (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-all ${
              isDragging
                ? "border-blue-500 bg-blue-50/60 scale-[1.005]"
                : "border-slate-300 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-400"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,.md,.json"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileProcess(e.target.files[0]);
                }
                e.target.value = "";
              }}
              className="hidden"
            />

            <div className="flex flex-col items-center justify-center space-y-2">
              <div className="p-3 bg-blue-100 text-blue-700 rounded-full">
                {isProcessing ? (
                  <RefreshCw className="w-6 h-6 animate-spin" />
                ) : (
                  <UploadCloud className="w-6 h-6" />
                )}
              </div>

              <div>
                <h4 className="text-sm font-bold text-slate-800">
                  {isProcessing ? "Extracting Clauses & Parsing Document..." : "Drag & Drop Contract File Here"}
                </h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  No copy-pasting required! Supports Microsoft Word, Adobe PDF, Markdown, and text files.
                </p>
              </div>

              <div className="pt-2 flex items-center gap-2">
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors cursor-pointer disabled:opacity-50"
                >
                  Browse Files
                </button>
                <span className="text-xs text-slate-400">or drop document into this box</span>
              </div>

              {/* Supported Format Badges */}
              <div className="pt-3 flex flex-wrap items-center justify-center gap-1.5 text-[11px]">
                <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-medium">
                  📄 Word (.docx)
                </span>
                <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium">
                  📑 PDF (.pdf)
                </span>
                <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-medium">
                  📝 Plain Text (.txt)
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
                  Markdown (.md)
                </span>
                <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-medium">
                  JSON (.json)
                </span>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: GOOGLE DRIVE FASTN INTEGRATION */}
        {activeTab === "gdrive" && (
          <div className="space-y-4">
            <div className="p-3.5 bg-emerald-50/70 border border-emerald-200 rounded-lg flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-emerald-600 text-white rounded-lg">
                  <Cloud className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-emerald-950">Fastn Google Drive Contract Inbound Relay</h4>
                  <p className="text-[11px] text-emerald-800">
                    Connected to Fastn Workflow: <code className="font-mono font-semibold">cas-contract-intake (wf_0c61baf31b93)</code>
                  </p>
                </div>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded bg-emerald-200/70 text-emerald-900 border border-emerald-300">
                Connected &amp; Ready
              </span>
            </div>

            {/* Google Drive Pre-Connected Catalog */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-700 font-semibold">
                <span>Select Enterprise Contract from Google Drive:</span>
                <button
                  type="button"
                  onClick={loadDriveFiles}
                  disabled={loadingDriveFiles}
                  className="flex items-center gap-1 text-[11px] text-emerald-700 hover:text-emerald-900 cursor-pointer"
                >
                  <RefreshCw className={`w-3 h-3 ${loadingDriveFiles ? "animate-spin" : ""}`} />
                  <span>Refresh Drive</span>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {gdriveFiles.map((file) => (
                  <div
                    key={file.id}
                    className="p-3 rounded-lg border border-slate-200 bg-white hover:border-emerald-500 hover:bg-emerald-50/30 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-1.5 truncate">
                          <File className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          <span className="text-xs font-bold text-slate-900 truncate">{file.title}</span>
                        </div>
                        <span className="text-[10px] font-mono bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded shrink-0">
                          {file.file_type.toUpperCase()} • {file.size_kb} KB
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">{file.description}</p>
                      <p className="text-[10px] text-slate-400 mt-1 font-mono">📁 {file.folder}</p>
                    </div>

                    <div className="pt-2.5 mt-2 border-t border-slate-100 flex items-center justify-between">
                      <span className="text-[10px] text-slate-500">Party: {file.counterparty}</span>
                      <button
                        type="button"
                        onClick={() => handleImportDrive(file.id)}
                        disabled={importingDriveId === file.id}
                        className="flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 shadow-2xs"
                      >
                        {importingDriveId === file.id ? (
                          <>
                            <RefreshCw className="w-3 h-3 animate-spin" />
                            <span>Importing...</span>
                          </>
                        ) : (
                          <>
                            <ArrowRight className="w-3 h-3" />
                            <span>Import via Fastn</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Custom Google Drive Link Input */}
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
              <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
                Or Ingest Custom Google Drive Document Link
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={customDriveUrl}
                  onChange={(e) => setCustomDriveUrl(e.target.value)}
                  placeholder="https://drive.google.com/file/d/1A2B3C... or File ID"
                  className="flex-1 px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-emerald-500 text-slate-800 font-mono"
                />
                <button
                  type="button"
                  disabled={!customDriveUrl.trim() || importingDriveId !== null}
                  onClick={() => handleImportDrive("custom_gdrive_url", customDriveUrl)}
                  className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-md transition-colors cursor-pointer disabled:opacity-50 whitespace-nowrap"
                >
                  Fetch via Fastn
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: TEMPLATES & DIRECT CLAUSE EDIT */}
        {activeTab === "templates" && (
          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 mb-1.5 block">Quick-Load Legal Agreements:</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {TEMPLATES.map((tpl) => (
                  <button
                    key={tpl.id}
                    type="button"
                    onClick={() => handleSelectTemplate(tpl)}
                    className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-white hover:border-indigo-500 hover:shadow-2xs text-left transition-all cursor-pointer flex flex-col justify-between"
                  >
                    <span className="text-xs font-bold text-slate-900 mb-1">{tpl.name}</span>
                    <p className="text-[11px] text-slate-500 line-clamp-2">{tpl.description}</p>
                    <span className="text-[10px] font-medium text-indigo-600 mt-2">Click to load &rarr;</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-slate-700">Contract Operative Text (Direct Editor):</label>
                <button
                  type="button"
                  onClick={() => onContractTextChange("")}
                  className="text-[11px] text-rose-600 hover:text-rose-800 font-medium cursor-pointer"
                >
                  Clear Text
                </button>
              </div>
              <textarea
                rows={8}
                value={contractText}
                onChange={(e) => onContractTextChange(e.target.value)}
                placeholder="Paste or edit clauses here..."
                className="w-full p-3 text-xs font-mono bg-white border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 leading-relaxed"
              />
            </div>
          </div>
        )}

        {/* Collapsible Extracted Text Preview Drawer */}
        {previewOpen && (
          <div className="mt-4 pt-3 border-t border-slate-200">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-blue-600" />
                Extracted Contract Clauses &amp; Operative Language ({wordCount} words)
              </span>
              <button
                type="button"
                onClick={() => setPreviewOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <textarea
              rows={10}
              value={contractText}
              onChange={(e) => onContractTextChange(e.target.value)}
              className="w-full p-3 font-mono text-xs bg-slate-900 text-slate-100 rounded-lg border border-slate-700 leading-relaxed focus:outline-none"
            />
          </div>
        )}
      </div>
    </div>
  );
}
