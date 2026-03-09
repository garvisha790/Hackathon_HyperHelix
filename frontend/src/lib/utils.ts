import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    UPLOADED: "bg-taxodo-subtle text-taxodo-muted",
    PROCESSING: "bg-taxodo-warning/15 text-[#9b5b1f]",
    EXTRACTED: "bg-taxodo-info/15 text-taxodo-info",
    VALIDATED: "bg-taxodo-accent/25 text-taxodo-primary",
    DONE: "bg-taxodo-success/15 text-taxodo-success",
    FAILED: "bg-taxodo-danger/15 text-taxodo-danger",
    APPROVED: "bg-taxodo-success/15 text-taxodo-success",
    REJECTED: "bg-taxodo-danger/15 text-taxodo-danger",
    PENDING: "bg-taxodo-warning/15 text-[#9b5b1f]",
    AUTO_POSTED: "bg-taxodo-success/15 text-taxodo-success",
    NEEDS_REVIEW: "bg-taxodo-warning/15 text-[#9b5b1f]",
    CORRECTED: "bg-taxodo-info/15 text-taxodo-info",
  };
  return map[status] || "bg-taxodo-subtle text-taxodo-muted";
}

export function validationColor(status: string): string {
  const map: Record<string, string> = {
    pass: "border-taxodo-success/50 bg-taxodo-success/10",
    fail: "border-taxodo-danger/50 bg-taxodo-danger/10",
    warn: "border-taxodo-warning/50 bg-taxodo-warning/15",
  };
  return map[status] || "border-taxodo-border";
}
