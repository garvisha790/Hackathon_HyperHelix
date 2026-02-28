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
    UPLOADED: "bg-gray-100 text-gray-700",
    PROCESSING: "bg-yellow-100 text-yellow-700",
    EXTRACTED: "bg-blue-100 text-blue-700",
    VALIDATED: "bg-indigo-100 text-indigo-700",
    DONE: "bg-green-100 text-green-700",
    FAILED: "bg-red-100 text-red-700",
    APPROVED: "bg-green-100 text-green-700",
    REJECTED: "bg-red-100 text-red-700",
    PENDING: "bg-yellow-100 text-yellow-700",
    AUTO_POSTED: "bg-green-100 text-green-700",
    NEEDS_REVIEW: "bg-orange-100 text-orange-700",
    CORRECTED: "bg-purple-100 text-purple-700",
  };
  return map[status] || "bg-gray-100 text-gray-700";
}

export function validationColor(status: string): string {
  const map: Record<string, string> = {
    pass: "border-green-400 bg-green-50",
    fail: "border-red-400 bg-red-50",
    warn: "border-amber-400 bg-amber-50",
  };
  return map[status] || "border-gray-200";
}
