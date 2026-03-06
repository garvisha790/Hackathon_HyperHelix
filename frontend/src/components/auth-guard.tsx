"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const { isAuthenticated, verifySession } = useAuth();
    const [isVerifying, setIsVerifying] = useState(true);

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const isValid = await verifySession();
                if (!isValid) {
                    router.replace("/auth/login");
                }
            } catch (err) {
                router.replace("/auth/login");
            } finally {
                setIsVerifying(false);
            }
        };

        checkAuth();
    }, [pathname, router, verifySession]);

    if (isVerifying) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-taxodo-page">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-taxodo-primary border-t-transparent mx-auto"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return null; // Will redirect in useEffect
    }

    return <>{children}</>;
}
