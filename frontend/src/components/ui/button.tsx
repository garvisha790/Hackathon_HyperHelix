import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm border text-sm font-semibold leading-none transition-colors duration-[120ms] ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-taxodo-secondary/20 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "border-taxodo-primary bg-taxodo-primary text-white hover:border-taxodo-primary-hover hover:bg-taxodo-primary-hover active:border-taxodo-primary-active active:bg-taxodo-primary-active",
        secondary: "border-taxodo-secondary bg-taxodo-surface text-taxodo-secondary hover:bg-taxodo-subtle",
        tertiary: "border-transparent bg-transparent text-taxodo-muted hover:bg-taxodo-subtle hover:text-taxodo-ink",
        cta: "border-taxodo-cta bg-taxodo-cta text-taxodo-ink hover:brightness-95 active:brightness-90",
        danger: "border-taxodo-danger bg-taxodo-danger text-white hover:brightness-95 active:brightness-90",
      },
      size: {
        default: "h-10 px-4",
        sm: "h-9 px-3 text-[13px]",
        lg: "h-11 px-5",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return <button className={cn(buttonVariants({ variant, size }), className)} ref={ref} {...props} />;
  }
);

Button.displayName = "Button";

export { Button, buttonVariants };
