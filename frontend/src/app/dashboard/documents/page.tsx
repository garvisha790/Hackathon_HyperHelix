"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { formatDate, statusColor, cn } from "@/lib/utils";
import { Upload, FileText, RefreshCw, RotateCcw } from "lucide-react";

export default function DocumentsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [uploading, setUploading] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.get("/documents").then((r) => r.data),
    refetchInterval: 5000,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      setUploading(true);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", "invoice");
      const { data } = await api.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 60000,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setUploading(false);
    },
    onError: (err) => {
      console.error("Upload error:", err);
      setUploading(false);
    },
  });

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) uploadMutation.mutate(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  };

  const retryMutation = useMutation({
    mutationFn: async (docId: string) => {
      await api.post(`/documents/${docId}/process`, {}, { timeout: 120000 });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err) => {
      console.error("Retry error:", err);
    },
  });

  const docs = data?.documents || [];

  return (
    <div className="space-y-6 page-enter">
      <div className="section-intro">
        <div>
          <h1 className="text-2xl font-bold text-taxodo-ink">Documents</h1>
          <p className="section-subtitle">Upload invoices, credit notes, and receipts</p>
        </div>
        <button onClick={() => refetch()} className="flex items-center gap-2 rounded-md border border-taxodo-border bg-taxodo-surface px-3 py-2 text-[13px] font-semibold text-taxodo-ink transition-colors hover:bg-taxodo-subtle">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {/* Upload Zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-[#D5DEE3] bg-taxodo-surface p-10 transition-colors hover:border-taxodo-secondary hover:bg-taxodo-subtle"
      >
        <Upload className="mb-3 h-10 w-10 text-taxodo-muted opacity-50" />
        <p className="text-[15px] font-medium text-taxodo-ink">
          {uploading ? "Uploading & processing..." : "Drag & drop a file here, or click to browse"}
        </p>
        <p className="mt-1 text-[13px] text-taxodo-muted">Supports PDF, JPEG, PNG</p>
        <label className="mt-4 cursor-pointer rounded-sm bg-taxodo-primary px-5 py-2.5 text-[15px] font-semibold text-white transition-colors hover:bg-taxodo-primary-hover active:bg-taxodo-primary-active">
          Select File
          <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={handleFileSelect} className="hidden" />
        </label>
      </div>

      {/* Document List */}
      {isLoading ? (
        <div className="text-center text-[15px] text-taxodo-muted">Loading...</div>
      ) : docs.length === 0 ? (
        <div className="taxodo-card p-12 text-center">
          <FileText className="mx-auto mb-3 h-12 w-12 text-taxodo-muted opacity-30" />
          <p className="text-[15px] text-taxodo-muted">No documents uploaded yet</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="table-base table-zebra">
            <thead className="table-head">
              <tr>
                <th className="table-th text-left">File Name</th>
                <th className="table-th text-left">Type</th>
                <th className="table-th text-left">Status</th>
                <th className="table-th text-left">Date</th>
                <th className="table-th text-left">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-taxodo-border">
              {docs.map((doc: any) => (
                <tr
                  key={doc.id}
                  onClick={() => router.push(`/dashboard/documents/${doc.id}`)}
                  className="cursor-pointer transition-colors hover:bg-taxodo-subtle"
                >
                  <td className="table-td font-medium">{doc.file_name}</td>
                  <td className="table-td capitalize text-taxodo-muted">{doc.document_type.replace("_", " ")}</td>
                  <td className="table-td">
                    <span className={cn("inline-block rounded-sm px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide", statusColor(doc.status))}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="table-td text-taxodo-muted">{formatDate(doc.created_at)}</td>
                  <td className="table-td">
                    {["UPLOADED", "FAILED", "PROCESSING"].includes(doc.status) && (
                      <button
                        onClick={(e) => { e.stopPropagation(); retryMutation.mutate(doc.id); }}
                        className="flex items-center gap-1 rounded-md bg-taxodo-warning/10 px-2 py-1 text-[11px] font-bold uppercase tracking-wide text-taxodo-warning hover:bg-taxodo-warning/20 transition-colors"
                      >
                        <RotateCcw className="h-3 w-3" /> Retry
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
