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
    <div className="space-y-6 page-enter">
      <div className="section-intro">
        <div>
          <h1 className="text-2xl font-bold text-taxodo-ink">Tax Intelligence</h1>
          <p className="section-subtitle">GST liability & Income Tax estimate</p>
        </div>
        <div className="flex gap-3">
          <select value={fy} onChange={(e) => setFy(e.target.value)} className="taxodo-select">
            <option value="2025-26">FY 2025-26</option>
            <option value="2024-25">FY 2024-25</option>
          </select>
          <select value={periodType} onChange={(e) => setPeriodType(e.target.value)} className="taxodo-select">
            <option value="quarterly">Quarterly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
      </div>

      {/* GST Summary Table */}
      <div className="taxodo-card taxodo-card-pad">
        <h2 className="section-kicker mb-4 flex items-center gap-2">
          <Receipt className="h-4 w-4" /> GST Summary (GSTR-3B Aligned)
        </h2>
        {gstData?.length > 0 ? (
          <div className="table-wrap">
            <table className="table-base table-zebra">
              <thead className="table-head">
                <tr>
                  <th className="table-th text-left">Period</th>
                  <th className="table-th text-right">Output CGST</th>
                  <th className="table-th text-right">Output SGST</th>
                  <th className="table-th text-right">Output IGST</th>
                  <th className="table-th text-right">Input CGST</th>
                  <th className="table-th text-right">Input SGST</th>
                  <th className="table-th text-right">Input IGST</th>
                  <th className="table-th text-right font-bold text-taxodo-ink">Net Liab.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-taxodo-border">
                {gstData.map((row: any) => (
                  <tr key={row.id}>
                    <td className="table-td font-medium">{row.period_start} to {row.period_end}</td>
                    <td className="table-td numeric text-right">{formatCurrency(row.output_cgst)}</td>
                    <td className="table-td numeric text-right">{formatCurrency(row.output_sgst)}</td>
                    <td className="table-td numeric text-right">{formatCurrency(row.output_igst)}</td>
                    <td className="table-td numeric text-right font-semibold text-taxodo-success">{formatCurrency(row.input_cgst)}</td>
                    <td className="table-td numeric text-right font-semibold text-taxodo-success">{formatCurrency(row.input_sgst)}</td>
                    <td className="table-td numeric text-right font-semibold text-taxodo-success">{formatCurrency(row.input_igst)}</td>
                    <td className="table-td numeric text-right font-bold">{formatCurrency(row.net_liability)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-[15px] text-taxodo-muted">No GST data available yet</p>
        )}
      </div>

      {/* Income Tax Estimate */}
      {itData && (
        <div className="taxodo-card taxodo-card-pad">
          <h2 className="section-kicker mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" /> Income Tax Estimate — FY {itData.fy} ({itData.tax_regime} regime)
          </h2>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <MetricCard label="Total Revenue" value={formatCurrency(itData.total_revenue)} color="success" />
            <MetricCard label="Total Expenses" value={formatCurrency(itData.total_expenses)} color="danger" />
            <MetricCard label="Taxable Income" value={formatCurrency(itData.taxable_income)} color="primary" />
            <MetricCard label="Total Tax Liability" value={formatCurrency(itData.total_tax_liability)} color="warning" />
          </div>

          {itData.slab_breakup?.length > 0 && (
            <div className="mt-6">
              <h3 className="section-kicker mb-3">SLAB BREAKUP</h3>
              <div className="space-y-2">
                {itData.slab_breakup.map((slab: any, i: number) => (
                  <div key={i} className="flex items-center justify-between rounded-md bg-taxodo-subtle px-4 py-2.5 text-[15px]">
                    <span className="text-taxodo-muted">{slab.range} @ {slab.rate}%</span>
                    <span className="numeric font-bold text-taxodo-ink">{formatCurrency(slab.tax)}</span>
                  </div>
                ))}
                <div className="flex items-center justify-between rounded-md bg-taxodo-warning/20 px-4 py-2.5 text-[15px] font-bold text-taxodo-ink">
                  <span>+ 4% Health & Education Cess</span>
                  <span className="numeric">{formatCurrency(itData.cess)}</span>
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
  const styles: Record<string, string> = {
    success: "bg-taxodo-success/10 text-taxodo-success",
    danger: "bg-taxodo-danger/10 text-taxodo-danger",
    primary: "bg-taxodo-primary/10 text-taxodo-primary",
    warning: "bg-taxodo-warning/20 text-taxodo-warning"
  };
  return (
    <div className={`rounded-md ${styles[color]} p-4`}>
      <p className="text-[13px] font-semibold tracking-wide opacity-80">{label}</p>
      <p className="numeric mt-1 text-xl font-bold">{value}</p>
    </div>
  );
}
