import type { Metadata } from "next";
import { Manrope, Source_Sans_3 } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/components/layout/query-provider";
import { AuthProvider } from "@/hooks/use-auth";

const manrope = Manrope({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-manrope",
});

const sourceSans3 = Source_Sans_3({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-source-sans-3",
});

export const metadata: Metadata = {
  title: "Taxodo AI | Auditor-Grade Tax Intelligence",
  description: "AI-powered bookkeeping, GST compliance, and tax intelligence for modern Indian businesses.",
  icons: {
    icon: "/icons/taxodo_app_icon.svg",
    shortcut: "/icons/taxodo_app_icon.svg",
    apple: "/icons/taxodo_app_icon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${manrope.variable} ${sourceSans3.variable} app-shell antialiased`}>
        <AuthProvider>
          <QueryProvider>{children}</QueryProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
