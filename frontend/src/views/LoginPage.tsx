import React, { useState } from "react";
import { Shield, Sparkles, User, Lock, Mail, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login, register, loginAsGuest } = useAuth();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGuestLoading, setIsGuestLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      if (tab === "login") {
        await login(email, password);
      } else {
        await register(email, password, fullName);
      }
    } catch (err: any) {
      setError(err?.message || "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGuest = async () => {
    setError(null);
    setIsGuestLoading(true);
    try {
      await loginAsGuest();
    } catch (err: any) {
      setError(err?.message || "Failed to start guest session.");
    } finally {
      setIsGuestLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-[#0F172A] via-[#1E293B] to-[#0A0F1D] flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-white">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-linear-to-tr from-blue-600 to-indigo-500 shadow-xl shadow-blue-500/25 mb-4">
          <Shield className="w-7 h-7 text-white" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Contract Agentic Society (CAS)
        </h2>
        <p className="mt-2 text-xs text-slate-400">
          Federated Multi-Agent Legal & Negotiation Mesh Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-[#1E293B]/80 backdrop-blur-xl border border-slate-700/60 rounded-2xl shadow-2xl p-6 sm:p-8">
          {/* Tabs */}
          <div className="flex border-b border-slate-700/80 mb-6">
            <button
              onClick={() => {
                setTab("login");
                setError(null);
              }}
              className={`flex-1 pb-3 text-xs font-semibold tracking-wider uppercase transition-colors border-b-2 ${
                tab === "login"
                  ? "border-blue-500 text-blue-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setTab("register");
                setError(null);
              }}
              className={`flex-1 pb-3 text-xs font-semibold tracking-wider uppercase transition-colors border-b-2 ${
                tab === "register"
                  ? "border-blue-500 text-blue-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Register
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {tab === "register" && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <User className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="General Counsel"
                    className="block w-full pl-9 pr-3 py-2 text-xs bg-slate-900/60 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Corporate Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="lawyer@enterprise.com"
                  className="block w-full pl-9 pr-3 py-2 text-xs bg-slate-900/60 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-9 pr-3 py-2 text-xs bg-slate-900/60 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 px-4 bg-linear-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-blue-500/25 transition disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting ? (
                <span>Authenticating...</span>
              ) : tab === "login" ? (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              ) : (
                <>
                  <span>Create Account</span>
                  <CheckCircle2 className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-700/70" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-[#1E293B] px-3 text-slate-400 text-[10px] tracking-wider font-semibold">
                Or Continue Instantly
              </span>
            </div>
          </div>

          {/* Guest Mode Button */}
          <button
            type="button"
            onClick={handleGuest}
            disabled={isGuestLoading}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 rounded-lg text-xs font-semibold text-slate-200 transition shadow-xs cursor-pointer group"
          >
            <Sparkles className="w-4 h-4 text-amber-400 group-hover:rotate-12 transition-transform" />
            <span>
              {isGuestLoading ? "Initializing Guest..." : "Continue as Guest (Read-Only Demo)"}
            </span>
          </button>

          <p className="mt-4 text-[10px] text-center text-slate-400">
            Guest mode provides read-only exploration of the live dashboard, 15-stage multi-agent demo, and benchmark suite without saving credentials.
          </p>
        </div>
      </div>
    </div>
  );
}
