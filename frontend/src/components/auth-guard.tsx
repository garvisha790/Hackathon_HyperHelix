"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const { isAuthenticated } = useAuth();
    const [hasToken, setHasToken] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Check for token on mount (client-side only)
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem("token");
            console.log("[AUTH-GUARD] Token check:", !!token);
            
            if (!token) {
                console.log("[AUTH-GUARD] No token, redirecting to login");
                router.replace("/auth/login");
                setIsLoading(false);
                return;
            }
            
            // Have token - allow access immediately
            console.log("[AUTH-GUARD] Token found, allowing access");
            setHasToken(true);
            setIsLoading(false);
        }
    }, [router]);

    // Show loading spinner during initial check
    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-taxodo-page">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-taxodo-primary border-t-transparent mx-auto"></div>
            </div>
        );
    }

    // If no token, don't render (useEffect will redirect)
    if (!hasToken) {
        return null;
    }

    // If we have a token, render children
    // The auth context will handle session verification in the background
    return <>{children}</>;
}
