"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatCurrency, formatDate, statusColor, cn } from "@/lib/utils";
import { Search, BookOpen } from "lucide-react";

export default function LedgerPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["ledger", search, statusFilter],
    queryFn: () =>
      api.get("/ledger/transactions", { params: { search: search || undefined, status: statusFilter || undefined, limit: 100 } }).then((r) => r.data),
  });

  const txns = data?.transactions || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Ledger</h1>
        <p className="mt-1 text-sm text-gray-500">Double-entry journal transactions</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search transactions..."
            className="w-full rounded-lg border pl-10 pr-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border px-3 py-2.5 text-sm text-gray-700"
        >
          <option value="">All Statuses</option>
          <option value="AUTO_POSTED">Auto Posted</option>
          <option value="NEEDS_REVIEW">Needs Review</option>
          <option value="CORRECTED">Corrected</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center text-sm text-gray-500">Loading...</div>
      ) : txns.length === 0 ? (
        <div className="rounded-xl border bg-white p-12 text-center">
          <BookOpen className="mx-auto mb-3 h-12 w-12 text-gray-300" />
          <p className="text-sm text-gray-500">No transactions yet. Approve invoices to generate ledger entries.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {txns.map((txn: any) => (
            <div key={txn.id} className="rounded-xl border bg-white p-5">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{txn.description || "Transaction"}</p>
                  <p className="mt-0.5 text-xs text-gray-500">
                    {formatDate(txn.transaction_date)} &middot; v{txn.version}
                    {txn.assigned_category && <span className="ml-2 rounded bg-gray-100 px-1.5 py-0.5 text-xs">{txn.assigned_category}</span>}
                  </p>
                </div>
                <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", statusColor(txn.status))}>{txn.status}</span>
              </div>

              {/* Journal Lines */}
              <table className="w-full text-sm">
                <thead className="border-b text-xs text-gray-500">
                  <tr>
                    <th className="py-1.5 text-left">Account</th>
                    <th className="py-1.5 text-right w-32">Debit (₹)</th>
                    <th className="py-1.5 text-right w-32">Credit (₹)</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {(txn.journal_lines || []).map((jl: any) => (
                    <tr key={jl.id}>
                      <td className="py-1.5 text-gray-700">{jl.account_name || jl.account_code || "—"}</td>
                      <td className="py-1.5 text-right font-mono">{jl.debit > 0 ? formatCurrency(jl.debit) : ""}</td>
                      <td className="py-1.5 text-right font-mono">{jl.credit > 0 ? formatCurrency(jl.credit) : ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
