"use client";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatCurrency, formatDate, statusColor, validationColor, cn } from "@/lib/utils";
import { ArrowLeft, CheckCircle, XCircle } from "lucide-react";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const docId = params.id as string;

  const { data: doc } = useQuery({
    queryKey: ["document", docId],
    queryFn: () => api.get(`/documents/${docId}`).then((r) => r.data),
  });

  const { data: invoice } = useQuery({
    queryKey: ["invoice", docId],
    queryFn: () => api.get(`/invoices/${docId}`).then((r) => r.data),
    enabled: doc?.status === "DONE" || doc?.status === "VALIDATED",
    retry: false,
  });

  const { data: validation } = useQuery({
    queryKey: ["validation", docId],
    queryFn: () => api.get(`/invoices/${docId}/validation`).then((r) => r.data),
    enabled: !!invoice,
    retry: false,
  });

  const approveMutation = useMutation({
    mutationFn: () => api.post(`/invoices/${docId}/approve`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["invoice", docId] }); queryClient.invalidateQueries({ queryKey: ["documents"] }); },
  });

  const rejectMutation = useMutation({
    mutationFn: () => api.post(`/invoices/${docId}/reject`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["invoice", docId] }); },
  });

  return (
    <div className="space-y-6">
      <button onClick={() => router.back()} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Documents
      </button>

      {doc && (
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{doc.file_name}</h1>
            <p className="text-sm text-gray-500">Uploaded {formatDate(doc.created_at)}</p>
          </div>
          <span className={cn("rounded-full px-3 py-1 text-sm font-medium", statusColor(doc.status))}>{doc.status}</span>
        </div>
      )}

      {invoice && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Extracted Invoice Fields */}
          <div className="rounded-xl border bg-white p-6">
            <h2 className="mb-4 text-sm font-semibold text-gray-700">Extracted Invoice</h2>
            <div className="space-y-3">
              <Field label="Invoice Number" value={invoice.invoice_number} validation={validation?.field_results?.invoice_number} />
              <Field label="Invoice Date" value={formatDate(invoice.invoice_date)} validation={validation?.field_results?.invoice_date} />
              <Field label="Vendor" value={invoice.vendor_name} />
              <Field label="Vendor GSTIN" value={invoice.vendor_gstin} validation={validation?.field_results?.vendor_gstin} />
              <Field label="Buyer GSTIN" value={invoice.buyer_gstin} validation={validation?.field_results?.buyer_gstin} />
              <Field label="Place of Supply" value={invoice.place_of_supply} />
              <div className="border-t pt-3 mt-3">
                <Field label="Subtotal" value={formatCurrency(invoice.subtotal)} />
                <Field label="CGST" value={formatCurrency(invoice.cgst)} />
                <Field label="SGST" value={formatCurrency(invoice.sgst)} />
                <Field label="IGST" value={formatCurrency(invoice.igst)} />
                <Field label="Total" value={formatCurrency(invoice.total)} validation={validation?.field_results?.total} highlight />
              </div>
              {validation?.field_results?.gst_split && (
                <Field label="GST Split" value={validation.field_results.gst_split.status === "pass" ? "Valid" : validation.field_results.gst_split.message} validation={validation.field_results.gst_split} />
              )}
            </div>
          </div>

          {/* Validation Summary + Actions */}
          <div className="space-y-6">
            {validation && (
              <div className="rounded-xl border bg-white p-6">
                <h2 className="mb-4 text-sm font-semibold text-gray-700">Validation Results</h2>
                <div className={cn("mb-4 rounded-lg p-3 text-sm font-medium", {
                  "bg-green-50 text-green-700": validation.overall_status === "pass",
                  "bg-red-50 text-red-700": validation.overall_status === "fail",
                  "bg-amber-50 text-amber-700": validation.overall_status === "warn",
                })}>
                  {validation.overall_status === "pass" ? "All validations passed" :
                   validation.overall_status === "fail" ? `${validation.errors_count} error(s) found` :
                   `${validation.warnings_count} warning(s) found`}
                </div>

                {Object.entries(validation.field_results || {}).map(([key, val]: [string, any]) => (
                  <div key={key} className={cn("mb-2 rounded-lg border-l-4 p-3", validationColor(val.status))}>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase text-gray-600">{key.replace(/_/g, " ")}</span>
                      <span className={cn("text-xs font-bold", {
                        "text-green-600": val.status === "pass",
                        "text-red-600": val.status === "fail",
                        "text-amber-600": val.status === "warn",
                      })}>{val.status.toUpperCase()}</span>
                    </div>
                    {val.message && <p className="mt-1 text-xs text-gray-600">{val.message}</p>}
                  </div>
                ))}
              </div>
            )}

            {invoice.validation_status === "PENDING" || invoice.validation_status === "VALID" ? (
              <div className="flex gap-3">
                <button
                  onClick={() => approveMutation.mutate()}
                  disabled={approveMutation.isPending || invoice.is_duplicate}
                  className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-3 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50"
                >
                  <CheckCircle className="h-4 w-4" /> Approve & Post to Ledger
                </button>
                <button
                  onClick={() => rejectMutation.mutate()}
                  disabled={rejectMutation.isPending}
                  className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-red-300 px-4 py-3 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50"
                >
                  <XCircle className="h-4 w-4" /> Reject
                </button>
              </div>
            ) : (
              <div className={cn("rounded-lg p-4 text-center text-sm font-medium", statusColor(invoice.validation_status))}>
                Invoice {invoice.validation_status}
              </div>
            )}

            {invoice.is_duplicate && (
              <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 text-sm text-amber-700">
                This invoice has been flagged as a potential duplicate.
              </div>
            )}

            {/* Line Items */}
            {invoice.line_items?.length > 0 && (
              <div className="rounded-xl border bg-white p-6">
                <h2 className="mb-3 text-sm font-semibold text-gray-700">Line Items</h2>
                <table className="w-full text-sm">
                  <thead className="border-b text-xs text-gray-500">
                    <tr>
                      <th className="py-2 text-left">Description</th>
                      <th className="py-2 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {invoice.line_items.map((item: any, i: number) => (
                      <tr key={i}>
                        <td className="py-2">{item.description || "—"}</td>
                        <td className="py-2 text-right">{formatCurrency(item.taxable_value || item.rate || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {!invoice && doc?.status !== "DONE" && doc?.status !== "FAILED" && (
        <div className="rounded-xl border bg-white p-12 text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
          <p className="text-sm text-gray-500">Processing document... This may take up to 30 seconds.</p>
        </div>
      )}
    </div>
  );
}

function Field({ label, value, validation, highlight }: { label: string; value: string | null | undefined; validation?: any; highlight?: boolean }) {
  return (
    <div className={cn("flex items-start justify-between rounded-lg px-3 py-2", validation ? `border-l-4 ${validationColor(validation.status)}` : "")}>
      <span className="text-xs text-gray-500">{label}</span>
      <span className={cn("text-sm text-right", highlight ? "font-bold text-gray-900" : "text-gray-700")}>{value || "—"}</span>
    </div>
  );
}
