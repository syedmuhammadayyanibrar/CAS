import React, { useState, useEffect, useRef } from "react";
import {
  Shield,
  User,
  Lock,
  Mail,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  KeyRound,
  RefreshCw,
  Clock,
  ArrowLeft,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { fetchAuthConfig } from "../api/client";

declare global {
  interface Window {
    google?: any;
    PasswordCredential?: any;
  }
}

const REMEMBERED_EMAIL_KEY = "cas_remembered_email";

function formatDuration(totalSeconds: number): string {
  const sec = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(sec / 3600);
  const minutes = Math.floor((sec % 3600) / 60);
  const seconds = sec % 60;
  if (hours > 0) {
    return `${hours}h ${String(minutes).padStart(2, "0")}m ${String(seconds).padStart(2, "0")}s`;
  }
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

async function storeBrowserCredentials(email: string, password: string, name?: string) {
  try {
    if (
      typeof window !== "undefined" &&
      window.PasswordCredential &&
      navigator.credentials &&
      typeof navigator.credentials.store === "function"
    ) {
      const cred = new window.PasswordCredential({
        id: email,
        password,
        name: name || email,
      });
      await navigator.credentials.store(cred);
    }
  } catch {
    // Ignore if browser blocks or does not support PasswordCredential
  }
}

export function LoginPage() {
  const { login, register, requestOtp, verifyOtp, loginWithGoogle, loginAsGuest } = useAuth();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [loginMethod, setLoginMethod] = useState<"password" | "otp">("password");

  const [email, setEmail] = useState(() => {
    try {
      return localStorage.getItem(REMEMBERED_EMAIL_KEY) || "";
    } catch {
      return "";
    }
  });
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [fullName, setFullName] = useState("");

  // OTP Verification State
  const [otpStep, setOtpStep] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [otpPurpose, setOtpPurpose] = useState<"login" | "register">("register");
  const [otpExpiresIn, setOtpExpiresIn] = useState(300); // 5 minutes (300s)
  const [resendWaitIn, setResendWaitIn] = useState(120); // 2 minutes initial (120s)
  const [resendCount, setResendCount] = useState(1);

  const [error, setError] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [isGuestLoading, setIsGuestLoading] = useState(false);
  const [googleClientId, setGoogleClientId] = useState<string | null>(
    "853519585394-cqa4lvkg6sonanj128hg7qqmf84vnv3k.apps.googleusercontent.com"
  );
  const googleBtnRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAuthConfig().then((cfg) => {
      if (cfg.google_client_id) setGoogleClientId(cfg.google_client_id);
    });
  }, []);

  // Countdown tick for OTP 5-minute validity and progressive resend wait timer
  useEffect(() => {
    if (!otpStep) return;
    const interval = setInterval(() => {
      setOtpExpiresIn((prev) => (prev > 0 ? prev - 1 : 0));
      setResendWaitIn((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [otpStep]);

  // Render Google's official button
  useEffect(() => {
    if (!googleClientId || otpStep) return;
    let cancelled = false;
    const init = () => {
      if (cancelled || !window.google?.accounts?.id || !googleBtnRef.current) return false;
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response: any) => {
          if (!response?.credential) return;
          setError(null);
          setIsGoogleLoading(true);
          try {
            await loginWithGoogle(response.credential);
          } catch (err: any) {
            setError(err?.message || "Google sign-in failed.");
          } finally {
            setIsGoogleLoading(false);
          }
        },
      });
      window.google.accounts.id.renderButton(googleBtnRef.current, {
        theme: "outline",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: 320,
      });
      return true;
    };
    if (init()) return () => { cancelled = true; };
    const timer = setInterval(() => {
      if (init()) clearInterval(timer);
    }, 300);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [googleClientId, loginWithGoogle, otpStep]);

  const persistEmailPreference = (targetEmail: string) => {
    try {
      if (rememberMe && targetEmail) {
        localStorage.setItem(REMEMBERED_EMAIL_KEY, targetEmail.trim().toLowerCase());
      } else {
        localStorage.removeItem(REMEMBERED_EMAIL_KEY);
      }
    } catch {
      // Ignore storage errors
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessNotice(null);
    setIsSubmitting(true);
    try {
      persistEmailPreference(email);

      if (tab === "login") {
        if (loginMethod === "otp") {
          const otpRes = await requestOtp(email, "login");
          setOtpPurpose("login");
          setOtpCode("");
          setOtpExpiresIn(otpRes.otp_expires_in_seconds || 300);
          setResendWaitIn(otpRes.resend_wait_seconds || 120);
          setResendCount(otpRes.resend_count || 1);
          setOtpStep(true);
          setSuccessNotice(
            otpRes.fallback_otp_code
              ? `Verification code generated for ${email}: ${otpRes.fallback_otp_code}`
              : `A 6-digit verification code has been sent to ${email} via Resend.`
          );
        } else {
          await login(email, password, rememberMe);
          await storeBrowserCredentials(email, password);
        }
      } else {
        const res = await register(email, password, fullName, rememberMe);
        await storeBrowserCredentials(email, password, fullName);
        if (res?.requires_verification) {
          setOtpPurpose("register");
          setOtpCode("");
          setOtpExpiresIn(res.otp_expires_in_seconds || 300);
          setResendWaitIn(res.resend_wait_seconds || 120);
          setResendCount(1);
          setOtpStep(true);
          setSuccessNotice(
            res.fallback_otp_code
              ? `Account created! Verification code for ${email}: ${res.fallback_otp_code}`
              : `Account created! Enter the 6-digit OTP sent to ${email} to verify your email and sign in.`
          );
        }
      }
    } catch (err: any) {
      if (err?.retryAfterSeconds) {
        setResendWaitIn(err.retryAfterSeconds);
      }
      setError(err?.message || "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessNotice(null);
    if (otpCode.trim().length < 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }
    if (otpExpiresIn <= 0) {
      setError("This OTP has expired (5-minute limit). Please click Resend OTP to get a new code.");
      return;
    }
    setIsSubmitting(true);
    try {
      await verifyOtp(email, otpCode.trim(), rememberMe);
    } catch (err: any) {
      setError(err?.message || "Invalid or expired OTP code.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendOtp = async () => {
    if (resendWaitIn > 0 || isResending) return;
    setError(null);
    setSuccessNotice(null);
    setIsResending(true);
    try {
      const otpRes = await requestOtp(email, otpPurpose);
      setOtpCode("");
      setOtpExpiresIn(otpRes.otp_expires_in_seconds || 300);
      setResendWaitIn(otpRes.resend_wait_seconds || 120);
      setResendCount(otpRes.resend_count || resendCount + 1);
      setSuccessNotice(
        `New 6-digit OTP sent to ${email}. Valid for 5 minutes (next resend cooldown: ${formatDuration(
          otpRes.resend_wait_seconds || 120
        )}).`
      );
    } catch (err: any) {
      if (err?.retryAfterSeconds) {
        setResendWaitIn(err.retryAfterSeconds);
      }
      setError(err?.message || "Could not resend OTP right now.");
    } finally {
      setIsResending(false);
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
    <div className="min-h-screen bg-white flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-800">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-600 shadow-lg shadow-blue-600/20 mb-4">
          <Shield className="w-7 h-7 text-white" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Contract Agentic Society (CAS)
        </h2>
        <p className="mt-1.5 text-xs text-slate-500 font-medium">
          Federated Multi-Agent Legal & Negotiation Mesh Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white border border-slate-200/90 rounded-2xl shadow-xl shadow-slate-200/50 p-6 sm:p-8">
          {otpStep ? (
            /* ================= 6-DIGIT OTP VERIFICATION VIEW ================= */
            <div>
              <div className="flex items-center justify-between mb-4">
                <button
                  type="button"
                  onClick={() => {
                    setOtpStep(false);
                    setError(null);
                    setSuccessNotice(null);
                  }}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 cursor-pointer"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back</span>
                </button>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  <Clock className="w-3 h-3" />
                  <span>
                    {otpExpiresIn > 0
                      ? `OTP valid: ${formatDuration(otpExpiresIn)}`
                      : "OTP Expired"}
                  </span>
                </span>
              </div>

              <h3 className="text-base font-bold text-slate-900 mb-1">
                Verify Your Email with OTP
              </h3>
              <p className="text-xs text-slate-500 mb-5 leading-relaxed">
                Enter the 6-digit verification code sent via Resend to{" "}
                <span className="font-semibold text-slate-800">{email}</span>. Codes expire after 5 minutes.
              </p>

              {error && (
                <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
                  <span>{error}</span>
                </div>
              )}

              {successNotice && (
                <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                  <span>{successNotice}</span>
                </div>
              )}

              <form onSubmit={handleVerifyOtp} className="space-y-4">
                <div>
                  <label
                    htmlFor="cas-otp-input"
                    className="block text-xs font-medium text-slate-700 mb-1.5"
                  >
                    6-Digit Verification Code
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <KeyRound className="w-4 h-4" />
                    </div>
                    <input
                      id="cas-otp-input"
                      name="otp"
                      type="text"
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      maxLength={6}
                      required
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                      placeholder="123456"
                      className="block w-full pl-10 pr-4 py-2.5 text-center tracking-[0.5em] font-mono text-base font-bold bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-300 focus:outline-hidden focus:ring-2 focus:ring-blue-600 focus:bg-white focus:border-transparent transition"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || otpCode.length < 6 || otpExpiresIn <= 0}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-md shadow-blue-600/20 transition disabled:opacity-50 cursor-pointer"
                >
                  {isSubmitting ? (
                    <span>Verifying Code...</span>
                  ) : (
                    <>
                      <span>Verify OTP & Complete Sign In</span>
                      <CheckCircle2 className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              <div className="mt-5 pt-4 border-t border-slate-200 flex items-center justify-between text-xs">
                <span className="text-slate-500">Didn&apos;t receive the code?</span>
                <button
                  type="button"
                  onClick={handleResendOtp}
                  disabled={resendWaitIn > 0 || isResending}
                  className="inline-flex items-center gap-1.5 font-semibold text-blue-600 hover:text-blue-700 disabled:text-slate-400 disabled:cursor-not-allowed cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isResending ? "animate-spin" : ""}`} />
                  {resendWaitIn > 0 ? (
                    <span>Resend in {formatDuration(resendWaitIn)}</span>
                  ) : isResending ? (
                    <span>Sending...</span>
                  ) : (
                    <span>Resend OTP</span>
                  )}
                </button>
              </div>
              {resendCount > 1 && (
                <p className="mt-2 text-[11px] text-slate-400 text-right">
                  Progressive security cooldown active (request #{resendCount}, max 2 hours).
                </p>
              )}
            </div>
          ) : (
            /* ================= SIGN IN / REGISTER VIEW ================= */
            <>
              {/* Tabs */}
              <div className="flex border-b border-slate-200 mb-6">
                <button
                  type="button"
                  onClick={() => {
                    setTab("login");
                    setError(null);
                    setSuccessNotice(null);
                  }}
                  className={`flex-1 pb-3 text-xs font-semibold tracking-wider uppercase transition-colors border-b-2 cursor-pointer ${
                    tab === "login"
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-slate-400 hover:text-slate-600"
                  }`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setTab("register");
                    setError(null);
                    setSuccessNotice(null);
                  }}
                  className={`flex-1 pb-3 text-xs font-semibold tracking-wider uppercase transition-colors border-b-2 cursor-pointer ${
                    tab === "register"
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-slate-400 hover:text-slate-600"
                  }`}
                >
                  Create Account
                </button>
              </div>

              {error && (
                <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
                  <span>{error}</span>
                </div>
              )}

              {successNotice && (
                <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                  <span>{successNotice}</span>
                </div>
              )}

              {/* Continue with Google */}
              {googleClientId ? (
                <div
                  ref={googleBtnRef}
                  className={`mb-4 flex justify-center min-h-[44px] ${
                    isGoogleLoading ? "opacity-50 pointer-events-none" : ""
                  }`}
                />
              ) : null}

              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-200" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-3 text-slate-400 text-[10px] tracking-wider font-semibold">
                    Or with corporate email
                  </span>
                </div>
              </div>

              {/* Password vs Email OTP mode selector on Sign In tab */}
              {tab === "login" && (
                <div className="grid grid-cols-2 gap-1.5 p-1 bg-slate-100 rounded-lg mb-4">
                  <button
                    type="button"
                    onClick={() => {
                      setLoginMethod("password");
                      setError(null);
                    }}
                    className={`py-1.5 text-[11px] font-semibold rounded-md transition cursor-pointer ${
                      loginMethod === "password"
                        ? "bg-white text-slate-900 shadow-2xs"
                        : "text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    Password Sign In
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setLoginMethod("otp");
                      setError(null);
                    }}
                    className={`py-1.5 text-[11px] font-semibold rounded-md transition cursor-pointer ${
                      loginMethod === "otp"
                        ? "bg-white text-slate-900 shadow-2xs"
                        : "text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    Email OTP Code
                  </button>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4" autoComplete="on">
                {tab === "register" && (
                  <div>
                    <label
                      htmlFor="cas-fullname"
                      className="block text-xs font-medium text-slate-700 mb-1"
                    >
                      Full Name
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                        <User className="w-4 h-4" />
                      </div>
                      <input
                        id="cas-fullname"
                        name="name"
                        type="text"
                        autoComplete="name"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="General Counsel"
                        className="block w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-600 focus:bg-white focus:border-transparent transition"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label
                    htmlFor="cas-email"
                    className="block text-xs font-medium text-slate-700 mb-1"
                  >
                    Corporate Email
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      id="cas-email"
                      name="email"
                      type="email"
                      autoComplete="username email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="lawyer@enterprise.com"
                      className="block w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-600 focus:bg-white focus:border-transparent transition"
                    />
                  </div>
                </div>

                {(tab === "register" || loginMethod === "password") && (
                  <div>
                    <label
                      htmlFor="cas-password"
                      className="block text-xs font-medium text-slate-700 mb-1"
                    >
                      Password
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                        <Lock className="w-4 h-4" />
                      </div>
                      <input
                        id="cas-password"
                        name="password"
                        type={showPassword ? "text" : "password"}
                        autoComplete={tab === "register" ? "new-password" : "current-password"}
                        minLength={8}
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••••••"
                        className="block w-full pl-9 pr-9 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-600 focus:bg-white focus:border-transparent transition"
                      />
                      <button
                        type="button"
                        tabIndex={-1}
                        onClick={() => setShowPassword((prev) => !prev)}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 cursor-pointer"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* Remember me / Save login credentials */}
                <div className="flex items-center justify-between pt-0.5">
                  <label className="inline-flex items-center gap-2 text-xs text-slate-600 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span>Keep me signed in</span>
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-md shadow-blue-600/20 transition disabled:opacity-50 cursor-pointer"
                >
                  {isSubmitting ? (
                    <span>Processing...</span>
                  ) : tab === "login" && loginMethod === "otp" ? (
                    <>
                      <span>Send 6-Digit Login OTP</span>
                      <Mail className="w-4 h-4" />
                    </>
                  ) : tab === "login" ? (
                    <>
                      <span>Sign In</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  ) : (
                    <>
                      <span>Create Account & Send OTP</span>
                      <CheckCircle2 className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-200" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-3 text-slate-400 text-[10px] tracking-wider font-semibold">
                    Or Continue Instantly
                  </span>
                </div>
              </div>

              {/* Guest Mode Button without emoji/sparkle */}
              <button
                type="button"
                onClick={handleGuest}
                disabled={isGuestLoading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-slate-100 hover:bg-slate-200/80 border border-slate-300/80 rounded-lg text-xs font-semibold text-slate-700 transition shadow-2xs cursor-pointer"
              >
                <span>
                  {isGuestLoading ? "Initializing Guest..." : "Continue as Guest"}
                </span>
              </button>

              <p className="mt-4 text-[11px] text-center text-slate-400 leading-relaxed">
                Guest mode allows contract uploads, AI analysis, the 15-stage multi-agent demo, and benchmark exploration without saving credentials.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
