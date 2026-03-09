"use client";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#f43f5e", "#8b5cf6", "#06b6d4", "#f97316", "#ec4899", "#3b82f6"];

interface ExpenseData {
  category: string;
  amount: number;
  percentage: number;
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-lg">
      <div className="flex items-center gap-2 mb-1">
        <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: d.payload.fill }} />
        <span className="text-xs font-semibold text-gray-700">{d.name}</span>
      </div>
      <p className="text-sm font-bold text-gray-900">₹{d.value.toLocaleString("en-IN")}</p>
      <p className="text-[11px] text-gray-500">{d.payload.percentage}% of total</p>
    </div>
  );
}

export function ExpensePie({ data }: { data: ExpenseData[] }) {
  if (!data.length) {
    return <p className="flex h-48 items-center justify-center text-sm text-gray-400">No expense data yet</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie data={data} dataKey="amount" nameKey="category" cx="50%" cy="50%"
          innerRadius={60} outerRadius={105} paddingAngle={2}
          label={({ category, percentage }) => `${percentage}%`}
          labelLine={{ stroke: '#d1d5db', strokeWidth: 1 }}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="#fff" strokeWidth={2} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
