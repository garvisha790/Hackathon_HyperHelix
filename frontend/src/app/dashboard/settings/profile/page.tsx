"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { UserAvatar } from "@/components/profile/user-avatar";
import { BuildingIcon, CreditCard, MailIcon, ShieldCheckIcon, UserCircleIcon, Save, CheckCircle, AlertCircle, Edit2, Calendar } from "lucide-react";

export default function ProfileSettingsPage() {
    const { userProfile } = useAuth();
    const queryClient = useQueryClient();
    const [isEditing, setIsEditing] = useState(false);
    const [name, setName] = useState("");
    const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");

    // Initialize name when userProfile loads
    useEffect(() => {
        if (userProfile?.name) {
            setName(userProfile.name);
        }
    }, [userProfile]);

    const updateMutation = useMutation({
        mutationFn: (data: { name: string }) => api.put("/users/me", data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["auth"] });
            setSaveStatus("success");
            setIsEditing(false);
            setTimeout(() => setSaveStatus("idle"), 3000);
        },
        onError: () => {
            setSaveStatus("error");
            setTimeout(() => setSaveStatus("idle"), 3000);
        },
    });

    const handleSave = () => {
        if (name.trim()) {
            updateMutation.mutate({ name: name.trim() });
        }
    };

    const handleCancel = () => {
        setName(userProfile?.name || "");
        setIsEditing(false);
        setSaveStatus("idle");
    };

    if (!userProfile) {
        return (
            <div className="flex h-64 items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-taxodo-primary border-t-transparent mx-auto"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6 page-enter">
            {/* Header */}
            <div className="section-intro">
                <div>
                    <h1 className="text-2xl font-bold text-taxodo-ink">Profile & Settings</h1>
                    <p className="mt-1 text-[15px] text-taxodo-muted">Manage your personal account and company preferences.</p>
                </div>
            </div>

            {/* Success/Error Messages */}
            {saveStatus === "success" && (
                <div className="animate-in fade-in slide-in-from-top-2 flex items-center gap-3 rounded-lg bg-taxodo-success/10 border border-taxodo-success/20 px-4 py-3 text-taxodo-success">
                    <CheckCircle className="h-5 w-5 flex-shrink-0" />
                    <span className="text-sm font-medium">Profile updated successfully!</span>
                </div>
            )}
            {saveStatus === "error" && (
                <div className="animate-in fade-in slide-in-from-top-2 flex items-center gap-3 rounded-lg bg-taxodo-danger/10 border border-taxodo-danger/20 px-4 py-3 text-taxodo-danger">
                    <AlertCircle className="h-5 w-5 flex-shrink-0" />
                    <span className="text-sm font-medium">Failed to update profile. Please try again.</span>
                </div>
            )}

            <div className="grid gap-6 lg:grid-cols-2">
                {/* Personal Info Card */}
                <div className="taxodo-card taxodo-card-pad">
                    <div className="mb-6 flex items-start justify-between">
                        <div className="flex items-center gap-4">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-taxodo-primary/10 text-taxodo-primary">
                                <UserCircleIcon className="h-6 w-6" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-taxodo-ink font-manrope">Personal Information</h3>
                                <p className="text-sm text-taxodo-muted">Your identity and login details</p>
                            </div>
                        </div>
                        {!isEditing && (
                            <button
                                onClick={() => setIsEditing(true)}
                                className="flex items-center gap-2 rounded-md bg-taxodo-subtle px-3 py-1.5 text-sm font-medium text-taxodo-ink transition-colors hover:bg-taxodo-border"
                            >
                                <Edit2 className="h-4 w-4" />
                                Edit
                            </button>
                        )}
                    </div>

                    <div className="space-y-5">
                        {/* Avatar Section */}
                        <div className="flex items-center gap-4 rounded-lg bg-taxodo-subtle p-4">
                            <UserAvatar
                                name={userProfile.name}
                                email={userProfile.email}
                                size="xl"
                            />
                            <div>
                                <div className="text-sm font-medium text-taxodo-muted">Profile Picture</div>
                                <div className="mt-1 text-xs text-taxodo-muted">Auto-generated from your name</div>
                            </div>
                        </div>

                        {/* Full Name */}
                        <div>
                            <label className="mb-2 block text-sm font-semibold text-taxodo-ink">Full Name</label>
                            {isEditing ? (
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="taxodo-input"
                                    placeholder="Enter your full name"
                                />
                            ) : (
                                <div className="font-medium text-taxodo-ink">{userProfile.name || "Not set"}</div>
                            )}
                        </div>

                        {/* Email */}
                        <div>
                            <label className="mb-2 flex items-center gap-2 text-sm font-semibold text-taxodo-ink">
                                <MailIcon className="h-4 w-4" />
                                Email Address
                            </label>
                            <div className="flex items-center gap-2 font-medium text-taxodo-ink">
                                {userProfile.email}
                                <span className="inline-flex items-center rounded-full bg-taxodo-success/10 px-2 py-0.5 text-xs font-medium text-taxodo-success">
                                    ✓ Verified
                                </span>
                            </div>
                            <p className="mt-1 text-xs text-taxodo-muted">Email cannot be changed after registration</p>
                        </div>

                        {/* Role */}
                        <div>
                            <label className="mb-2 block text-sm font-semibold text-taxodo-ink">Role</label>
                            <span className="inline-flex items-center rounded-full bg-taxodo-secondary/10 px-3 py-1.5 text-sm font-medium uppercase tracking-wider text-taxodo-secondary">
                                {userProfile.role}
                            </span>
                        </div>

                        {/* Member Since */}
                        <div>
                            <label className="mb-2 flex items-center gap-2 text-sm font-semibold text-taxodo-ink">
                                <Calendar className="h-4 w-4" />
                                Member Since
                            </label>
                            <div className="text-sm text-taxodo-muted">
                                {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                            </div>
                        </div>

                        {/* Action Buttons */}
                        {isEditing && (
                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={handleSave}
                                    disabled={updateMutation.isPending || !name.trim()}
                                    className="flex items-center gap-2 rounded-md bg-taxodo-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:bg-taxodo-primary-hover disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {updateMutation.isPending ? (
                                        <>
                                            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="h-4 w-4" />
                                            Save Changes
                                        </>
                                    )}
                                </button>
                                <button
                                    onClick={handleCancel}
                                    disabled={updateMutation.isPending}
                                    className="rounded-md border border-taxodo-border bg-white px-4 py-2 text-sm font-medium text-taxodo-ink transition-colors hover:bg-taxodo-subtle disabled:opacity-50"
                                >
                                    Cancel
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Security Card */}
                <div className="taxodo-card taxodo-card-pad">
                    <div className="mb-6 flex items-center gap-4">
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
                            <ShieldCheckIcon className="h-6 w-6" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-taxodo-ink font-manrope">Account Security</h3>
                            <p className="text-sm text-taxodo-muted">Authentication and security settings</p>
                        </div>
                    </div>

                    <div className="space-y-5">
                        <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4">
                            <div className="flex items-center gap-3">
                                <ShieldCheckIcon className="h-5 w-5 text-emerald-600 flex-shrink-0" />
                                <div>
                                    <div className="font-medium text-emerald-900">Protected by AWS Cognito</div>
                                    <div className="mt-0.5 text-sm text-emerald-700">Your account uses industry-standard authentication</div>
                                </div>
                            </div>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-semibold text-taxodo-ink">Password</label>
                            <p className="text-sm text-taxodo-muted mb-3">Manage your password through AWS Cognito</p>
                            <button
                                disabled
                                className="rounded-md border border-taxodo-border bg-white px-4 py-2 text-sm font-medium text-taxodo-muted opacity-50 cursor-not-allowed"
                            >
                                Change Password (Coming Soon)
                            </button>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-semibold text-taxodo-ink">Two-Factor Authentication</label>
                            <p className="text-sm text-taxodo-muted mb-3">Add an extra layer of security to your account</p>
                            <button
                                disabled
                                className="rounded-md border border-taxodo-border bg-white px-4 py-2 text-sm font-medium text-taxodo-muted opacity-50 cursor-not-allowed"
                            >
                                Enable 2FA (Coming Soon)
                            </button>
                        </div>
                    </div>
                </div>

                {/* Company Workspace Card */}
                <div className="taxodo-card taxodo-card-pad lg:col-span-2">
                    <div className="mb-6 flex items-center gap-4">
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
                            <BuildingIcon className="h-6 w-6" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-taxodo-ink font-manrope">Company Workspace</h3>
                            <p className="text-sm text-taxodo-muted">Your organizational details and subscription</p>
                        </div>
                    </div>

                    <div className="grid gap-6 md:grid-cols-3">
                        <div>
                            <label className="mb-2 block text-sm font-semibold text-taxodo-ink">Organization Name</label>
                            <div className="text-lg font-medium text-taxodo-ink">{userProfile.tenant?.name || "Taxodo Enterprise"}</div>
                        </div>
                        <div>
                            <label className="mb-2 flex items-center gap-2 text-sm font-semibold text-taxodo-ink">
                                <CreditCard className="h-4 w-4" />
                                Plan & Billing
                            </label>
                            <div className="flex items-center gap-2">
                                <span className="font-medium text-taxodo-ink">Pro Plan</span>
                                <span className="inline-flex items-center rounded-full bg-taxodo-success/10 px-2 py-1 text-xs font-medium text-taxodo-success">
                                    Active
                                </span>
                            </div>
                        </div>
                        <div>
                            <label className="mb-2 block text-sm font-semibold text-taxodo-ink">Tenant ID</label>
                            <div className="font-mono text-xs text-taxodo-muted">{userProfile.tenant_id}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
