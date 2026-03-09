import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  kicker?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, subtitle, kicker = "Taxodo AI", actions, className }: PageHeaderProps) {
  return (
    <div className={cn("section-intro", className)}>
      <div>
        <p className="section-kicker">{kicker}</p>
        <h1 className="mt-2">{title}</h1>
        {subtitle && <p className="section-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
