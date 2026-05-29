"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import type { DistributionItem } from "@/lib/types";

interface ProvinceBarChartProps {
  data: DistributionItem[];
}

export function ProvinceBarChart({ data }: ProvinceBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ left: 60 }}>
        <XAxis type="category" dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis type="number" tick={{ fontSize: 12 }} />
        <Tooltip />
        <Bar dataKey="count" fill="#334155" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
