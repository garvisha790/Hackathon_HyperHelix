"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface AuthState {
  token: string | null;
  userId: string | null;
  tenantId: string | null;
  role: string | null;
  isAuthenticated: boolean;
}

export function useAuth() {
  const router = useRouter();
  const [auth, setAuth] = useState<AuthState>({
    token: null,
    userId: null,
    tenantId: null,
    role: null,
    isAuthenticated: false,
  });

  useEffect(() => {
    const token = localStorage.getItem("token");
    const userId = localStorage.getItem("userId");
    const tenantId = localStorage.getItem("tenantId");
    const role = localStorage.getItem("role");
    setAuth({
      token,
      userId,
      tenantId,
      role,
      isAuthenticated: !!token,
    });
  }, []);

  const login = (data: { access_token: string; user_id: string; tenant_id: string; role: string }) => {
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("userId", data.user_id);
    localStorage.setItem("tenantId", data.tenant_id);
    localStorage.setItem("role", data.role);
    setAuth({
      token: data.access_token,
      userId: data.user_id,
      tenantId: data.tenant_id,
      role: data.role,
      isAuthenticated: true,
    });
    router.push("/dashboard/overview");
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userId");
    localStorage.removeItem("tenantId");
    localStorage.removeItem("role");
    setAuth({ token: null, userId: null, tenantId: null, role: null, isAuthenticated: false });
    router.push("/auth/login");
  };

  return { ...auth, login, logout };
}
