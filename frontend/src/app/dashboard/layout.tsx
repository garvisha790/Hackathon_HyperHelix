"use client";
import { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { AuthGuard } from "@/components/auth-guard";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="min-h-screen app-shell flex">
      <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />
      <main
        className={`min-h-screen bg-taxodo-page p-8 transition-all duration-300 ease-in-out ${isCollapsed ? "ml-20" : "ml-64"
          } flex-1`}
      >
        <AuthGuard>{children}</AuthGuard>
      </main>
    </div>
  );
}
