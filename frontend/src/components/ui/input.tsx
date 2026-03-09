import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, hasError, ...props }, ref) => {
  return (
    <input
      ref={ref}
      className={cn(
        "taxodo-input",
        hasError && "border-taxodo-danger focus:border-taxodo-danger focus:ring-taxodo-danger/20",
        className
      )}
      {...props}
    />
  );
});

Input.displayName = "Input";

export { Input };
