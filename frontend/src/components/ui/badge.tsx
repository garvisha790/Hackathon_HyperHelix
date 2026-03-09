import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[12px] font-semibold", {
  variants: {
    variant: {
      neutral: "bg-taxodo-subtle text-taxodo-muted",
      success: "bg-taxodo-success/15 text-taxodo-success",
      warning: "bg-taxodo-warning/15 text-[#9b5b1f]",
      danger: "bg-taxodo-danger/15 text-taxodo-danger",
      info: "bg-taxodo-info/15 text-taxodo-info",
      highlight: "bg-taxodo-accent/25 text-taxodo-primary",
    },
  },
  defaultVariants: {
    variant: "neutral",
  },
});

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
