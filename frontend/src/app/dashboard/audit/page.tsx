"use client";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Shield } from "lucide-react";

export default function AuditPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => api.get("/audit/logs").then((r) => r.data).catch(() => ({ logs: [] })),
    retry: false,
  });

  const logs = data?.logs || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
        <p className="mt-1 text-sm text-gray-500">Complete trail of all actions taken in the system</p>
      </div>

      {isLoading ? (
        <div className="text-center text-sm text-gray-500">Loading...</div>
      ) : logs.length === 0 ? (
        <div className="rounded-xl border bg-white p-12 text-center">
          <Shield className="mx-auto mb-3 h-12 w-12 text-gray-300" />
          <p className="text-sm text-gray-500">No audit entries yet. Actions will be logged as you use the system.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border bg-white">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Action</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Entity</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Details</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {logs.map((log: any) => (
                <tr key={log.id}>
                  <td className="px-4 py-3 font-medium text-gray-900">{log.action}</td>
                  <td className="px-4 py-3 text-gray-600">{log.entity_type || "—"}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{log.details ? JSON.stringify(log.details) : "—"}</td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(log.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
