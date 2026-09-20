import React, { useState } from "react";
import { X, FileText, Upload, Sparkles } from "lucide-react";
import { uploadContract } from "../api/client";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (contractId: string) => void;
}

const SAMPLE_TEXT = `MASTER SERVICES AGREEMENT

This Master Services Agreement ("Agreement") is made effective as of October 1, 2026, by and between:
Acme Global Enterprises ("Customer"), a Delaware corporation, and
NovaCloud Inc. ("Vendor"), a Delaware corporation.

1. SERVICES AND SERVICE LEVEL AGREEMENT
Vendor shall provide cloud infrastructure services with 99.9% monthly uptime. If uptime falls below 99.9%, Customer's sole remedy shall be a 5% service credit.

2. FEES AND PAYMENT
Customer shall pay all fees Net 30 days from invoice date. Overdue amounts incur interest at 1.5% per month.

3. TERM AND AUTOMATIC RENEWAL
This Agreement shall commence on the Effective Date and continue for an initial term of one (1) year. Thereafter, it shall automatically renew for successive one-year terms unless either party gives written notice of non-renewal at least sixty (60) days prior to the expiration of the current term.

4. CONFIDENTIALITY
Each party agrees to protect the Confidential Information of the other party with the same degree of care it uses for its own confidential information, but in no event less than reasonable care.

5. INTELLECTUAL PROPERTY & INDEPENDENT CONTRACTOR
Vendor retains all right, title, and interest in and to the Services, including any software or derivatives developed under this Agreement. Customer receives a non-exclusive license.

6. INDEMNIFICATION
Vendor shall defend, indemnify, and hold harmless Customer against third-party claims alleging that the Service infringes any valid patent or copyright.
Customer shall defend, indemnify, and hold harmless Vendor against any and all claims, liabilities, damages, losses, and expenses arising out of Customer's use of the Service or violation of applicable laws. Customer's indemnity shall be uncapped.

7. LIMITATION OF LIABILITY
EXCEPT FOR CUSTOMER'S INDEMNIFICATION OBLIGATIONS AND BREACH OF CONFIDENTIALITY, IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR INDIRECT, INCIDENTAL, CONSEQUENTIAL, SPECIAL, OR PUNITIVE DAMAGES.
VENDOR'S TOTAL AGGREGATE LIABILITY UNDER THIS AGREEMENT SHALL BE LIMITED TO THE FEES PAID BY CUSTOMER IN THE ONE (1) MONTH PRECEDING THE EVENT GIVING RISE TO LIABILITY.
CUSTOMER'S AGGREGATE LIABILITY SHALL BE UNCAPPED.

8. GOVERNING LAW & DISPUTE RESOLUTION
This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to conflict of laws principles. The parties submit to the exclusive jurisdiction of the state and federal courts in Wilmington, Delaware.`;

export function UploadModal({ isOpen, onClose, onSuccess }: UploadModalProps) {
  const [title, setTitle] = useState("Enterprise Cloud Services Agreement");
  const [counterparty, setCounterparty] = useState("NovaCloud Inc.");
  const [governingLaw, setGoverningLaw] = useState("State of Delaware");
  const [content, setContent] = useState(SAMPLE_TEXT);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) {
      setError("Please provide contract text.");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const res = await uploadContract(title, content, {
        counterparty,
        governing_law: governingLaw,
        source: "web_intake_modal",
      });
      onSuccess(res.contract_id);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to upload contract");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
      <div className="bg-white border border-[#E5E7EB] rounded-xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-[#E5E7EB] flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            <h2 className="text-sm font-bold text-[#111827]">Contract Intake &amp; Ingestion</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1 rounded-md hover:bg-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4 flex-1">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-md">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Agreement Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="w-full bg-white border border-[#E5E7EB] rounded-md px-3 py-1.5 text-xs text-[#111827] focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Counterparty Name</label>
              <input
                type="text"
                value={counterparty}
                onChange={(e) => setCounterparty(e.target.value)}
                className="w-full bg-white border border-[#E5E7EB] rounded-md px-3 py-1.5 text-xs text-[#111827] focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Governing Jurisdiction</label>
            <select
              value={governingLaw}
              onChange={(e) => setGoverningLaw(e.target.value)}
              className="w-full bg-white border border-[#E5E7EB] rounded-md px-3 py-1.5 text-xs text-[#111827] focus:outline-hidden focus:border-blue-500 cursor-pointer"
            >
              <option value="State of Delaware">State of Delaware</option>
              <option value="State of New York">State of New York</option>
              <option value="State of California">State of California</option>
              <option value="England & Wales">England &amp; Wales</option>
              <option value="Federal (United States)">Federal (United States)</option>
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700">Contract Raw Text</label>
              <button
                type="button"
                onClick={() => setContent(SAMPLE_TEXT)}
                className="flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800 font-medium cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Reset Sample Contract
              </button>
            </div>
            <textarea
              rows={10}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste contract text, clauses, or agreement terms..."
              className="w-full font-mono bg-slate-50 border border-slate-200 rounded-md p-3 text-xs text-slate-800 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500 leading-relaxed"
            />
          </div>

          <div className="pt-3 flex items-center justify-end gap-3 border-t border-[#E5E7EB]">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-md transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-md shadow-xs transition-colors cursor-pointer disabled:opacity-50"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>{loading ? "Ingesting..." : "Ingest & Create"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
