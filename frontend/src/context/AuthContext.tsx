import React, { createContext, useContext, useState, useEffect } from "react";
import {
  AuthUser,
  OTPDispatchResponse,
  getStoredAccessToken,
  setStoredAccessToken,
  apiLogin,
  apiRegister,
  apiRequestOtp,
  apiVerifyOtp,
  apiGuestLogin,
  apiGoogleLogin,
  apiLogout,
  fetchCurrentUser,
  refreshAccessToken,
  UNAUTHORIZED_EVENT,
} from "../api/client";

interface RegisterResult {
  requires_verification?: boolean;
  otp_expires_in_seconds?: number;
  resend_wait_seconds?: number;
  email_delivered?: boolean;
  fallback_otp_code?: string | null;
}

interface AuthContextType {
  user: AuthUser | null;
  role: string | null;
  isAuthenticated: boolean;
  isGuest: boolean;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName?: string,
    rememberMe?: boolean
  ) => Promise<RegisterResult>;
  requestOtp: (
    email: string,
    purpose?: "login" | "register" | "verification"
  ) => Promise<OTPDispatchResponse>;
  verifyOtp: (email: string, otp: string, rememberMe?: boolean) => Promise<void>;
  loginWithGoogle: (credential: string) => Promise<void>;
  loginAsGuest: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Proactively refresh the 15-minute access token every 12 minutes so active sessions never drop
const PROACTIVE_REFRESH_INTERVAL_MS = 12 * 60 * 1000;

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Any API call that ends in an unrecoverable 401 returns the user to the login screen
  useEffect(() => {
    const onUnauthorized = () => setUser(null);
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  // Initialize session on mount
  useEffect(() => {
    async function initAuth() {
      try {
        const token = getStoredAccessToken();
        if (token) {
          const profile = await fetchCurrentUser();
          setUser(profile);
        } else {
          // Attempt silent refresh via HttpOnly refresh cookie
          const newToken = await refreshAccessToken();
          if (newToken) {
            const profile = await fetchCurrentUser();
            setUser(profile);
          }
        }
      } catch {
        setStoredAccessToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }
    initAuth();
  }, []);

  // Proactive background refresh timer for authenticated non-guest sessions
  useEffect(() => {
    if (!user || user.role === "guest") return;
    const interval = setInterval(() => {
      refreshAccessToken().catch(() => {});
    }, PROACTIVE_REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [user]);

  const login = async (email: string, password: string, rememberMe: boolean = false) => {
    const res = await apiLogin(email, password, rememberMe);
    setUser(res.user);
  };

  const register = async (
    email: string,
    password: string,
    fullName?: string,
    rememberMe: boolean = false
  ): Promise<RegisterResult> => {
    const res = await apiRegister(email, password, fullName, rememberMe);
    // Only set user immediately if OTP verification is not required
    if (!res.requires_verification) {
      setUser(res.user);
    }
    return {
      requires_verification: res.requires_verification,
      otp_expires_in_seconds: res.otp_expires_in_seconds,
      resend_wait_seconds: res.resend_wait_seconds,
      email_delivered: res.email_delivered,
      fallback_otp_code: res.fallback_otp_code,
    };
  };

  const requestOtp = async (
    email: string,
    purpose: "login" | "register" | "verification" = "login"
  ): Promise<OTPDispatchResponse> => {
    return apiRequestOtp(email, purpose);
  };

  const verifyOtp = async (email: string, otp: string, rememberMe: boolean = false) => {
    const res = await apiVerifyOtp(email, otp, rememberMe);
    setUser(res.user);
  };

  const loginWithGoogle = async (credential: string) => {
    const res = await apiGoogleLogin(credential);
    setUser(res.user);
  };

  const loginAsGuest = async () => {
    const res = await apiGuestLogin();
    setUser(res.user);
  };

  const logout = async () => {
    await apiLogout();
    setUser(null);
  };

  const role = user?.role || null;
  const isAuthenticated = Boolean(user);
  const isGuest = role === "guest";

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isAuthenticated,
        isGuest,
        isLoading,
        login,
        register,
        requestOtp,
        verifyOtp,
        loginWithGoogle,
        loginAsGuest,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
