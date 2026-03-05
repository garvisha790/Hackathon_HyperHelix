"use client";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { BarChart3, FileText, Receipt, TrendingUp, AlertTriangle } from "lucide-react";
import { PnLChart } from "@/components/dashboard/pnl-chart";
import { ExpensePie } from "@/components/dashboard/expense-pie";
import { GSTTracker } from "@/components/dashboard/gst-tracker";
import { CashflowChart } from "@/components/dashboard/cashflow-chart";

export default function OverviewPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get("/dashboard/overview").then((r) => r.data),
  });

  if (isLoading) {
    return <div className="flex h-64 items-center justify-center text-gray-500">Loading dashboard...</div>;
  }

  const d = data || {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Financial overview for your business</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard icon={FileText} label="Total Documents" value={d.total_documents || 0} color="blue" />
        <KPICard icon={TrendingUp} label="Total Revenue" value={formatCurrency(d.total_revenue || 0)} color="green" />
        <KPICard icon={BarChart3} label="Total Expenses" value={formatCurrency(d.total_expenses || 0)} color="red" />
        <KPICard icon={Receipt} label="GST Liability" value={formatCurrency(d.gst_liability || 0)} color="amber" />
      </div>

      {/* Pipeline Status */}
      {d.pipeline && (
        <div className="rounded-xl border bg-white p-6">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">Document Pipeline</h2>
          <div className="grid grid-cols-4 gap-4">
            <PipelineStat label="Uploaded" count={d.pipeline.uploaded} color="bg-gray-200" />
            <PipelineStat label="Processing" count={d.pipeline.processing} color="bg-yellow-200" />
            <PipelineStat label="Completed" count={d.pipeline.done} color="bg-green-200" />
            <PipelineStat label="Failed" count={d.pipeline.failed} color="bg-red-200" />
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border bg-white p-6">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">Profit & Loss</h2>
          <PnLChart data={d.pnl || []} />
        </div>
        <div className="rounded-xl border bg-white p-6">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">Expenses by Category</h2>
          <ExpensePie data={d.expenses_by_category || []} />
        </div>
        <div className="rounded-xl border bg-white p-6">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">GST Tracker</h2>
          <GSTTracker data={d.gst_tracker || []} />
        </div>
        <div className="rounded-xl border bg-white p-6">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">Cash Flow</h2>
          <CashflowChart data={d.cashflow || []} />
        </div>
      </div>
    </div>
  );
}

function KPICard({ icon: Icon, label, value, color }: { icon: any; label: string; value: string | number; color: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    red: "bg-red-50 text-red-600",
    amber: "bg-amber-50 text-amber-600",
  };
  return (
    <div className="rounded-xl border bg-white p-5">
      <div className="flex items-center gap-3">
        <div className={`rounded-lg p-2 ${colors[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs font-medium text-gray-500">{label}</p>
          <p className="text-lg font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}

function PipelineStat({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <div className="text-center">
      <div className={`mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full ${color}`}>
        <span className="text-lg font-bold">{count}</span>
      </div>
      <p className="text-xs font-medium text-gray-600">{label}</p>
    </div>
  );
}
