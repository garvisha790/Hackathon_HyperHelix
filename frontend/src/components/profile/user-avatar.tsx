/**
 * UserAvatar Component
 * 
 * A production-ready avatar component that displays user initials
 * with consistent styling across the application
 */
import { cn } from "@/lib/utils";

interface UserAvatarProps {
  name?: string;
  email?: string;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  showTooltip?: boolean;
}

const sizeClasses = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-12 w-12 text-base",
  xl: "h-16 w-16 text-lg",
};

/**
 * Generates a consistent color based on the user's name
 * Uses a hash function to ensure the same name always gets the same color
 */
function getAvatarColor(name: string): string {
  const colors = [
    "bg-taxodo-primary text-white",
    "bg-taxodo-secondary text-white",
    "bg-taxodo-accent text-taxodo-ink",
    "bg-taxodo-cta text-white",
    "bg-taxodo-success text-white",
    "bg-taxodo-info text-white",
  ];
  
  // Simple hash function for consistent color selection
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  return colors[Math.abs(hash) % colors.length];
}

/**
 * Extracts initials from a name
 * Examples: "John Doe" -> "JD", "Alice" -> "A"
 */
function getInitials(name?: string, email?: string): string {
  if (name && name.trim()) {
    const parts = name.trim().split(" ");
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return parts[0][0].toUpperCase();
  }
  
  if (email) {
    return email[0].toUpperCase();
  }
  
  return "?";
}

export function UserAvatar({
  name,
  email,
  size = "md",
  className,
  showTooltip = false,
}: UserAvatarProps) {
  const initials = getInitials(name, email);
  const colorClass = getAvatarColor(name || email || "default");
  
  const avatar = (
    <div
      className={cn(
        "flex items-center justify-center rounded-full font-semibold shadow-sm ring-2 ring-white/20 transition-all duration-200 hover:shadow-md",
        sizeClasses[size],
        colorClass,
        className
      )}
      title={showTooltip ? name || email : undefined}
    >
      {initials}
    </div>
  );
  
  return avatar;
}
