"use client";
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Receipt, TrendingUp, IndianRupee, ArrowUpRight, ArrowDownRight, Scale } from "lucide-react";

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

  // Compute GST totals
  const gstTotals = useMemo(() => {
    if (!gstData?.length) return null;
    return gstData.reduce((acc: any, row: any) => ({
      output_cgst: acc.output_cgst + (row.output_cgst || 0),
      output_sgst: acc.output_sgst + (row.output_sgst || 0),
      output_igst: acc.output_igst + (row.output_igst || 0),
      input_cgst: acc.input_cgst + (row.input_cgst || 0),
      input_sgst: acc.input_sgst + (row.input_sgst || 0),
      input_igst: acc.input_igst + (row.input_igst || 0),
      net_liability: acc.net_liability + (row.net_liability || 0),
    }), { output_cgst: 0, output_sgst: 0, output_igst: 0, input_cgst: 0, input_sgst: 0, input_igst: 0, net_liability: 0 });
  }, [gstData]);

  const totalOutputGST = gstTotals ? gstTotals.output_cgst + gstTotals.output_sgst + gstTotals.output_igst : 0;
  const totalInputGST = gstTotals ? gstTotals.input_cgst + gstTotals.input_sgst + gstTotals.input_igst : 0;

  return (
    <div className="space-y-6 page-enter">
      <div className="section-intro">
        <div>
          <h1 className="text-2xl font-bold text-taxodo-ink">Tax Intelligence</h1>
          <p className="section-subtitle">GST liability & Income Tax estimate</p>
        </div>
        <div className="flex gap-3">
          <select value={fy} onChange={(e) => setFy(e.target.value)} className="taxodo-select" aria-label="Financial Year">
            <option value="2025-26">FY 2025-26</option>
            <option value="2024-25">FY 2024-25</option>
          </select>
          <select value={periodType} onChange={(e) => setPeriodType(e.target.value)} className="taxodo-select" aria-label="Period Type">
            <option value="quarterly">Quarterly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
      </div>

      {/* GST Quick Cards */}
      {gstTotals && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <QuickCard icon={<ArrowUpRight className="h-5 w-5" />} label="Output GST (Sales)" value={totalOutputGST} color="danger" />
          <QuickCard icon={<ArrowDownRight className="h-5 w-5" />} label="Input GST (Purchases)" value={totalInputGST} color="success" />
          <QuickCard icon={<Scale className="h-5 w-5" />} label="GST Payable" value={gstTotals.net_liability} color="warning" />
        </div>
      )}

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
                {/* Totals Row */}
                {gstTotals && (
                  <tr className="bg-taxodo-primary/5 font-bold">
                    <td className="table-td text-taxodo-ink">FY Total</td>
                    <td className="table-td numeric text-right text-taxodo-ink">{formatCurrency(gstTotals.output_cgst)}</td>
                    <td className="table-td numeric text-right text-taxodo-ink">{formatCurrency(gstTotals.output_sgst)}</td>
                    <td className="table-td numeric text-right text-taxodo-ink">{formatCurrency(gstTotals.output_igst)}</td>
                    <td className="table-td numeric text-right text-taxodo-success">{formatCurrency(gstTotals.input_cgst)}</td>
                    <td className="table-td numeric text-right text-taxodo-success">{formatCurrency(gstTotals.input_sgst)}</td>
                    <td className="table-td numeric text-right text-taxodo-success">{formatCurrency(gstTotals.input_igst)}</td>
                    <td className="table-td numeric text-right text-taxodo-ink text-base">{formatCurrency(gstTotals.net_liability)}</td>
                  </tr>
                )}
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
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <MetricCard label="Total Revenue" value={formatCurrency(itData.total_revenue)} color="success" />
            <MetricCard label="Total Expenses" value={formatCurrency(itData.total_expenses)} color="danger" />
            <MetricCard label="Net Profit" value={formatCurrency(itData.total_revenue - itData.total_expenses)} color={itData.total_revenue - itData.total_expenses >= 0 ? "success" : "danger"} />
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
                {itData.assumptions?.rebate > 0 && (
                  <div className="flex items-center justify-between rounded-md bg-green-50 border border-green-200 px-4 py-2.5 text-[15px] font-bold text-green-700">
                    <span>(-) Section 87A Rebate</span>
                    <span className="numeric">- {formatCurrency(itData.assumptions.rebate)}</span>
                  </div>
                )}
                {itData.assumptions?.note && (
                  <div className="rounded-md bg-blue-50 border border-blue-200 px-4 py-2 text-[13px] text-blue-700 italic">
                    {itData.assumptions.note}
                  </div>
                )}
                <div className="flex items-center justify-between rounded-md bg-taxodo-primary/10 px-4 py-3 text-[16px] font-bold text-taxodo-ink">
                  <span className="flex items-center gap-2"><IndianRupee className="h-4 w-4" /> Total Income Tax Payable</span>
                  <span className="numeric text-taxodo-primary">{formatCurrency(itData.total_tax_liability)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function QuickCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: string }) {
  const styles: Record<string, string> = {
    success: "bg-taxodo-success/10 text-taxodo-success border-taxodo-success/20",
    danger: "bg-taxodo-danger/10 text-taxodo-danger border-taxodo-danger/20",
    warning: "bg-taxodo-warning/15 text-taxodo-warning border-taxodo-warning/20",
  };
  return (
    <div className={`rounded-lg border p-4 ${styles[color]}`}>
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-[13px] font-semibold opacity-80">{label}</span>
      </div>
      <p className="numeric text-2xl font-bold">{formatCurrency(value)}</p>
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
