import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/components/layout/query-provider";

export const metadata: Metadata = {
  title: "Digital CA — AI-Powered Chartered Accountant",
  description: "Automated bookkeeping, GST compliance, and financial intelligence for Indian businesses",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
