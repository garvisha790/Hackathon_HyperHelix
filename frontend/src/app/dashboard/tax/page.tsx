"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Receipt, TrendingDown, TrendingUp } from "lucide-react";

export default function TaxPage() {
  const [fy, setFy] = useState("2025-26");
  const [periodType, setPeriodType] = useState("quarterly");

  const { data: gstData } = useQuery({
    queryKey: ["gst", fy, periodType],
    queryFn: () => api.get("/tax/gst/summary", { params: { period_type: periodType, year: parseInt(fy.split("-")[0]) } }).then((r) => r.data),
  });

  const { data: itData } = useQuery({
    queryKey: ["income-tax", fy],
    queryFn: () => api.get("/tax/income/estimate", { params: { fy } }).then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tax Intelligence</h1>
          <p className="mt-1 text-sm text-gray-500">GST liability & Income Tax estimate</p>
        </div>
        <div className="flex gap-2">
          <select value={fy} onChange={(e) => setFy(e.target.value)} className="rounded-lg border px-3 py-2 text-sm">
            <option value="2025-26">FY 2025-26</option>
            <option value="2024-25">FY 2024-25</option>
          </select>
          <select value={periodType} onChange={(e) => setPeriodType(e.target.value)} className="rounded-lg border px-3 py-2 text-sm">
            <option value="quarterly">Quarterly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
      </div>

      {/* GST Summary Table */}
      <div className="rounded-xl border bg-white p-6">
        <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-700">
          <Receipt className="h-4 w-4" /> GST Summary (GSTR-3B Aligned)
        </h2>
        {gstData?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50 text-xs text-gray-500">
                <tr>
                  <th className="px-3 py-2 text-left">Period</th>
                  <th className="px-3 py-2 text-right">Output CGST</th>
                  <th className="px-3 py-2 text-right">Output SGST</th>
                  <th className="px-3 py-2 text-right">Output IGST</th>
                  <th className="px-3 py-2 text-right">Input CGST</th>
                  <th className="px-3 py-2 text-right">Input SGST</th>
                  <th className="px-3 py-2 text-right">Input IGST</th>
                  <th className="px-3 py-2 text-right font-bold">Net Liability</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {gstData.map((row: any) => (
                  <tr key={row.id}>
                    <td className="px-3 py-2 font-medium">{row.period_start} to {row.period_end}</td>
                    <td className="px-3 py-2 text-right">{formatCurrency(row.output_cgst)}</td>
                    <td className="px-3 py-2 text-right">{formatCurrency(row.output_sgst)}</td>
                    <td className="px-3 py-2 text-right">{formatCurrency(row.output_igst)}</td>
                    <td className="px-3 py-2 text-right text-green-600">{formatCurrency(row.input_cgst)}</td>
                    <td className="px-3 py-2 text-right text-green-600">{formatCurrency(row.input_sgst)}</td>
                    <td className="px-3 py-2 text-right text-green-600">{formatCurrency(row.input_igst)}</td>
                    <td className="px-3 py-2 text-right font-bold">{formatCurrency(row.net_liability)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-400">No GST data available yet</p>
        )}
      </div>

      {/* Income Tax Estimate */}
      {itData && (
        <div className="rounded-xl border bg-white p-6">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-700">
            <TrendingUp className="h-4 w-4" /> Income Tax Estimate — FY {itData.fy} ({itData.tax_regime} regime)
          </h2>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <MetricCard label="Total Revenue" value={formatCurrency(itData.total_revenue)} color="green" />
            <MetricCard label="Total Expenses" value={formatCurrency(itData.total_expenses)} color="red" />
            <MetricCard label="Taxable Income" value={formatCurrency(itData.taxable_income)} color="blue" />
            <MetricCard label="Total Tax Liability" value={formatCurrency(itData.total_tax_liability)} color="amber" />
          </div>

          {itData.slab_breakup?.length > 0 && (
            <div className="mt-6">
              <h3 className="mb-3 text-xs font-semibold text-gray-500">SLAB BREAKUP</h3>
              <div className="space-y-2">
                {itData.slab_breakup.map((slab: any, i: number) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2 text-sm">
                    <span className="text-gray-600">{slab.range} @ {slab.rate}%</span>
                    <span className="font-mono font-medium">{formatCurrency(slab.tax)}</span>
                  </div>
                ))}
                <div className="flex items-center justify-between rounded-lg bg-amber-50 px-4 py-2 text-sm font-bold">
                  <span>+ 4% Health & Education Cess</span>
                  <span>{formatCurrency(itData.cess)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  const bg: Record<string, string> = { green: "bg-green-50", red: "bg-red-50", blue: "bg-blue-50", amber: "bg-amber-50" };
  return (
    <div className={`rounded-lg ${bg[color]} p-4`}>
      <p className="text-xs font-medium text-gray-500">{label}</p>
      <p className="mt-1 text-lg font-bold text-gray-900">{value}</p>
    </div>
  );
}
