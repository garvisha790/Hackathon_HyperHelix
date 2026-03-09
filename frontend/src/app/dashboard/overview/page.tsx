"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import Link from "next/link";
import {
  BarChart3, FileText, Receipt, TrendingUp, TrendingDown,
  HelpCircle, IndianRupee, ArrowUpRight, ArrowDownRight,
  CheckCircle2, Clock, AlertCircle, Scale, Wallet,
  CreditCard, ExternalLink, Upload
} from "lucide-react";
import { PnLChart } from "@/components/dashboard/pnl-chart";
import { ExpensePie } from "@/components/dashboard/expense-pie";
import { GSTTracker } from "@/components/dashboard/gst-tracker";
import { CashflowChart } from "@/components/dashboard/cashflow-chart";

function Tooltip({ text, children }: { text: string; children: React.ReactNode }) {
  return (
    <div className="group relative inline-block">
      {children}
      <div className="invisible group-hover:visible absolute z-50 w-72 p-3 mt-2 -left-24 text-sm bg-gray-900 text-white rounded-lg shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
        <div className="relative">
          {text}
          <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-gray-900"></div>
        </div>
      </div>
    </div>
  );
}

export default function OverviewPage() {
  const [fy, setFy] = useState("2025-26");
  const fyYear = parseInt(fy.split("-")[0]);

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", fyYear],
    queryFn: () => api.get("/dashboard/overview", { params: { fy_year: fyYear } }).then((r) => r.data),
  });

  const { data: gstData } = useQuery({
    queryKey: ["gst-dash", fy],
    queryFn: () => api.get("/tax/gst/summary", { params: { period_type: "quarterly", year: fyYear } }).then((r) => r.data),
  });

  const { data: itData } = useQuery({
    queryKey: ["it-dash", fy],
    queryFn: () => api.get("/tax/income/estimate", { params: { fy } }).then((r) => r.data),
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-taxodo-primary border-t-transparent" />
          <span className="text-sm text-taxodo-muted">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  const d = data || {};
  const netProfit = d.net_profit ?? ((d.total_revenue || 0) - (d.total_expenses || 0));
  const receivables = d.total_receivables || 0;
  const payables = d.total_payables || 0;

  // Aggregate GST totals
  const totalOutputGST = (gstData || []).reduce((s: number, r: any) => s + (r.output_cgst || 0) + (r.output_sgst || 0) + (r.output_igst || 0), 0);
  const totalInputGST = (gstData || []).reduce((s: number, r: any) => s + (r.input_cgst || 0) + (r.input_sgst || 0) + (r.input_igst || 0), 0);
  const netGST = totalOutputGST - totalInputGST;

  return (
    <div className="space-y-6 page-enter">
      {/* ─── Header ─── */}
      <div className="section-intro">
        <div>
          <h1 className="text-2xl font-bold text-taxodo-ink">Dashboard</h1>
          <p className="mt-1 text-[15px] text-taxodo-muted">Financial overview &mdash; FY {fy}</p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/dashboard/documents" className="inline-flex items-center gap-2 rounded-md bg-taxodo-primary px-4 py-2 text-sm font-medium text-white hover:bg-taxodo-primary-hover transition-colors">
            <Upload className="h-4 w-4" /> Upload Invoice
          </Link>
          <select value={fy} onChange={(e) => setFy(e.target.value)} className="taxodo-select" aria-label="Financial Year">
            <option value="2025-26">FY 2025-26</option>
            <option value="2024-25">FY 2024-25</option>
          </select>
        </div>
      </div>

      {/* ─── Row 1: Financial KPIs ─── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard icon={TrendingUp} label="Total Revenue" value={formatCurrency(d.total_revenue || 0)}
          color="success" delta="Sales Invoices + BOS"
          tooltip="Total revenue from approved Sales Invoices and Bills of Supply this FY." />
        <KPICard icon={TrendingDown} label="Total Expenses" value={formatCurrency(d.total_expenses || 0)}
          color="danger" delta="Purchases + DN − CN"
          tooltip="Total expenses from Purchase Invoices and Debit Notes, minus Credit Note reversals." />
        <KPICard icon={Scale} label="Net Profit" value={formatCurrency(netProfit)}
          color={netProfit >= 0 ? "success" : "danger"} delta={netProfit >= 0 ? "Profitable" : "Loss"}
          tooltip="Net Profit = Total Revenue − Total Expenses. Base for Income Tax computation." />
        <KPICard icon={FileText} label="Documents" value={d.total_documents || 0}
          color="primary" delta={`${d.pipeline?.done || 0} approved`}
          tooltip="Total documents uploaded and processed in your account." />
      </div>

      {/* ─── Row 2: Receivables / Payables / GST / IT ─── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MiniCard icon={<Wallet className="h-5 w-5 text-blue-600" />}
          label="Receivables" value={formatCurrency(receivables)}
          bg="bg-blue-50" hint="Money owed to you" />
        <MiniCard icon={<CreditCard className="h-5 w-5 text-orange-600" />}
          label="Payables" value={formatCurrency(payables)}
          bg="bg-orange-50" hint="Money you owe vendors" />
        <MiniCard icon={<Receipt className="h-5 w-5 text-amber-600" />}
          label="GST Payable" value={formatCurrency(netGST)}
          bg="bg-amber-50" hint={`Out ₹${fmt(totalOutputGST)} − In ₹${fmt(totalInputGST)}`} />
        <MiniCard icon={<IndianRupee className="h-5 w-5 text-violet-600" />}
          label="Income Tax" value={formatCurrency(itData?.total_tax_liability || 0)}
          bg="bg-violet-50" hint={itData ? `${itData.tax_regime} regime` : "No data"} />
      </div>

      {/* ─── Row 3: GST & IT Snapshot side-by-side ─── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* GST Card */}
        <div className="taxodo-card taxodo-card-pad">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-[15px] font-bold text-taxodo-ink flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-amber-100"><Receipt className="h-4 w-4 text-amber-600" /></div>
              GST Summary
            </h2>
            <Link href="/dashboard/tax" className="text-xs font-semibold text-taxodo-secondary hover:underline flex items-center gap-1">Details <ExternalLink className="h-3 w-3" /></Link>
          </div>
          <div className="space-y-2.5">
            <SummaryRow label="Output GST (Sales)" amount={totalOutputGST} color="text-red-500" />
            <SummaryRow label="Input GST (Purchases)" amount={totalInputGST} color="text-green-600" />
            <div className="border-t border-taxodo-border mt-2 pt-3">
              <SummaryRow label="Net GST Payable" amount={netGST} color="text-taxodo-ink" bold />
            </div>
          </div>
          {/* Visual bar */}
          {totalOutputGST > 0 && (
            <div className="mt-4">
              <div className="flex gap-1 text-[11px] text-taxodo-muted mb-1">
                <span>Output</span><span className="ml-auto">Input</span>
              </div>
              <div className="flex h-3 w-full overflow-hidden rounded-full bg-gray-100">
                <div className="bg-red-400 rounded-l-full transition-all" style={{ width: `${(totalOutputGST / (totalOutputGST + totalInputGST) * 100)}%` }} />
                <div className="bg-green-400 rounded-r-full transition-all" style={{ width: `${(totalInputGST / (totalOutputGST + totalInputGST) * 100)}%` }} />
              </div>
            </div>
          )}
        </div>

        {/* IT Card */}
        <div className="taxodo-card taxodo-card-pad">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-[15px] font-bold text-taxodo-ink flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-violet-100"><IndianRupee className="h-4 w-4 text-violet-600" /></div>
              Income Tax Estimate
            </h2>
            <Link href="/dashboard/tax" className="text-xs font-semibold text-taxodo-secondary hover:underline flex items-center gap-1">Details <ExternalLink className="h-3 w-3" /></Link>
          </div>
          <div className="space-y-2.5">
            <SummaryRow label="Taxable Income" amount={itData?.taxable_income || 0} color="text-taxodo-primary" />
            <SummaryRow label="Tax on Income" amount={itData?.estimated_tax || 0} color="text-taxodo-muted" />
            <SummaryRow label="4% Health & Education Cess" amount={itData?.cess || 0} color="text-taxodo-muted" />
            <div className="border-t border-taxodo-border mt-2 pt-3">
              <SummaryRow label="Total Tax Payable" amount={itData?.total_tax_liability || 0} color="text-taxodo-ink" bold />
            </div>
          </div>
          {/* Slab mini breakdown */}
          {itData?.slab_breakup?.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {itData.slab_breakup.map((s: any, i: number) => (
                <span key={i} className="inline-flex items-center rounded-full bg-taxodo-subtle px-2.5 py-1 text-[11px] font-medium text-taxodo-muted">
                  {s.range} @ {s.rate}% → {formatCurrency(s.tax)}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ─── Row 4: Pipeline Status (compact) ─── */}
      {d.pipeline && (
        <div className="taxodo-card taxodo-card-pad">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[15px] font-bold text-taxodo-ink">Document Pipeline</h2>
            <Link href="/dashboard/documents" className="text-xs font-semibold text-taxodo-secondary hover:underline flex items-center gap-1">View All <ExternalLink className="h-3 w-3" /></Link>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <PipelineStat label="Uploaded" count={d.pipeline.uploaded} icon={<Clock className="h-4 w-4" />} color="text-gray-600" bg="bg-gray-100" />
            <PipelineStat label="Processing" count={d.pipeline.processing} icon={<AlertCircle className="h-4 w-4" />} color="text-amber-600" bg="bg-amber-50" />
            <PipelineStat label="Completed" count={d.pipeline.done} icon={<CheckCircle2 className="h-4 w-4" />} color="text-green-600" bg="bg-green-50" />
            <PipelineStat label="Failed" count={d.pipeline.failed} icon={<AlertCircle className="h-4 w-4" />} color="text-red-500" bg="bg-red-50" />
          </div>
          {/* Progress bar */}
          {d.pipeline.total > 0 && (
            <div className="mt-4 flex h-2 w-full overflow-hidden rounded-full bg-gray-100">
              {d.pipeline.done > 0 && <div className="bg-green-500 transition-all" style={{ width: `${(d.pipeline.done / d.pipeline.total * 100)}%` }} />}
              {d.pipeline.processing > 0 && <div className="bg-amber-400 transition-all" style={{ width: `${(d.pipeline.processing / d.pipeline.total * 100)}%` }} />}
              {d.pipeline.failed > 0 && <div className="bg-red-400 transition-all" style={{ width: `${(d.pipeline.failed / d.pipeline.total * 100)}%` }} />}
            </div>
          )}
        </div>
      )}

      {/* ─── Row 5: Charts ─── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="taxodo-card taxodo-card-pad">
          <h2 className="text-[15px] font-bold text-taxodo-ink mb-4">Revenue vs Expenses</h2>
          <PnLChart data={d.pnl || []} />
        </div>
        <div className="taxodo-card taxodo-card-pad">
          <h2 className="text-[15px] font-bold text-taxodo-ink mb-4">Expense Breakdown</h2>
          <ExpensePie data={d.expenses_by_category || []} />
        </div>
        <div className="taxodo-card taxodo-card-pad">
          <h2 className="text-[15px] font-bold text-taxodo-ink mb-4">GST Input vs Output</h2>
          <GSTTracker data={d.gst_tracker || []} />
        </div>
        <div className="taxodo-card taxodo-card-pad">
          <h2 className="text-[15px] font-bold text-taxodo-ink mb-4">Cash Flow</h2>
          <CashflowChart data={d.cashflow || []} />
        </div>
      </div>

      {/* ─── Row 6: Recent Invoices ─── */}
      {(d.recent_invoices?.length > 0) && (
        <div className="taxodo-card taxodo-card-pad">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[15px] font-bold text-taxodo-ink">Recent Invoices</h2>
            <Link href="/dashboard/documents" className="text-xs font-semibold text-taxodo-secondary hover:underline flex items-center gap-1">View All <ExternalLink className="h-3 w-3" /></Link>
          </div>
          <div className="table-wrap">
            <table className="table-base">
              <thead className="table-head">
                <tr>
                  <th className="table-th text-left">Invoice #</th>
                  <th className="table-th text-left">Party</th>
                  <th className="table-th text-left">Type</th>
                  <th className="table-th text-left">Date</th>
                  <th className="table-th text-right">Amount</th>
                  <th className="table-th text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-taxodo-border">
                {d.recent_invoices.map((inv: any) => (
                  <tr key={inv.id} className="hover:bg-taxodo-subtle/50 transition-colors">
                    <td className="table-td">
                      <Link href={`/dashboard/documents/${inv.document_id}`} className="font-medium text-taxodo-secondary hover:underline">
                        {inv.invoice_number}
                      </Link>
                    </td>
                    <td className="table-td text-taxodo-muted">{inv.transaction_nature === "sale" ? (inv.buyer_name || "—") : (inv.vendor_name || "—")}</td>
                    <td className="table-td"><DocTypeBadge type={inv.document_type} nature={inv.transaction_nature} /></td>
                    <td className="table-td text-taxodo-muted text-[13px]">{formatDate(inv.invoice_date)}</td>
                    <td className="table-td numeric text-right font-semibold">{formatCurrency(inv.total)}</td>
                    <td className="table-td text-center"><StatusDot status={inv.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─────────── Helper Components ─────────── */

function fmt(n: number) {
  if (n >= 100000) return `${(n / 100000).toFixed(1)}L`;
  if (n >= 1000) return `${(n / 1000).toFixed(0)}K`;
  return n.toFixed(0);
}

function KPICard({ icon: Icon, label, value, color, tooltip, delta }: {
  icon: any; label: string; value: string | number; color: string; tooltip?: string; delta?: string;
}) {
  const colors: Record<string, string> = {
    primary: "bg-taxodo-primary/10 text-taxodo-primary",
    success: "bg-green-50 text-green-600",
    danger: "bg-red-50 text-red-500",
    warning: "bg-amber-50 text-amber-600",
  };

  return (
    <div className="taxodo-card p-5 transition-all hover:shadow-modal hover:-translate-y-0.5">
      <div className="flex items-start gap-3">
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${colors[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <p className="text-[12px] font-semibold uppercase tracking-wider text-taxodo-muted truncate">{label}</p>
            {tooltip && (
              <Tooltip text={tooltip}>
                <HelpCircle className="h-3 w-3 shrink-0 text-gray-400 hover:text-taxodo-primary cursor-help transition-colors" />
              </Tooltip>
            )}
          </div>
          <p className="numeric text-xl font-bold text-taxodo-ink mt-0.5">{value}</p>
          {delta && <p className="text-[11px] text-taxodo-muted mt-0.5">{delta}</p>}
        </div>
      </div>
    </div>
  );
}

function MiniCard({ icon, label, value, bg, hint }: {
  icon: React.ReactNode; label: string; value: string; bg: string; hint: string;
}) {
  return (
    <div className={`rounded-lg ${bg} p-4 transition-all hover:shadow-sm`}>
      <div className="flex items-center gap-2 mb-1.5">
        {icon}
        <span className="text-[12px] font-semibold uppercase tracking-wider text-gray-500">{label}</span>
      </div>
      <p className="numeric text-lg font-bold text-taxodo-ink">{value}</p>
      <p className="text-[11px] text-gray-500 mt-0.5">{hint}</p>
    </div>
  );
}

function SummaryRow({ label, amount, color, bold }: {
  label: string; amount: number; color: string; bold?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between ${bold ? "text-[15px]" : "text-[14px]"}`}>
      <span className={bold ? "font-bold text-taxodo-ink" : "text-taxodo-muted"}>{label}</span>
      <span className={`numeric font-semibold ${bold ? "font-bold text-taxodo-ink" : color}`}>{formatCurrency(amount)}</span>
    </div>
  );
}

function PipelineStat({ label, count, icon, color, bg }: {
  label: string; count: number; icon: React.ReactNode; color: string; bg: string;
}) {
  return (
    <div className={`flex items-center gap-3 rounded-lg ${bg} p-3`}>
      <div className={`${color}`}>{icon}</div>
      <div>
        <p className={`text-lg font-bold ${color}`}>{count}</p>
        <p className="text-[11px] text-gray-500">{label}</p>
      </div>
    </div>
  );
}

function DocTypeBadge({ type, nature }: { type: string; nature?: string }) {
  const labels: Record<string, { text: string; cls: string }> = {
    "invoice-sale": { text: "Sales Invoice", cls: "bg-green-50 text-green-700" },
    "invoice-purchase": { text: "Purchase Invoice", cls: "bg-blue-50 text-blue-700" },
    "credit_note": { text: "Credit Note", cls: "bg-orange-50 text-orange-700" },
    "debit_note": { text: "Debit Note", cls: "bg-red-50 text-red-700" },
    "bill_of_supply": { text: "Bill of Supply", cls: "bg-gray-100 text-gray-700" },
    "receipt": { text: "Receipt", cls: "bg-gray-100 text-gray-600" },
  };
  const key = type === "invoice" ? `invoice-${nature || "purchase"}` : type;
  const cfg = labels[key] || { text: type, cls: "bg-gray-100 text-gray-600" };
  return <span className={`inline-block rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${cfg.cls}`}>{cfg.text}</span>;
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    APPROVED: "bg-green-500", VALID: "bg-green-500", PENDING: "bg-amber-400", INVALID: "bg-red-400", REJECTED: "bg-red-500",
  };
  return (
    <div className="flex items-center justify-center gap-1.5">
      <div className={`h-2 w-2 rounded-full ${colors[status] || "bg-gray-400"}`} />
      <span className="text-[11px] capitalize text-taxodo-muted">{status.toLowerCase()}</span>
    </div>
  );
}
