"use client";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { BarChart3, FileText, Receipt, TrendingUp, AlertTriangle, HelpCircle } from "lucide-react";
import { PnLChart } from "@/components/dashboard/pnl-chart";
import { ExpensePie } from "@/components/dashboard/expense-pie";
import { GSTTracker } from "@/components/dashboard/gst-tracker";
import { CashflowChart } from "@/components/dashboard/cashflow-chart";

// Tooltip Component
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
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get("/dashboard/overview").then((r) => r.data),
  });

  if (isLoading) {
    return <div className="flex h-64 items-center justify-center text-taxodo-muted">Loading dashboard...</div>;
  }

  const d = data || {};

  return (
    <div className="space-y-6 page-enter">
      <div className="section-intro">
        <div>
          <h1 className="text-2xl font-bold text-taxodo-ink">Dashboard</h1>
          <p className="mt-1 text-[15px] text-taxodo-muted">Financial overview for your business</p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard 
          icon={FileText} 
          label="Total Documents" 
          value={d.total_documents || 0} 
          color="primary"
          tooltip="Total number of invoices and documents uploaded and processed in your account. This includes approved, pending, and rejected documents."
        />
        <KPICard 
          icon={TrendingUp} 
          label="Total Revenue" 
          value={formatCurrency(d.total_revenue || 0)} 
          color="success"
          tooltip="Total revenue from all approved sales invoices. This represents the money your business has earned from customers this financial year."
        />
        <KPICard 
          icon={BarChart3} 
          label="Total Expenses" 
          value={formatCurrency(d.total_expenses || 0)} 
          color="danger"
          tooltip="Total expenses from all approved purchase invoices. This includes costs of goods, services, and operational expenses your business has incurred."
        />
        <KPICard 
          icon={Receipt} 
          label="GST Liability" 
          value={formatCurrency(d.gst_liability || 0)} 
          color="warning"
          tooltip={`Net GST you owe to the government this month. Calculated as: Output GST (collected from customers) minus Input GST (paid to vendors). ${d.gst_liability > 0 ? 'Due by 20th of next month.' : 'No liability this month.'}`}
        />
      </div>

      {/* Pipeline Status */}
      {d.pipeline && (
        <div className="taxodo-card taxodo-card-pad">
          <h2 className="section-kicker mb-4">Document Pipeline</h2>
          <div className="grid grid-cols-4 gap-4">
            <PipelineStat label="Uploaded" count={d.pipeline.uploaded} bg="bg-taxodo-subtle" text="text-taxodo-ink" />
            <PipelineStat label="Processing" count={d.pipeline.processing} bg="bg-taxodo-cta/20" text="text-taxodo-cta" />
            <PipelineStat label="Completed" count={d.pipeline.done} bg="bg-taxodo-success/20" text="text-taxodo-success" />
            <PipelineStat label="Failed" count={d.pipeline.failed} bg="bg-taxodo-danger/10" text="text-taxodo-danger" />
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="taxodo-card taxodo-card-pad">
          <h2 className="section-kicker mb-4">Profit & Loss</h2>
          <PnLChart data={d.pnl || []} />
        </div>
        <div className="taxodo-card taxodo-card-pad">
          <h2 className="section-kicker mb-4">Expenses by Category</h2>
          <ExpensePie data={d.expenses_by_category || []} />
        </div>
        <div className="taxodo-card taxodo-card-pad">
          <h2 className="section-kicker mb-4">GST Tracker</h2>
          <GSTTracker data={d.gst_tracker || []} />
        </div>
        <div className="taxodo-card taxodo-card-pad">
          <h2 className="section-kicker mb-4">Cash Flow</h2>
          <CashflowChart data={d.cashflow || []} />
        </div>
      </div>
    </div>
  );
}

function KPICard({ icon: Icon, label, value, color, tooltip }: { icon: any; label: string; value: string | number; color: string; tooltip?: string }) {
  const colors: Record<string, string> = {
    primary: "bg-taxodo-primary/10 text-taxodo-primary",
    success: "bg-taxodo-success/10 text-taxodo-success",
    danger: "bg-taxodo-danger/10 text-taxodo-danger",
    warning: "bg-taxodo-warning/20 text-taxodo-warning",
  };

  return (
    <div className="taxodo-card p-5 transition-shadow hover:shadow-modal">
      <div className="flex items-center gap-4">
        <div className={`flex h-12 w-12 items-center justify-center rounded-md ${colors[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-1.5">
            <p className="text-[13px] font-semibold tracking-wide text-taxodo-muted">{label}</p>
            {tooltip && (
              <Tooltip text={tooltip}>
                <HelpCircle className="h-3.5 w-3.5 text-gray-400 hover:text-taxodo-primary cursor-help transition-colors" />
              </Tooltip>
            )}
          </div>
          <p className="numeric text-2xl font-bold text-taxodo-ink">{value}</p>
        </div>
      </div>
    </div>
  );
}

function PipelineStat({ label, count, bg, text }: { label: string; count: number; bg: string; text: string }) {
  return (
    <div className="text-center">
      <div className={`mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full ${bg}`}>
        <span className={`text-xl font-bold ${text}`}>{count}</span>
      </div>
      <p className="text-[13px] font-semibold text-taxodo-muted">{label}</p>
    </div>
  );
}
