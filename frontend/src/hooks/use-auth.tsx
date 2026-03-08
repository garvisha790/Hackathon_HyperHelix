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
  login: (data: { access_token: string; refresh_token?: string; user_id: string; tenant_id: string; role: string }) => Promise<void>;
  logout: () => void;
  verifySession: () => Promise<boolean>;
  refreshToken: () => Promise<boolean>;
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
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("userId");
    localStorage.removeItem("tenantId");
    localStorage.removeItem("role");
    setAuth({ token: null, userId: null, tenantId: null, role: null, isAuthenticated: false, userProfile: null });
    router.push("/auth/login");
  }, [router]);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    const storedRefreshToken = localStorage.getItem("refreshToken");
    if (!storedRefreshToken) {
      console.log("[AUTH] No refresh token available");
      return false;
    }

    try {
      console.log("[AUTH] Refreshing access token...");
      const { data } = await api.post("/auth/refresh", { refresh_token: storedRefreshToken });
      
      localStorage.setItem("token", data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("refreshToken", data.refresh_token);
      }
      
      setAuth((prev) => ({
        ...prev,
        token: data.access_token,
        isAuthenticated: true,
      }));
      
      console.log("[AUTH] Token refreshed successfully");
      return true;
    } catch (err: any) {
      console.error("[AUTH] Token refresh failed:", err.response?.data || err.message);
      logout();
      return false;
    }
  }, [logout]);

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
    console.log("[AUTH] Initial mount - checking stored token:", !!token);
    
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
      isAuthenticated: false, // Set to false initially, will verify below
    }));

    // Verify session with backend
    console.log("[AUTH] Verifying stored session on mount...");
    api.get("/auth/me")
      .then(({ data }) => {
        console.log("[AUTH] Session verified successfully:", data.email);
        setAuth((prev) => ({
          ...prev,
          isAuthenticated: true,
          userProfile: data,
        }));
      })
      .catch((err) => {
        console.error("[AUTH] Session verification failed on mount:", err.response?.data || err.message);
        // Clear auth state and redirect to login
        localStorage.removeItem("token");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("userId");
        localStorage.removeItem("tenantId");
        localStorage.removeItem("role");
        setAuth({ token: null, userId: null, tenantId: null, role: null, isAuthenticated: false, userProfile: null });
      });
  }, []); // Run only once on mount

  const login = useCallback(async (data: { access_token: string; refresh_token?: string; user_id: string; tenant_id: string; role: string }) => {
    console.log("[AUTH] Login successful, storing credentials...");
    localStorage.setItem("token", data.access_token);
    if (data.refresh_token) {
      localStorage.setItem("refreshToken", data.refresh_token);
    }
    localStorage.setItem("userId", data.user_id);
    localStorage.setItem("tenantId", data.tenant_id);
    localStorage.setItem("role", data.role);
    
    // Verify session immediately to ensure user profile is loaded
    try {
      console.log("[AUTH] Verifying session before navigation...");
      const { data: userProfile } = await api.get("/auth/me");
      console.log("[AUTH] Session verified:", userProfile.email);
      
      // Update auth state synchronously
      const newAuthState = {
        token: data.access_token,
        userId: data.user_id,
        tenantId: data.tenant_id,
        role: data.role,
        isAuthenticated: true,
        userProfile: userProfile,
      };
      
      setAuth(newAuthState);
      console.log("[AUTH] State updated, isAuthenticated:", true);
      
      // Small delay to ensure state propagates
      await new Promise(resolve => setTimeout(resolve, 100));
      
      console.log("[AUTH] Navigating to dashboard...");
      router.push("/dashboard/overview");
    } catch (err) {
      console.error("[AUTH] Session verification failed after login:", err);
      // Clear tokens if verification fails
      logout();
    }
  }, [router, logout]);

  return (
    <AuthContext.Provider value={{ ...auth, login, logout, verifySession, refreshToken }}>
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
