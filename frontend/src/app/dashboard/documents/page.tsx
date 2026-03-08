"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { formatDate, statusColor, cn } from "@/lib/utils";
import { Upload, FileText, RefreshCw, RotateCcw, Loader2 } from "lucide-react";
import { DuplicateModal } from "@/components/documents/duplicate-modal";

// Processing stage helper
function getProcessingStage(status: string) {
  const stages = {
    UPLOADED: { stage: 1, text: "Uploaded", icon: "✓" },
    PROCESSING: { stage: 2, text: "Extracting Data", icon: "↻" },
    DONE: { stage: 3, text: "Validating", icon: "↻" },
    VALIDATED: { stage: 4, text: "Complete", icon: "✓" },
    APPROVED: { stage: 4, text: "Complete", icon: "✓" },
    FAILED: { stage: 0, text: "Failed", icon: "✗" },
  };
  return stages[status as keyof typeof stages] || { stage: 0, text: status, icon: "" };
}

export default function DocumentsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [uploading, setUploading] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [duplicateInfo, setDuplicateInfo] = useState<any>(null);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.get("/documents").then((r) => r.data),
    refetchInterval: 5000,
  });

  const checkDuplicateMutation = useMutation({
    mutationFn: async (fileName: string) => {
      const { data } = await api.get(`/documents/check-duplicate/${encodeURIComponent(fileName)}`);
      return data;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async ({ file, replaceDocId }: { file: File; replaceDocId?: string }) => {
      setUploading(true);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", "invoice");
      if (replaceDocId) {
        formData.append("replace_document_id", replaceDocId);
      }
      const { data } = await api.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 60000,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setUploading(false);
      setPendingFile(null);
      setDuplicateInfo(null);
      setShowDuplicateModal(false);
    },
    onError: (err) => {
      console.error("Upload error:", err);
      setUploading(false);
    },
  });

  const handleFileUpload = async (file: File) => {
    // Check for duplicate first
    const duplicateCheck = await checkDuplicateMutation.mutateAsync(file.name);
    
    if (duplicateCheck.is_duplicate) {
      // Show duplicate modal
      setPendingFile(file);
      setDuplicateInfo(duplicateCheck.existing_document);
      setShowDuplicateModal(true);
    } else {
      // No duplicate, upload directly
      uploadMutation.mutate({ file });
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file);
  };

  const handleReplaceDocument = () => {
    if (pendingFile && duplicateInfo) {
      uploadMutation.mutate({ file: pendingFile, replaceDocId: duplicateInfo.id });
    }
  };

  const handleKeepBoth = () => {
    if (pendingFile) {
      uploadMutation.mutate({ file: pendingFile });
    }
  };

  const handleCloseDuplicateModal = () => {
    setShowDuplicateModal(false);
    setPendingFile(null);
    setDuplicateInfo(null);
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
                    {doc.status === "PROCESSING" || doc.status === "UPLOADED" ? (
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-3.5 w-3.5 animate-spin text-taxodo-primary" />
                        <div className="flex flex-col">
                          <span className="text-xs font-semibold text-taxodo-ink">{getProcessingStage(doc.status).text}</span>
                          <div className="flex items-center gap-1 text-[10px] text-taxodo-muted">
                            <span className={doc.status === "UPLOADED" || doc.status === "PROCESSING" || doc.status === "DONE" || doc.status === "VALIDATED" ? "text-green-600" : "text-gray-400"}>Upload</span>
                            <span>→</span>
                            <span className={doc.status === "PROCESSING" || doc.status === "DONE" || doc.status === "VALIDATED" ? "text-taxodo-primary font-semibold" : "text-gray-400"}>Extract</span>
                            <span>→</span>
                            <span className={doc.status === "DONE" || doc.status === "VALIDATED" ? "text-taxodo-primary font-semibold" : "text-gray-400"}>Validate</span>
                            <span>→</span>
                            <span className={doc.status === "VALIDATED" || doc.status === "APPROVED" ? "text-green-600" : "text-gray-400"}>Done</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <span className={cn("inline-block rounded-sm px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide", statusColor(doc.status))}>
                        {doc.status}
                      </span>
                    )}
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

      {/* Duplicate Detection Modal */}
      {showDuplicateModal && duplicateInfo && pendingFile && (
        <DuplicateModal
          isOpen={showDuplicateModal}
          onClose={handleCloseDuplicateModal}
          onReplace={handleReplaceDocument}
          onKeepBoth={handleKeepBoth}
          existingDocument={duplicateInfo}
          newFileName={pendingFile.name}
        />
      )}
    </div>
  );
}
