"use client";
import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { EyeIcon, EyeOffIcon } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      console.log("[LOGIN] Attempting login for:", email);
      const { data } = await api.post("/auth/login", { email, password });
      console.log("[LOGIN] Login API response received");
      login(data);
      // Keep loading state true during navigation
    } catch (err: any) {
      console.error("[LOGIN] Login failed:", err);
      setError(err.response?.data?.detail || "Login failed");
      setLoading(false); // Only reset loading on error
    }
  };

  return (
    <div className="flex min-h-screen bg-taxodo-page overflow-hidden font-sans">
      {/* Left Slanted Background */}
      <div
        className="absolute inset-y-0 left-0 z-0 hidden w-[55%] bg-taxodo-secondary lg:block"
        style={{ clipPath: "polygon(0 0, 100% 0, 85% 100%, 0 100%)" }}
      />

      <div className="relative z-10 flex w-full">
        {/* Left Branding Content - Hidden on Mobile */}
        <div className="hidden w-[55%] flex-col justify-between p-12 lg:flex xl:p-20 text-white">
          <div className="mb-auto">
            <Image
              src="/icons/taxodo_logo_white.svg"
              alt="Taxodo"
              width={200}
              height={48}
              className="h-12 w-auto drop-shadow-sm"
            />
          </div>
          <div className="my-auto max-w-[480px] pl-4">
            <h1 className="text-5xl font-bold font-manrope leading-[1.15] tracking-tight text-white">Auditor-grade Tax Intelligence for your business.</h1>
            <p className="mt-8 text-white/90 text-lg leading-relaxed">Automate your compliance, streamline your ledger, and get actionable tax insights in real-time.</p>
          </div>
          <div className="mt-auto pt-10">
            <p className="text-sm text-white/60">&copy; {new Date().getFullYear()} Taxodo AI. All rights reserved.</p>
          </div>
        </div>

        {/* Right Form Content */}
        <div className="flex flex-1 flex-col items-center justify-center p-6 sm:p-12 lg:w-[45%]">
          <div className="w-full max-w-[440px] animate-in fade-in zoom-in-95 duration-500">
            {/* Show logo on mobile only */}
            <div className="mb-10 lg:hidden flex justify-center">
              <Image src="/icons/taxodo_logo_clean.svg" alt="Taxodo" width={200} height={48} className="h-12 w-auto drop-shadow-sm" />
            </div>

            <form onSubmit={handleSubmit} className="taxodo-card p-8 sm:p-12 shadow-modal w-full bg-white border border-taxodo-border/50 rounded-2xl">
              <div className="mb-8 text-center lg:text-left">
                <h2 className="text-2xl font-bold tracking-tight text-taxodo-ink font-manrope">Sign in</h2>
                <p className="mt-2 text-[15px] text-taxodo-muted">Welcome back! Please enter your details.</p>
              </div>

              {error && (
                <div className="mb-6 rounded-md bg-taxodo-danger/10 p-4 text-[14px] font-medium text-taxodo-danger border border-taxodo-danger/20">
                  {error}
                </div>
              )}

              <div className="space-y-5">
                <div>
                  <label className="block text-[14px] font-semibold text-taxodo-ink">Email Address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="taxodo-input mt-2 transition-shadow focus:ring-2 focus:ring-taxodo-primary/20"
                    placeholder="you@company.com"
                    required
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between">
                    <label className="block text-[14px] font-semibold text-taxodo-ink">Password</label>
                    <a href="#" className="text-[13px] font-medium text-taxodo-primary hover:text-taxodo-primary-hover hover:underline outline-none">Forgot password?</a>
                  </div>
                  <div className="relative mt-2">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="taxodo-input w-full pr-10 transition-shadow focus:ring-2 focus:ring-taxodo-primary/20"
                      placeholder="••••••••"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-taxodo-muted hover:text-taxodo-ink focus:outline-none"
                    >
                      {showPassword ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="mt-8 w-full rounded-md bg-taxodo-primary px-4 py-3 text-[15px] font-semibold text-white shadow-sm transition-all hover:bg-taxodo-primary-hover hover:shadow-md disabled:pointer-events-none disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading && (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                )}
                {loading ? "Signing in..." : "Sign in to Dashboard"}
              </button>

              <p className="mt-6 text-center text-[15px] text-taxodo-muted">
                Don&apos;t have an account?{" "}
                <Link href="/auth/signup" className="font-semibold text-taxodo-primary hover:text-taxodo-primary-hover transition-colors">
                  Sign up
                </Link>
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
