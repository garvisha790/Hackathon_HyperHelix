"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface GSTData {
  period: string;
  output_gst: number;
  input_gst: number;
  net_liability: number;
}

export function GSTTracker({ data }: { data: GSTData[] }) {
  if (!data.length) {
    return <p className="flex h-48 items-center justify-center text-sm text-gray-400">No GST data yet</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="period" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v: number) => `₹${v.toLocaleString("en-IN")}`} />
        <Legend />
        <Bar dataKey="output_gst" name="Output GST" fill="#ef4444" radius={[4, 4, 0, 0]} />
        <Bar dataKey="input_gst" name="Input GST (ITC)" fill="#22c55e" radius={[4, 4, 0, 0]} />
        <Bar dataKey="net_liability" name="Net Liability" fill="#f59e0b" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
