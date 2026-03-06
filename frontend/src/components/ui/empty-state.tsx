import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  className?: string;
}

export function EmptyState({ icon, title, description, className }: EmptyStateProps) {
  return (
    <div className={cn("taxodo-card taxodo-card-pad text-center", className)}>
      {icon && <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-md bg-taxodo-subtle text-taxodo-muted">{icon}</div>}
      <h3 className="text-[18px] font-semibold text-taxodo-ink">{title}</h3>
      <p className="mt-2 text-[15px] text-taxodo-muted">{description}</p>
    </div>
  );
}
