"use client";
import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { formatDate, statusColor, cn } from "@/lib/utils";
import { Upload, FileText, RefreshCw, RotateCcw, Loader2, Eye, CheckCircle2, XCircle, CloudUpload, ScanSearch, BrainCircuit, CircleCheck } from "lucide-react";
import { DuplicateModal } from "@/components/documents/duplicate-modal";

// Pipeline steps for display
const PIPELINE_STEPS = [
  { key: "upload", label: "Upload", icon: CloudUpload },
  { key: "extract", label: "Extract", icon: ScanSearch },
  { key: "validate", label: "AI Validate", icon: BrainCircuit },
  { key: "done", label: "Done", icon: CircleCheck },
];

function getActiveStep(status: string): number {
  switch (status) {
    case "UPLOADED": return 0;
    case "PROCESSING": return 1;
    case "EXTRACTED": return 2;
    case "VALIDATED": case "DONE": case "APPROVED": return 3;
    default: return -1; // FAILED
  }
}

export default function DocumentsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [uploading, setUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState(0); // 0=uploading, 1=processing, 2=validating, 3=done
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [duplicateInfo, setDuplicateInfo] = useState<any>(null);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.get("/documents").then((r) => r.data),
    refetchInterval: uploading ? 3000 : 8000,
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
      setUploadStep(0);
      setUploadError(null);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", "invoice");
      if (replaceDocId) {
        formData.append("replace_document_id", replaceDocId);
      }
      const { data } = await api.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
        onUploadProgress: (progressEvent) => {
          if (progressEvent.loaded === progressEvent.total) {
            setUploadStep(1); // Upload done, now processing
          }
        },
      });
      return data;
    },
    onSuccess: () => {
      setUploadStep(3); // Done
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setTimeout(() => {
        setUploading(false);
        setUploadStep(0);
        setPendingFile(null);
        setDuplicateInfo(null);
        setShowDuplicateModal(false);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }, 1500);
    },
    onError: (err: any) => {
      console.error("Upload error:", err);
      const detail = err?.response?.data?.detail;
      if (detail && typeof detail === "string") {
        setUploadError(detail);
      } else {
        setUploadError("Upload failed. Please try again.");
      }
      setUploading(false);
      setUploadStep(0);
      if (fileInputRef.current) fileInputRef.current.value = "";
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

  // Track processing status from polled data to update upload step indicator
  useEffect(() => {
    if (!uploading || !docs.length) return;
    // Find the most recently uploaded doc (last in array or most recently created)
    const latest = docs[docs.length - 1];
    if (!latest) return;
    const step = getActiveStep(latest.status);
    if (step > uploadStep) setUploadStep(step);
  }, [docs, uploading]);

  const isProcessing = (status: string) =>
    ["UPLOADED", "PROCESSING"].includes(status);
  const isReviewable = (status: string) =>
    ["EXTRACTED", "VALIDATED", "DONE", "APPROVED"].includes(status);

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
        className={cn(
          "relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed bg-taxodo-surface p-10 transition-all",
          uploading
            ? "border-taxodo-primary/40 bg-taxodo-primary/[0.03]"
            : "border-[#D5DEE3] hover:border-taxodo-secondary hover:bg-taxodo-subtle"
        )}
      >
        {uploading ? (
          /* ─── Live progress stepper ─── */
          <div className="flex w-full max-w-md flex-col items-center gap-5">
            <Loader2 className="h-8 w-8 animate-spin text-taxodo-primary" />
            <p className="text-[15px] font-semibold text-taxodo-ink">
              {uploadStep === 0 && "Uploading file..."}
              {uploadStep === 1 && "Extracting invoice data (OCR)..."}
              {uploadStep === 2 && "Running AI validation..."}
              {uploadStep === 3 && "Complete!"}
            </p>

            {/* Step indicators */}
            <div className="flex w-full items-center justify-between">
              {PIPELINE_STEPS.map((step, i) => {
                const StepIcon = step.icon;
                const isDone = uploadStep > i;
                const isCurrent = uploadStep === i;
                return (
                  <div key={step.key} className="flex flex-1 items-center">
                    <div className="flex flex-col items-center gap-1">
                      <div
                        className={cn(
                          "flex h-8 w-8 items-center justify-center rounded-full transition-all duration-300",
                          isDone
                            ? "bg-green-500 text-white"
                            : isCurrent
                              ? "bg-taxodo-primary text-white animate-pulse"
                              : "bg-gray-200 text-gray-400"
                        )}
                      >
                        {isDone ? (
                          <CheckCircle2 className="h-4 w-4" />
                        ) : isCurrent ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <StepIcon className="h-4 w-4" />
                        )}
                      </div>
                      <span
                        className={cn(
                          "text-[11px] font-medium",
                          isDone
                            ? "text-green-600"
                            : isCurrent
                              ? "text-taxodo-primary font-semibold"
                              : "text-gray-400"
                        )}
                      >
                        {step.label}
                      </span>
                    </div>
                    {i < PIPELINE_STEPS.length - 1 && (
                      <div
                        className={cn(
                          "mx-1 mt-[-16px] h-0.5 flex-1 rounded transition-all duration-500",
                          isDone ? "bg-green-400" : "bg-gray-200"
                        )}
                      />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Progress bar */}
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-700 ease-out",
                  uploadStep === 3 ? "bg-green-500" : "bg-taxodo-primary"
                )}
                style={{ width: `${Math.min(((uploadStep + 1) / PIPELINE_STEPS.length) * 100, 100)}%` }}
              />
            </div>
          </div>
        ) : (
          /* ─── Default drop zone ─── */
          <>
            <Upload className="mb-3 h-10 w-10 text-taxodo-muted opacity-50" />
            <p className="text-[15px] font-medium text-taxodo-ink">Drag & drop a file here, or click to browse</p>
            <p className="mt-1 text-[13px] text-taxodo-muted">Supports PDF, JPEG, PNG</p>
            {uploadError && (
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-2 text-[13px] text-red-700">
                <XCircle className="h-4 w-4 flex-shrink-0" />
                <span>{uploadError}</span>
                <button onClick={() => setUploadError(null)} className="ml-auto text-red-400 hover:text-red-600">&times;</button>
              </div>
            )}
            <label className="mt-4 cursor-pointer rounded-sm bg-taxodo-primary px-5 py-2.5 text-[15px] font-semibold text-white transition-colors hover:bg-taxodo-primary-hover active:bg-taxodo-primary-active">
              Select File
              <input ref={fileInputRef} type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={handleFileSelect} className="hidden" />
            </label>
          </>
        )}
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
              {docs.map((doc: any) => {
                const activeStep = getActiveStep(doc.status);
                return (
                <tr
                  key={doc.id}
                  onClick={() => router.push(`/dashboard/documents/${doc.id}`)}
                  className="cursor-pointer transition-colors hover:bg-taxodo-subtle"
                >
                  <td className="table-td font-medium">{doc.file_name}</td>
                  <td className="table-td capitalize text-taxodo-muted">{doc.document_type.replace("_", " ")}</td>

                  {/* ─── Status cell with mini pipeline ─── */}
                  <td className="table-td">
                    {doc.status === "FAILED" ? (
                      <span className="inline-flex items-center gap-1 rounded-sm bg-red-50 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide text-red-600">
                        <XCircle className="h-3 w-3" /> Failed
                      </span>
                    ) : isProcessing(doc.status) ? (
                      /* In-progress: show animated pipeline */
                      <div className="flex items-center gap-1.5">
                        {PIPELINE_STEPS.map((step, i) => {
                          const isDone = activeStep > i;
                          const isCurrent = activeStep === i;
                          return (
                            <div key={step.key} className="flex items-center gap-1.5">
                              <div
                                className={cn(
                                  "flex h-5 w-5 items-center justify-center rounded-full text-white transition-all",
                                  isDone
                                    ? "bg-green-500"
                                    : isCurrent
                                      ? "bg-taxodo-primary animate-pulse"
                                      : "bg-gray-200 text-gray-400"
                                )}
                              >
                                {isDone ? (
                                  <CheckCircle2 className="h-3 w-3" />
                                ) : isCurrent ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <span className="text-[8px]">{i + 1}</span>
                                )}
                              </div>
                              {i < PIPELINE_STEPS.length - 1 && (
                                <div className={cn("h-px w-3", isDone ? "bg-green-400" : "bg-gray-200")} />
                              )}
                            </div>
                          );
                        })}
                        <span className="ml-1 text-[11px] font-medium text-taxodo-primary">
                          {PIPELINE_STEPS[Math.min(activeStep, PIPELINE_STEPS.length - 1)]?.label}...
                        </span>
                      </div>
                    ) : (
                      /* Completed statuses: show badge */
                      <span className={cn("inline-block rounded-sm px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide", statusColor(doc.status))}>
                        {doc.status}
                      </span>
                    )}
                  </td>

                  <td className="table-td text-taxodo-muted">{formatDate(doc.created_at)}</td>

                  {/* ─── Actions cell ─── */}
                  <td className="table-td">
                    {doc.status === "FAILED" ? (
                      <button
                        onClick={(e) => { e.stopPropagation(); retryMutation.mutate(doc.id); }}
                        className="flex items-center gap-1 rounded-md bg-taxodo-warning/10 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-taxodo-warning hover:bg-taxodo-warning/20 transition-colors"
                      >
                        <RotateCcw className="h-3 w-3" /> Retry
                      </button>
                    ) : isProcessing(doc.status) ? (
                      <span className="flex items-center gap-1.5 text-[11px] font-medium text-taxodo-muted">
                        <Loader2 className="h-3 w-3 animate-spin text-taxodo-primary" />
                        Processing...
                      </span>
                    ) : isReviewable(doc.status) ? (
                      <button
                        onClick={(e) => { e.stopPropagation(); router.push(`/dashboard/documents/${doc.id}`); }}
                        className="flex items-center gap-1 rounded-md bg-taxodo-primary/10 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-taxodo-primary hover:bg-taxodo-primary/20 transition-colors"
                      >
                        <Eye className="h-3 w-3" /> Review
                      </button>
                    ) : null}
                  </td>
                </tr>
                );
              })}
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
