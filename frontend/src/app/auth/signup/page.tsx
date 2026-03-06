"use client";
import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { EyeIcon, EyeOffIcon } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";

export default function SignupPage() {
  const [form, setForm] = useState({ email: "", password: "", name: "", tenant_name: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      console.log("[SIGNUP] Attempting signup for:", form.email);
      const { data } = await api.post("/auth/signup", form);
      console.log("[SIGNUP] Signup API response received");
      login(data);
    } catch (err: any) {
      console.error("[SIGNUP] Signup failed:", err);
      setError(err.response?.data?.detail || "Signup failed");
    } finally {
      setLoading(false);
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
            <p className="mt-8 text-white/90 text-lg leading-relaxed">Join Taxodo today and automate your regulatory compliance securely and effortlessly.</p>
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
                <h2 className="text-2xl font-bold tracking-tight text-taxodo-ink font-manrope">Get Started</h2>
                <p className="mt-2 text-[15px] text-taxodo-muted">Create an account to automate your compliance.</p>
              </div>

              {error && <div className="mb-6 rounded-md bg-taxodo-danger/10 p-4 text-[14px] font-medium text-taxodo-danger border border-taxodo-danger/20">{error}</div>}

              <div className="space-y-5">
                <div>
                  <label className="block text-[14px] font-semibold text-taxodo-ink">Your Name</label>
                  <input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="taxodo-input mt-2 transition-shadow focus:ring-2 focus:ring-taxodo-primary/20"
                    placeholder="John Doe"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[14px] font-semibold text-taxodo-ink">Business Name</label>
                  <input
                    value={form.tenant_name}
                    onChange={(e) => setForm({ ...form, tenant_name: e.target.value })}
                    className="taxodo-input mt-2 transition-shadow focus:ring-2 focus:ring-taxodo-primary/20"
                    placeholder="e.g. Acme Solutions Pvt Ltd"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[14px] font-semibold text-taxodo-ink">Email Address</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="taxodo-input mt-2 transition-shadow focus:ring-2 focus:ring-taxodo-primary/20"
                    placeholder="you@company.com"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[14px] font-semibold text-taxodo-ink">Password</label>
                  <div className="relative mt-2">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={form.password}
                      onChange={(e) => setForm({ ...form, password: e.target.value })}
                      className="taxodo-input w-full pr-10 transition-shadow focus:ring-2 focus:ring-taxodo-primary/20"
                      placeholder="••••••••"
                      required
                      minLength={8}
                      pattern="^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$"
                      title="Password must contain at least 8 characters, one uppercase, one lowercase, one number, and one special character."
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-taxodo-muted hover:text-taxodo-ink focus:outline-none"
                    >
                      {showPassword ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
                    </button>
                  </div>
                  <p className="mt-2 text-[11px] leading-tight text-taxodo-muted">
                    Must be at least 8 characters and contain an uppercase letter, a lowercase letter, a number, and a special character.
                  </p>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="mt-8 w-full rounded-md bg-taxodo-primary px-4 py-3 text-[15px] font-semibold text-white shadow-sm transition-all hover:bg-taxodo-primary-hover hover:shadow-md disabled:pointer-events-none disabled:opacity-50"
              >
                {loading ? "Creating account..." : "Create Account"}
              </button>

              <p className="mt-6 text-center text-[15px] text-taxodo-muted">
                Already have an account?{" "}
                <Link href="/auth/login" className="font-semibold text-taxodo-primary hover:text-taxodo-primary-hover transition-colors">
                  Sign in
                </Link>
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
