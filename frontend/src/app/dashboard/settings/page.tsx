"use client";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Settings, Save, CheckCircle } from "lucide-react";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ name: "", gstin: "", state_code: "", business_type: "", return_frequency: "", tax_regime: "" });
  const [saved, setSaved] = useState(false);

  const { data: tenant } = useQuery({
    queryKey: ["tenant"],
    queryFn: () => api.get("/tenants/me").then((r) => r.data),
  });

  useEffect(() => {
    if (tenant) {
      setForm({
        name: tenant.name || "",
        gstin: tenant.gstin || "",
        state_code: tenant.state_code || "",
        business_type: tenant.business_type || "",
        return_frequency: tenant.return_frequency || "quarterly",
        tax_regime: tenant.tax_regime || "new",
      });
    }
  }, [tenant]);

  const updateMutation = useMutation({
    mutationFn: (data: any) => api.put("/tenants/me", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenant"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Business Settings</h1>
        <p className="mt-1 text-sm text-gray-500">Configure your business profile for GST and tax computation</p>
      </div>

      <div className="max-w-2xl rounded-xl border bg-white p-6">
        <div className="space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">Business Name</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Acme Corporation"
              className="w-full rounded-lg border px-3.5 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">GSTIN</label>
            <input
              value={form.gstin}
              onChange={(e) => setForm({ ...form, gstin: e.target.value.toUpperCase() })}
              placeholder="e.g. 27AADCS0472N1Z2"
              maxLength={15}
              className="w-full rounded-lg border px-3.5 py-2.5 text-sm font-mono focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
            <p className="mt-1 text-xs text-gray-400">15 characters: 2-digit state code + PAN + entity + Z + check</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="business-type" className="mb-1.5 block text-sm font-medium text-gray-700">Business Type</label>
              <select
                id="business-type"
                value={form.business_type}
                onChange={(e) => setForm({ ...form, business_type: e.target.value })}
                className="w-full rounded-lg border px-3.5 py-2.5 text-sm"
              >
                <option value="">Select...</option>
                <option value="service">Service</option>
                <option value="retail">Retail</option>
                <option value="manufacturing">Manufacturing</option>
                <option value="trading">Trading</option>
                <option value="professional">Professional</option>
              </select>
            </div>
            <div>
              <label htmlFor="return-frequency" className="mb-1.5 block text-sm font-medium text-gray-700">GST Return Frequency</label>
              <select
                id="return-frequency"
                value={form.return_frequency}
                onChange={(e) => setForm({ ...form, return_frequency: e.target.value })}
                className="w-full rounded-lg border px-3.5 py-2.5 text-sm"
              >
                <option value="quarterly">Quarterly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">Income Tax Regime</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input type="radio" checked={form.tax_regime === "new"} onChange={() => setForm({ ...form, tax_regime: "new" })} className="text-brand-600" />
                <span className="text-sm">New Regime (FY 2025-26)</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" checked={form.tax_regime === "old"} onChange={() => setForm({ ...form, tax_regime: "old" })} className="text-brand-600" />
                <span className="text-sm">Old Regime</span>
              </label>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={() => updateMutation.mutate(form)}
              disabled={updateMutation.isPending}
              className="flex items-center gap-2 rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {updateMutation.isPending ? "Saving..." : "Save Settings"}
            </button>
            {saved && (
              <span className="flex items-center gap-1 text-sm text-green-600">
                <CheckCircle className="h-4 w-4" /> Saved
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
