"use client";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface CashFlowData {
  period: string;
  inflow: number;
  outflow: number;
  net: number;
}

export function CashflowChart({ data }: { data: CashFlowData[] }) {
  if (!data.length) {
    return <p className="flex h-48 items-center justify-center text-sm text-gray-400">No cash flow data yet</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="period" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v: number) => `₹${v.toLocaleString("en-IN")}`} />
        <Legend />
        <Area type="monotone" dataKey="inflow" name="Inflow" stroke="#22c55e" fill="#22c55e" fillOpacity={0.1} />
        <Area type="monotone" dataKey="outflow" name="Outflow" stroke="#ef4444" fill="#ef4444" fillOpacity={0.1} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
