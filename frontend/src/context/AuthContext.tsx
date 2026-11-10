import React, { createContext, useContext, useState, useEffect } from "react";
import {
  AuthUser,
  getStoredAccessToken,
  setStoredAccessToken,
  apiLogin,
  apiRegister,
  apiGuestLogin,
  apiGoogleLogin,
  apiLogout,
  fetchCurrentUser,
  refreshAccessToken,
  UNAUTHORIZED_EVENT,
} from "../api/client";

interface AuthContextType {
  user: AuthUser | null;
  role: string | null;
  isAuthenticated: boolean;
  isGuest: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<{ requires_verification?: boolean }>;
  loginWithGoogle: (credential: string) => Promise<void>;
  loginAsGuest: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

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
          // Attempt silent refresh via cookie
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

  const login = async (email: string, password: string) => {
    const res = await apiLogin(email, password);
    setUser(res.user);
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const res = await apiRegister(email, password, fullName);
    setUser(res.user);
    return { requires_verification: res.requires_verification };
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
