"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, FileText, BookOpen, Receipt,
  BarChart3, MessageSquare, Settings, LogOut, Shield, ChevronLeft, ChevronRight
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import Image from "next/image";

const NAV_ITEMS = [
  { href: "/dashboard/overview", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/documents", label: "Documents", icon: FileText },
  { href: "/dashboard/ledger", label: "Ledger", icon: BookOpen },
  { href: "/dashboard/tax", label: "Tax", icon: Receipt },
  { href: "/dashboard/copilot", label: "AI Copilot", icon: MessageSquare },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
  { href: "/dashboard/audit", label: "Audit Log", icon: Shield, ownerOnly: true },
];

interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
}

export function Sidebar({ isCollapsed, setIsCollapsed }: SidebarProps) {
  const pathname = usePathname();
  const { role, logout } = useAuth();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-30 flex h-screen flex-col border-r border-taxodo-primary-hover bg-taxodo-primary shadow-xl transition-all duration-300 ease-in-out",
        isCollapsed ? "w-20" : "w-64"
      )}
    >
      <div className={cn("flex h-[72px] items-center border-b border-white/10 relative", isCollapsed ? "justify-center px-4" : "px-6 justify-between")}>
        {!isCollapsed ? (
          <Image
            src="/icons/taxodo_logo_white.svg"
            alt="Taxodo AI"
            width={160}
            height={32}
            className="h-8 w-auto drop-shadow-sm"
          />
        ) : (
          <Image
            src="/icons/taxodo_app_icon.svg"
            alt="Taxodo"
            width={32}
            height={32}
            className="h-8 w-8"
          />
        )}

        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3 top-6 flex h-6 w-6 items-center justify-center rounded-full border border-taxodo-border bg-white text-taxodo-muted shadow-sm hover:text-taxodo-primary"
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      <nav className="flex-1 space-y-1.5 px-3 py-6 overflow-hidden">
        {!isCollapsed && (
          <div className="mb-3 px-3 text-[11px] font-bold uppercase tracking-wider text-white/40">
            Main Menu
          </div>
        )}
        {NAV_ITEMS.filter((item) => !item.ownerOnly || role === "owner").map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              title={isCollapsed ? item.label : undefined}
              className={cn(
                "group flex items-center rounded-md py-2.5 text-[15px] font-medium transition-all duration-150 ease-out",
                isCollapsed ? "justify-center px-0" : "gap-3 px-3",
                isActive
                  ? "bg-taxodo-secondary text-white shadow-sm"
                  : "text-white/70 hover:bg-white/10 hover:text-white"
              )}
            >
              <item.icon className={cn(
                "h-5 w-5 transition-colors flex-shrink-0",
                isActive ? "text-white" : "text-white/50 group-hover:text-white"
              )} />
              {!isCollapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-3">
        <button
          onClick={logout}
          title={isCollapsed ? "Sign Out" : undefined}
          className={cn(
            "group flex w-full items-center rounded-md py-2.5 text-[15px] font-medium text-white/70 transition-colors hover:bg-white/10 hover:text-white",
            isCollapsed ? "justify-center px-0" : "gap-3 px-3"
          )}
        >
          <LogOut className="h-5 w-5 text-white/50 transition-colors group-hover:text-white flex-shrink-0" />
          {!isCollapsed && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
}
