"use client";
import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatCurrency, formatDate, statusColor, validationColor, cn } from "@/lib/utils";
import { ArrowLeft, ArrowRight, CheckCircle, XCircle, FileText, Zap, Trash2, RotateCcw, AlertTriangle, Edit2, Save, Wand2 } from "lucide-react";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const docId = params.id as string;

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<any>({});
  const [approveError, setApproveError] = useState<string | null>(null);
  const [aiReviewMode, setAiReviewMode] = useState(false);
  const [reviewSuggestions, setReviewSuggestions] = useState<any[]>([]);

  const { data: doc } = useQuery({
    queryKey: ["document", docId],
    queryFn: () => api.get(`/documents/${docId}`).then((r) => r.data),
  });

  const { data: invoice, refetch: refetchInvoice } = useQuery({
    queryKey: ["invoice", docId],
    queryFn: () => api.get(`/invoices/${docId}`).then((r) => r.data),
    enabled: doc?.status === "DONE" || doc?.status === "VALIDATED" || doc?.status === "APPROVED",
    retry: false,
    staleTime: 0,
    refetchOnMount: "always",
  });

  useEffect(() => {
    if (invoice && !isEditing) {
      setEditData({
        vendor_name: invoice.vendor_name || "",
        vendor_gstin: invoice.vendor_gstin || "",
        buyer_gstin: invoice.buyer_gstin || "",
        invoice_number: invoice.invoice_number || "",
        invoice_date: invoice.invoice_date || "",
        place_of_supply: invoice.place_of_supply || "",
        subtotal: invoice.subtotal || 0,
        cgst: invoice.cgst || 0,
        sgst: invoice.sgst || 0,
        igst: invoice.igst || 0,
        total: invoice.total || 0,
      });
    }
  }, [invoice, isEditing]);

  const { data: validation } = useQuery({
    queryKey: ["validation", docId],
    queryFn: () => api.get(`/invoices/${docId}/validation`).then((r) => r.data),
    enabled: !!invoice,
    retry: false,
  });

  const { data: preview } = useQuery({
    queryKey: ["preview", docId],
    queryFn: () => api.get(`/invoices/${docId}/download-url`).then((r) => r.data),
    enabled: !!doc,
    retry: false,
  });

  const { data: extraction } = useQuery({
    queryKey: ["extraction", docId],
    queryFn: () => api.get(`/invoices/${docId}/extraction`).then((r) => r.data),
    enabled: !!invoice,
    retry: false,
  });

  const approveMutation = useMutation({
    mutationFn: () => api.post(`/invoices/${docId}/approve`),
    onSuccess: () => {
      setApproveError(null);
      queryClient.invalidateQueries({ queryKey: ["invoice", docId] });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: any) => {
      setApproveError(err.response?.data?.detail || "Failed to approve invoice. Please check amounts.");
    }
  });

  const rejectMutation = useMutation({
    mutationFn: () => api.post(`/invoices/${docId}/reject`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["invoice", docId] }); },
  });

  const updateMutation = useMutation({
    mutationFn: (data: any) => api.patch(`/invoices/${docId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoice", docId] });
      queryClient.invalidateQueries({ queryKey: ["validation", docId] });
      setIsEditing(false);
      setAiReviewMode(false);
      setReviewSuggestions([]);
    },
  });

  const reviewMutation = useMutation({
    mutationFn: () => api.post(`/invoices/${docId}/generate-ai-review`).then((r) => r.data),
    onSuccess: (data) => {
      setReviewSuggestions(data.suggestions || []);
      setAiReviewMode(true);
      setIsEditing(true); // Switch to edit mode to allow form updates
    },
  });

  const acceptSuggestion = (suggestion: any) => {
    setEditData((prev: any) => ({ ...prev, [suggestion.field_name]: suggestion.suggested_value }));
    setReviewSuggestions((prev) => prev.filter(s => s.field_name !== suggestion.field_name));
  };

  const rejectSuggestion = (fieldName: string) => {
    setReviewSuggestions((prev) => prev.filter(s => s.field_name !== fieldName));
  };

  const acceptAllSuggestions = () => {
    const updates: any = {};
    reviewSuggestions.forEach(s => { updates[s.field_name] = s.suggested_value; });
    setEditData((prev: any) => ({ ...prev, ...updates }));
    setReviewSuggestions([]);
  };

  const rescanMutation = useMutation({
    mutationFn: () => api.post(`/documents/${docId}/process`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document", docId] });
      queryClient.invalidateQueries({ queryKey: ["invoice", docId] });
      queryClient.invalidateQueries({ queryKey: ["validation", docId] });
      queryClient.invalidateQueries({ queryKey: ["extraction", docId] });
      // Also trigger a document poll so we know when extraction completes
      const pollInterval = setInterval(async () => {
        const { data: freshDoc } = await api.get(`/documents/${docId}`);
        if (freshDoc.status === "DONE" || freshDoc.status === "VALIDATED") {
          clearInterval(pollInterval);
          queryClient.invalidateQueries({ queryKey: ["document", docId] });
          queryClient.invalidateQueries({ queryKey: ["invoice", docId] });
          queryClient.invalidateQueries({ queryKey: ["validation", docId] });
          queryClient.invalidateQueries({ queryKey: ["extraction", docId] });
        }
      }, 3000);
      // Cleanup after 2 minutes in case it never finishes
      setTimeout(() => clearInterval(pollInterval), 120000);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/documents/${docId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      router.push("/dashboard/documents");
    },
  });

  return (
    <div className="space-y-5 relative">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button onClick={() => router.back()} className="flex items-center gap-2 text-sm text-taxodo-muted hover:text-taxodo-ink">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
        {doc && (
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-taxodo-ink">{doc.file_name}</span>
            <span className={cn("rounded-sm px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide", statusColor(doc.status))}>
              {doc.status}
            </span>

            <div className="ml-4 flex items-center gap-2 border-l border-taxodo-border pl-4">
              <button
                onClick={() => rescanMutation.mutate()}
                disabled={rescanMutation.isPending || ["PROCESSING"].includes(doc.status)}
                className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[13px] font-semibold text-taxodo-ink transition-colors hover:bg-taxodo-subtle disabled:opacity-50"
                title="Reprocess Document"
              >
                <RotateCcw className={cn("h-4 w-4", rescanMutation.isPending && "animate-spin")} />
                Rescan
              </button>
              <button
                onClick={() => setShowDeleteModal(true)}
                className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[13px] font-semibold text-taxodo-danger transition-colors hover:bg-taxodo-danger/10"
                title="Delete Document"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main 2-panel layout for Users */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 lg:items-start">

        {/* ── Panel 1: Document View ────────────────────── */}
        <div className="flex flex-col gap-3 lg:sticky lg:top-6">
          <div className="overflow-hidden rounded-2xl border border-taxodo-border bg-taxodo-surface shadow-card">
            {preview?.download_url ? (
              preview.is_image ? (
                <img
                  src={preview.download_url}
                  alt={preview.file_name || "Document"}
                  className="w-full object-contain bg-gray-50/50"
                  style={{ maxHeight: "800px" }}
                />
              ) : (
                <iframe
                  src={preview.download_url}
                  className="h-[800px] w-full border-0 bg-gray-50/50"
                  title="Document"
                />
              )
            ) : (
              <div className="flex h-[400px] items-center justify-center text-taxodo-muted bg-gray-50/30">
                <div className="text-center">
                  <FileText className="mx-auto mb-3 h-10 w-10 opacity-20" />
                  <p className="text-sm font-medium">Loading document...</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Panel 2: Clean Data Sheet ──────────────────── */}
        <div className="flex flex-col gap-5">
          {invoice ? (
            <div className="overflow-hidden rounded-2xl border border-taxodo-border bg-white shadow-card">
              <div className="border-b border-taxodo-border bg-taxodo-surface/50 px-6 py-4 flex items-center justify-between">
                <h2 className="text-base font-bold text-taxodo-ink flex items-center gap-2">
                  <FileText className="h-4 w-4 text-taxodo-primary" /> Invoice Details
                </h2>
                <div className="flex items-center gap-3">
                  {validation?.overall_status === "fail" && !isEditing && !aiReviewMode && (
                    <button
                      onClick={() => reviewMutation.mutate()}
                      disabled={reviewMutation.isPending}
                      className="flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700 border border-indigo-200 hover:bg-indigo-100 transition-colors shadow-sm"
                    >
                      {reviewMutation.isPending ? "Analyzing..." : <><Wand2 className="h-3.5 w-3.5" /> AI Tax Review</>}
                    </button>
                  )}
                  {validation?.overall_status === "fail" && !isEditing && (
                    <span className="flex items-center gap-1.5 rounded-full bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-600 border border-red-100">
                      <AlertTriangle className="h-3.5 w-3.5" /> Needs Review
                    </span>
                  )}
                  {invoice.validation_status !== "APPROVED" && invoice.validation_status !== "REJECTED" && (
                    <button
                      onClick={() => setIsEditing(!isEditing)}
                      disabled={updateMutation.isPending}
                      className={cn("flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold transition-colors border",
                        isEditing ? "bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200" : "bg-taxodo-primary/10 text-taxodo-primary border-taxodo-primary/20 hover:bg-taxodo-primary/20"
                      )}
                    >
                      {isEditing ? "Cancel Edit" : <><Edit2 className="h-3.5 w-3.5" /> Edit Data</>}
                    </button>
                  )}
                </div>
              </div>

              <div className="p-6">
                {/* Vendor Info */}
                <div className="mb-8">
                  <p className="text-sm font-semibold uppercase tracking-wider text-taxodo-muted mb-3">Vendor Information</p>
                  <div className="rounded-xl border border-gray-100 bg-gray-50/50 p-4 space-y-3">
                    <EditableDataField
                      label="Vendor Name"
                      value={isEditing ? editData.vendor_name : invoice.vendor_name || "Unknown Vendor"}
                      isEditing={isEditing}
                      onChange={(v: string) => setEditData({ ...editData, vendor_name: v })}
                      className="font-bold text-lg text-taxodo-ink"
                      suggestionName="vendor_name"
                      reviewSuggestions={reviewSuggestions}
                      onAccept={acceptSuggestion}
                      onReject={rejectSuggestion}
                    />
                    <EditableDataField
                      label="GSTIN"
                      value={isEditing ? editData.vendor_gstin : invoice.vendor_gstin}
                      isEditing={isEditing}
                      onChange={(v: string) => setEditData({ ...editData, vendor_gstin: v })}
                      className="text-sm text-gray-900 font-semibold font-mono"
                      suggestionName="vendor_gstin"
                      reviewSuggestions={reviewSuggestions}
                      onAccept={acceptSuggestion}
                      onReject={rejectSuggestion}
                    />
                  </div>
                </div>

                {/* Key Details Grid */}
                <div className="mb-8 grid grid-cols-2 gap-x-6 gap-y-5">
                  <EditableDataField
                    label="Invoice Number"
                    value={isEditing ? editData.invoice_number : invoice.invoice_number}
                    isEditing={isEditing}
                    onChange={(v: string) => setEditData({ ...editData, invoice_number: v })}
                    suggestionName="invoice_number"
                    reviewSuggestions={reviewSuggestions}
                    onAccept={acceptSuggestion}
                    onReject={rejectSuggestion}
                  />
                  <EditableDataField
                    label="Invoice Date"
                    value={isEditing ? editData.invoice_date : formatDate(invoice.invoice_date)}
                    isEditing={isEditing}
                    onChange={(v: string) => setEditData({ ...editData, invoice_date: v })}
                    suggestionName="invoice_date"
                    reviewSuggestions={reviewSuggestions}
                    onAccept={acceptSuggestion}
                    onReject={rejectSuggestion}
                  />
                  <EditableDataField
                    label="Buyer GSTIN"
                    value={isEditing ? editData.buyer_gstin : invoice.buyer_gstin}
                    isEditing={isEditing}
                    onChange={(v: string) => setEditData({ ...editData, buyer_gstin: v })}
                    suggestionName="buyer_gstin"
                    reviewSuggestions={reviewSuggestions}
                    onAccept={acceptSuggestion}
                    onReject={rejectSuggestion}
                  />
                  <EditableDataField
                    label="Place of Supply"
                    value={isEditing ? editData.place_of_supply : invoice.place_of_supply}
                    isEditing={isEditing}
                    onChange={(v: string) => setEditData({ ...editData, place_of_supply: v })}
                    suggestionName="place_of_supply"
                    reviewSuggestions={reviewSuggestions}
                    onAccept={acceptSuggestion}
                    onReject={rejectSuggestion}
                  />
                </div>

                {/* Line Items */}
                {invoice.line_items && invoice.line_items.length > 0 && (
                  <div className="mb-8">
                    <p className="text-sm font-semibold uppercase tracking-wider text-taxodo-muted mb-3">Line Items</p>
                    <div className="rounded-xl border border-gray-100 overflow-hidden overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50/50 text-xs uppercase text-gray-500">
                          <tr>
                            <th className="px-4 py-3 font-semibold">Description</th>
                            <th className="px-4 py-3 font-semibold">HSN/SAC</th>
                            <th className="px-4 py-3 font-semibold text-right">Qty</th>
                            <th className="px-4 py-3 font-semibold text-right">Rate</th>
                            <th className="px-4 py-3 font-semibold text-right">Taxable</th>
                            <th className="px-4 py-3 font-semibold text-right text-gray-400">CGST</th>
                            <th className="px-4 py-3 font-semibold text-right text-gray-400">SGST</th>
                            <th className="px-4 py-3 font-semibold text-right text-gray-400">IGST</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 bg-white">
                          {invoice.line_items.map((item: any, idx: number) => (
                            <tr key={idx} className="hover:bg-gray-50/50 transition-colors">
                              <td className="px-4 py-3 font-medium text-gray-900 max-w-[200px] truncate" title={item.description}>{item.description || "—"}</td>
                              <td className="px-4 py-3 font-mono text-gray-500">{item.hsn_sac || "—"}</td>
                              <td className="px-4 py-3 text-right text-gray-900">{item.qty || "—"}</td>
                              <td className="px-4 py-3 text-right text-gray-900">{item.rate ? formatCurrency(item.rate) : "—"}</td>
                              <td className="px-4 py-3 text-right font-medium text-taxodo-ink">{item.taxable_value ? formatCurrency(item.taxable_value) : "—"}</td>

                              <td className="px-4 py-3 text-right text-gray-500 text-xs">
                                {item.cgst_amount ? (
                                  <div className="flex flex-col"><span className="text-taxodo-ink font-medium">{formatCurrency(item.cgst_amount)}</span><span>({item.cgst_rate}%)</span></div>
                                ) : "—"}
                              </td>
                              <td className="px-4 py-3 text-right text-gray-500 text-xs">
                                {item.sgst_amount ? (
                                  <div className="flex flex-col"><span className="text-taxodo-ink font-medium">{formatCurrency(item.sgst_amount)}</span><span>({item.sgst_rate}%)</span></div>
                                ) : "—"}
                              </td>
                              <td className="px-4 py-3 text-right text-gray-500 text-xs">
                                {item.igst_amount ? (
                                  <div className="flex flex-col"><span className="text-taxodo-ink font-medium">{formatCurrency(item.igst_amount)}</span><span>({item.igst_rate}%)</span></div>
                                ) : "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Amounts Breakdown */}
                <div className="mb-8">
                  <p className="text-sm font-semibold uppercase tracking-wider text-taxodo-muted mb-3">Amount & Taxes</p>
                  <div className="rounded-xl border border-gray-100 overflow-hidden">
                    <EditableCurrencyField
                      label="Subtotal"
                      value={isEditing ? editData.subtotal : invoice.subtotal}
                      isEditing={isEditing}
                      onChange={(v: number) => setEditData({ ...editData, subtotal: v })}
                      suggestionName="subtotal"
                      reviewSuggestions={reviewSuggestions}
                      onAccept={acceptSuggestion}
                      onReject={rejectSuggestion}
                    />
                    <EditableCurrencyField
                      label="CGST"
                      value={isEditing ? editData.cgst : invoice.cgst}
                      isEditing={isEditing}
                      onChange={(v: number) => setEditData({ ...editData, cgst: v })}
                      hideIfZero
                      suggestionName="cgst"
                      reviewSuggestions={reviewSuggestions}
                      onAccept={acceptSuggestion}
                      onReject={rejectSuggestion}
                    />
                    <EditableCurrencyField
                      label="SGST"
                      value={isEditing ? editData.sgst : invoice.sgst}
                      isEditing={isEditing}
                      onChange={(v: number) => setEditData({ ...editData, sgst: v })}
                      hideIfZero
                      suggestionName="sgst"
                      reviewSuggestions={reviewSuggestions}
                      onAccept={acceptSuggestion}
                      onReject={rejectSuggestion}
                    />
                    <EditableCurrencyField
                      label="IGST"
                      value={isEditing ? editData.igst : invoice.igst}
                      isEditing={isEditing}
                      onChange={(v: number) => setEditData({ ...editData, igst: v })}
                      hideIfZero
                      suggestionName="igst"
                      reviewSuggestions={reviewSuggestions}
                      onAccept={acceptSuggestion}
                      onReject={rejectSuggestion}
                    />
                    <div className="flex flex-col bg-gray-50/80 p-4">
                      <div className="flex justify-between items-center text-base font-bold">
                        <span className="text-gray-900">Total Amount</span>
                        {isEditing ? (
                          <input
                            type="number"
                            step="0.01"
                            value={editData.total}
                            onChange={(e) => setEditData({ ...editData, total: parseFloat(e.target.value) || 0 })}
                            className={cn("w-32 rounded-lg border-2 border-taxodo-primary/50 bg-white px-3 py-1.5 text-right font-bold focus:border-taxodo-primary focus:outline-none transition-all", reviewSuggestions.find((s: any) => s.field_name === "total") && "border-indigo-400 focus:border-indigo-500 shadow-[0_0_0_2px_rgba(99,102,241,0.2)]")}
                          />
                        ) : (
                          <span className="text-taxodo-primary text-xl">{formatCurrency(invoice.total)}</span>
                        )}
                      </div>
                      <AICopilotSuggestion suggestion={reviewSuggestions.find((s: any) => s.field_name === "total")} onAccept={acceptSuggestion} onReject={rejectSuggestion} />
                    </div>
                  </div>
                </div>

                {/* Approve/Reject Actions */}
                <div className="pt-2 border-t border-gray-100 mt-6">
                  {aiReviewMode && reviewSuggestions.length > 0 && (
                    <div className="mb-4 rounded-xl bg-indigo-50 p-4 border border-indigo-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm animate-in fade-in slide-in-from-bottom-2">
                      <div className="flex gap-3">
                        <Wand2 className="h-5 w-5 text-indigo-600 shrink-0 mt-0.5" />
                        <div>
                          <h3 className="text-sm font-bold text-indigo-900">AI Review Complete</h3>
                          <p className="text-sm text-indigo-700 mt-1">Review the {reviewSuggestions.length} inline suggestions above.</p>
                        </div>
                      </div>
                      <button onClick={acceptAllSuggestions} className="shrink-0 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-indigo-700 transition-colors active:scale-[0.98]">
                        Accept All Changes
                      </button>
                    </div>
                  )}

                  {approveError && (
                    <div className="mb-4 rounded-xl bg-red-50 p-4 border border-red-100">
                      <div className="flex gap-3">
                        <AlertTriangle className="h-5 w-5 text-red-600 shrink-0" />
                        <div>
                          <h3 className="text-sm font-bold text-red-800">Cannot Approve</h3>
                          <p className="text-sm text-red-700 mt-1">{approveError}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {isEditing ? (
                    <div className="flex flex-col gap-3 mt-4">
                      <button
                        onClick={() => updateMutation.mutate(editData)}
                        disabled={updateMutation.isPending}
                        className="flex w-full items-center justify-center gap-2 rounded-xl bg-taxodo-primary px-4 py-3.5 text-sm font-bold text-white shadow-sm hover:bg-taxodo-primary/90 disabled:opacity-50 transition-all active:scale-[0.98]"
                      >
                        {updateMutation.isPending ? (
                          <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                        ) : (
                          <><Save className="h-5 w-5" /> Save Changes & Re-validate</>
                        )}
                      </button>
                    </div>
                  ) : invoice.validation_status === "PENDING" || invoice.validation_status === "VALID" ? (
                    <div className="flex gap-4 mt-4">
                      <button
                        onClick={() => approveMutation.mutate()}
                        disabled={approveMutation.isPending || invoice.is_duplicate}
                        className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-taxodo-primary px-4 py-3.5 text-sm font-bold text-white shadow-sm hover:bg-taxodo-primary/90 disabled:opacity-50 transition-all active:scale-[0.98]"
                      >
                        <CheckCircle className="h-5 w-5" /> Approve Entry
                      </button>
                      <button
                        onClick={() => rejectMutation.mutate()}
                        disabled={rejectMutation.isPending}
                        className="flex flex-1 items-center justify-center gap-2 rounded-xl border-2 border-taxodo-border bg-white px-4 py-3.5 text-sm font-bold text-gray-700 hover:bg-gray-50 hover:text-taxodo-danger hover:border-taxodo-danger/30 disabled:opacity-50 transition-all active:scale-[0.98]"
                      >
                        <XCircle className="h-5 w-5" /> Reject
                      </button>
                    </div>
                  ) : (
                    <div className={cn("mt-4 flex items-center justify-center gap-2 rounded-xl p-4 text-sm font-bold", statusColor(invoice.validation_status))}>
                      {invoice.validation_status === "APPROVED" && <CheckCircle className="h-5 w-5" />}
                      Invoice {invoice.validation_status}
                    </div>
                  )}

                  {invoice.is_duplicate && (
                    <p className="text-center text-sm text-red-500 font-medium mt-3">
                      Cannot approve: Duplicate invoice detected.
                    </p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-white py-24 text-center">
              {doc?.status === "UPLOADED" || doc?.status === "PROCESSING" ? (
                <>
                  <div className="relative mb-6">
                    <div className="absolute inset-0 animate-ping rounded-full bg-taxodo-primary/20"></div>
                    <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-taxodo-primary/10">
                      <Zap className="h-8 w-8 text-taxodo-primary animate-pulse" />
                    </div>
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-gray-900">Extracting Data</h3>
                  <p className="max-w-xs text-sm text-gray-500 leading-relaxed">
                    Our AI is currently reading the document to extract vendor details, line items, and taxes...
                  </p>
                </>
              ) : (
                <p className="text-gray-500">Document data unavailable.</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm">
          <div className="w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="flex flex-col items-center p-6 text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600">
                <AlertTriangle className="h-7 w-7" />
              </div>
              <h3 className="mb-2 text-lg font-bold text-gray-900">Delete Document?</h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                Are you sure you want to delete <span className="font-semibold text-gray-700">{doc?.file_name}</span>? This action cannot be undone and will permanently remove the file and its extracted data.
              </p>
            </div>
            <div className="flex border-t border-gray-100 bg-gray-50/50 p-4 gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
                disabled={deleteMutation.isPending}
              >
                Cancel
              </button>
              <button
                onClick={() => deleteMutation.mutate()}
                className="flex-1 rounded-xl bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-red-700 transition-colors flex justify-center items-center"
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                ) : (
                  "Delete Permanently"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function AICopilotSuggestion({ suggestion, onAccept, onReject }: any) {
  if (!suggestion) return null;
  return (
    <div className="mt-2 w-full rounded-lg border border-indigo-200 bg-indigo-50/80 p-3 text-sm animate-in fade-in slide-in-from-top-1 shadow-sm">
      <div className="flex items-start gap-2.5">
        <Wand2 className="h-4 w-4 mt-0.5 text-indigo-600 shrink-0" />
        <div className="flex-1">
          <div className="flex items-center gap-2 font-mono text-[13px] mb-1.5">
            <span className="text-red-700 bg-red-100 px-1.5 py-0.5 rounded leading-none line-through decoration-red-400">{suggestion.old_value !== null ? suggestion.old_value : "Empty"}</span>
            <ArrowRight className="h-3.5 w-3.5 text-indigo-400" />
            <span className="text-green-800 font-bold bg-green-200 px-1.5 py-0.5 rounded leading-none shadow-sm">{suggestion.suggested_value !== null ? suggestion.suggested_value : "Empty"}</span>
          </div>
          <p className="text-indigo-900 leading-snug">{suggestion.reasoning}</p>
          <div className="mt-3 flex gap-2">
            <button type="button" onClick={() => onAccept(suggestion)} className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-indigo-700 transition-colors shadow-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none">Accept</button>
            <button type="button" onClick={() => onReject(suggestion.field_name)} className="rounded bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors focus:ring-2 focus:ring-gray-200 focus:outline-none">Reject</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function EditableDataField({ label, value, isEditing, onChange, className, suggestionName, reviewSuggestions, onAccept, onReject }: any) {
  const suggestion = reviewSuggestions?.find((s: any) => s.field_name === suggestionName);

  return (
    <div className={isEditing ? "flex flex-col gap-1 w-full" : "w-full"}>
      <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-1">{label}</p>
      {isEditing ? (
        <input
          type="text"
          value={value || ""}
          onChange={(e) => onChange?.(e.target.value)}
          className={cn("w-full rounded-lg border-2 border-taxodo-primary/50 bg-white px-3 py-1.5 text-sm font-medium focus:border-taxodo-primary focus:outline-none transition-all", className, suggestion && "border-indigo-400 focus:border-indigo-500 shadow-[0_0_0_2px_rgba(99,102,241,0.2)]")}
          placeholder={`Enter ${label.toLowerCase()}`}
        />
      ) : (
        <p className={cn("text-sm font-medium text-gray-900", className)}>{value || "—"}</p>
      )}
      <AICopilotSuggestion suggestion={suggestion} onAccept={onAccept} onReject={onReject} />
    </div>
  );
}

function EditableCurrencyField({ label, value, isEditing, onChange, hideIfZero, suggestionName, reviewSuggestions, onAccept, onReject }: any) {
  if (!isEditing && hideIfZero && !value && !reviewSuggestions?.find((s: any) => s.field_name === suggestionName)) return null;
  const suggestion = reviewSuggestions?.find((s: any) => s.field_name === suggestionName);

  return (
    <div className="flex flex-col border-b border-gray-100 p-3">
      <div className="flex justify-between items-center text-sm">
        <span className="text-gray-500 font-medium">{label}</span>
        {isEditing ? (
          <input
            type="number"
            step="0.01"
            value={value || 0}
            onChange={(e) => onChange?.(parseFloat(e.target.value) || 0)}
            className={cn("w-32 rounded-lg border-2 border-taxodo-primary/50 bg-white px-3 py-1.5 text-right font-medium focus:border-taxodo-primary focus:outline-none transition-all", suggestion && "border-indigo-400 focus:border-indigo-500 shadow-[0_0_0_2px_rgba(99,102,241,0.2)]")}
          />
        ) : (
          <span className="font-medium text-taxodo-ink">{formatCurrency(value)}</span>
        )}
      </div>
      <AICopilotSuggestion suggestion={suggestion} onAccept={onAccept} onReject={onReject} />
    </div>
  );
}
