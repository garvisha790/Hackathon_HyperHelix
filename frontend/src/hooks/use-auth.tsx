"use client";
import React, { useState, useEffect, createContext, useContext, useCallback } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

interface AuthState {
  token: string | null;
  userId: string | null;
  tenantId: string | null;
  role: string | null;
  isAuthenticated: boolean;
  userProfile: any | null;
}

interface AuthContextType extends AuthState {
  login: (data: { access_token: string; user_id: string; tenant_id: string; role: string }) => void;
  logout: () => void;
  verifySession: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }): React.ReactNode {
  const router = useRouter();
  const [auth, setAuth] = useState<AuthState>({
    token: null,
    userId: null,
    tenantId: null,
    role: null,
    isAuthenticated: false,
    userProfile: null,
  });

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("userId");
    localStorage.removeItem("tenantId");
    localStorage.removeItem("role");
    setAuth({ token: null, userId: null, tenantId: null, role: null, isAuthenticated: false, userProfile: null });
    router.push("/auth/login");
  }, [router]);

  const verifySession = useCallback(async (): Promise<boolean> => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      logout();
      return false;
    }

    try {
      console.log("[AUTH] Verifying session with token...");
      const { data } = await api.get("/auth/me");
      console.log("[AUTH] Session verified successfully:", data.email);
      setAuth((prev) => ({
        ...prev,
        isAuthenticated: true,
        userProfile: data,
      }));
      return true;
    } catch (err: any) {
      console.error("[AUTH] Session verification failed:", err.response?.data || err.message);
      logout();
      return false;
    }
  }, [logout]);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setAuth({ token: null, userId: null, tenantId: null, role: null, isAuthenticated: false, userProfile: null });
      return;
    }
    const userId = localStorage.getItem("userId");
    const tenantId = localStorage.getItem("tenantId");
    const role = localStorage.getItem("role");
    setAuth((prev) => ({
      ...prev,
      token,
      userId,
      tenantId,
      role,
      isAuthenticated: !!token,
    }));
  }, []);

  const login = useCallback((data: { access_token: string; user_id: string; tenant_id: string; role: string }) => {
    console.log("[AUTH] Login successful, storing credentials and navigating...");
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("userId", data.user_id);
    localStorage.setItem("tenantId", data.tenant_id);
    localStorage.setItem("role", data.role);
    setAuth((prev) => ({
      ...prev,
      token: data.access_token,
      userId: data.user_id,
      tenantId: data.tenant_id,
      role: data.role,
      isAuthenticated: true,
    }));
    console.log("[AUTH] Navigating to dashboard...");
    router.push("/dashboard/overview");
  }, [router]);

  return (
    <AuthContext.Provider value={{ ...auth, login, logout, verifySession }
    }>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
