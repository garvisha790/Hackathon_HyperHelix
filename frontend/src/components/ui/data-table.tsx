import { cn } from "@/lib/utils";

export function DataTableWrap({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("table-wrap", className)}>{children}</div>;
}

export function DataTable({ className, children }: { className?: string; children: React.ReactNode }) {
  return <table className={cn("table-base table-zebra", className)}>{children}</table>;
}

export function DataTableHead({ children }: { children: React.ReactNode }) {
  return <thead className="table-head">{children}</thead>;
}

export function DataTableRow({ className, children }: { className?: string; children: React.ReactNode }) {
  return <tr className={className}>{children}</tr>;
}

export function DataTableTh({ className, children }: { className?: string; children: React.ReactNode }) {
  return <th className={cn("table-th", className)}>{children}</th>;
}

export function DataTableTd({ className, children }: { className?: string; children: React.ReactNode }) {
  return <td className={cn("table-td", className)}>{children}</td>;
}
