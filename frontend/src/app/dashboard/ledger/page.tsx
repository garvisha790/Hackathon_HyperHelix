"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatCurrency, formatDate, statusColor, cn } from "@/lib/utils";
import { Search, BookOpen, Trash2, Download } from "lucide-react";

export default function LedgerPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [downloading, setDownloading] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["ledger", search, statusFilter],
    queryFn: () =>
      api.get("/ledger/transactions", { params: { search: search || undefined, status: statusFilter || undefined, limit: 100 } }).then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (txnId: string) => api.delete(`/ledger/transactions/${txnId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ledger"] });
    },
  });

  const handleDelete = async (txnId: string, description: string) => {
    if (confirm(`Delete transaction "${description}"?\n\nThis action cannot be undone.`)) {
      await deleteMutation.mutateAsync(txnId);
    }
  };

  const txns = data?.transactions || [];

  const handleDownloadPdf = async () => {
    setDownloading(true);
    try {
      const resp = await api.get("/ledger/export/pdf", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([resp.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `Ledger_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error("PDF download failed", e);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6 page-enter">
      <div className="section-intro">
        <div>
          <h1 className="text-2xl font-bold text-taxodo-ink">Ledger</h1>
          <p className="section-subtitle">Double-entry journal transactions</p>
        </div>
        <button
          onClick={handleDownloadPdf}
          disabled={downloading || txns.length === 0}
          className="flex items-center gap-2 rounded-lg bg-taxodo-primary px-4 py-2.5 text-[14px] font-semibold text-white shadow-sm hover:bg-taxodo-primary/90 transition-colors disabled:opacity-50"
        >
          <Download className="h-4 w-4" />
          {downloading ? "Generating..." : "Export PDF"}
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-3 h-4 w-4 text-taxodo-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search transactions..."
            className="taxodo-input pl-10"
          />
        </div>
        <select
          id="status-filter"
          aria-label="Filter transactions by status"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="taxodo-select"
        >
          <option value="">All Statuses</option>
          <option value="AUTO_POSTED">Auto Posted</option>
          <option value="NEEDS_REVIEW">Needs Review</option>
          <option value="CORRECTED">Corrected</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center text-[15px] text-taxodo-muted">Loading...</div>
      ) : txns.length === 0 ? (
        <div className="taxodo-card p-12 text-center">
          <BookOpen className="mx-auto mb-3 h-12 w-12 text-taxodo-muted opacity-30" />
          <p className="text-[15px] text-taxodo-muted">No transactions yet. Approve invoices to generate ledger entries.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {txns.map((txn: any) => {
            const isEmpty = !txn.journal_lines || txn.journal_lines.length === 0;
            return (
              <div key={txn.id} className={cn("taxodo-card p-5", isEmpty && "border-l-4 border-l-red-400")}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <p className="text-[15px] font-semibold text-taxodo-ink">{txn.description || "Transaction"}</p>
                    <p className="mt-1 text-[13px] text-taxodo-muted">
                      {formatDate(txn.transaction_date)} &middot; v{txn.version}
                      {txn.assigned_category && <span className="ml-2 rounded-sm bg-taxodo-subtle px-1.5 py-0.5 text-[12px]">{txn.assigned_category}</span>}
                      {isEmpty && <span className="ml-2 rounded-sm bg-red-100 px-1.5 py-0.5 text-[12px] text-red-700 font-semibold">Empty Transaction</span>}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={cn("inline-block rounded-sm px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide", statusColor(txn.status))}>{txn.status}</span>
                    <button
                      onClick={() => handleDelete(txn.id, txn.description)}
                      disabled={deleteMutation.isPending}
                      className="p-2 hover:bg-red-50 rounded-md text-taxodo-muted hover:text-red-600 transition-colors disabled:opacity-50"
                      title={isEmpty ? "Delete empty transaction" : "Delete transaction"}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Journal Lines */}
                <div className="table-wrap">
                <table className="table-base table-zebra">
                  <thead className="table-head">
                    <tr>
                      <th className="table-th text-left">Account</th>
                      <th className="table-th text-right w-32">Debit (₹)</th>
                      <th className="table-th text-right w-32">Credit (₹)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-taxodo-border">
                    {isEmpty ? (
                      <tr>
                        <td colSpan={3} className="table-td text-center text-taxodo-muted italic py-6">
                          No journal lines — this transaction is incomplete
                        </td>
                      </tr>
                    ) : (
                      (txn.journal_lines || []).map((jl: any) => (
                        <tr key={jl.id}>
                          <td className="table-td text-taxodo-ink">{jl.account_name || jl.account_code || "—"}</td>
                          <td className="table-td numeric text-right font-medium">{jl.debit > 0 ? formatCurrency(jl.debit) : ""}</td>
                          <td className="table-td numeric text-right font-medium">{jl.credit > 0 ? formatCurrency(jl.credit) : ""}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          );
          })}
        </div>
      )}
    </div>
  );
}
