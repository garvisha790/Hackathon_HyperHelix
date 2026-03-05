"use client";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f97316", "#ec4899", "#6366f1"];

interface ExpenseData {
  category: string;
  amount: number;
  percentage: number;
}

export function ExpensePie({ data }: { data: ExpenseData[] }) {
  if (!data.length) {
    return <p className="flex h-48 items-center justify-center text-sm text-gray-400">No expense data yet</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={data} dataKey="amount" nameKey="category" cx="50%" cy="50%" outerRadius={100} label={({ category, percentage }) => `${percentage}%`}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(v: number) => `₹${v.toLocaleString("en-IN")}`} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
