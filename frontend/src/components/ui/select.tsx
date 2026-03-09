import * as React from "react";
import { cn } from "@/lib/utils";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  hasError?: boolean;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(({ className, hasError, ...props }, ref) => {
  return (
    <select
      ref={ref}
      className={cn(
        "taxodo-select w-full",
        hasError && "border-taxodo-danger focus:border-taxodo-danger focus:ring-taxodo-danger/20",
        className
      )}
      {...props}
    />
  );
});

Select.displayName = "Select";

export { Select };
