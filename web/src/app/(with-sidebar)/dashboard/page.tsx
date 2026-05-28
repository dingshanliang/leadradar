"use client";

import { useMemo } from "react";
import useSWR from "swr";
import { MetricCard } from "@/components/dashboard/metric-card";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listLeads } from "@/lib/api-client";
import { SIGNAL_TYPE_LABELS } from "@/lib/constants";
import type { LeadListItem } from "@/lib/types";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";

const PIE_COLORS = ["#0369A1", "#059669", "#D97706", "#7C3AED", "#EA580C", "#DC2626", "#0F172A"];

export default function DashboardPage() {
  const { data: leads, isLoading } = useSWR<LeadListItem[]>(
    "leads-dashboard",
    () => listLeads({ limit: 200, offset: 0 }),
    { revalidateOnFocus: false }
  );

  const metrics = useMemo(() => {
    if (!leads) return null;
    const total = leads.length;
    const saCount = leads.filter((l) => l.grade === "S" || l.grade === "A").length;
    const pending = leads.filter((l) => l.lead_status === "new" || l.lead_status === "qualified").length;
    const scheduled = leads.filter((l) => l.lead_status === "diagnosis_scheduled").length;
    const invalid = leads.filter((l) => l.lead_status === "invalid").length;
    const invalidRate = total > 0 ? ((invalid / total) * 100).toFixed(1) : "0";
    return { total, saCount, pending, scheduled, invalid, invalidRate };
  }, [leads]);

  const signalTypeData = useMemo(() => {
    if (!leads) return [];
    const counts: Record<string, number> = {};
    leads.forEach((l) => {
      const type = l.signal_type ?? "unknown";
      counts[type] = (counts[type] || 0) + 1;
    });
    return Object.entries(counts)
      .map(([key, count]) => ({ name: SIGNAL_TYPE_LABELS[key] ?? key, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
  }, [leads]);

  const packageData = useMemo(() => {
    if (!leads) return [];
    const counts: Record<string, number> = {};
    leads.forEach((l) => {
      const pkg = l.recommended_package ?? "未分类";
      counts[pkg] = (counts[pkg] || 0) + 1;
    });
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [leads]);

  const provinceData = useMemo(() => {
    if (!leads) return [];
    const counts: Record<string, number> = {};
    leads.forEach((l) => {
      const prov = l.province ?? "未知";
      counts[prov] = (counts[prov] || 0) + 1;
    });
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
  }, [leads]);

  return (
    <div className="px-8 py-6">
      <h1 className="font-heading text-2xl font-bold text-primary mb-1">
        信号看板
      </h1>
      <p className="text-sm text-muted mb-6">数据概览与分布分析</p>

      {isLoading || !metrics ? (
        <div className="grid grid-cols-6 gap-4 mb-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : (
        <>
          {/* Metrics */}
          <div className="grid grid-cols-6 gap-4 mb-6">
            <MetricCard label="线索总数" value={metrics.total} />
            <MetricCard label="S/A 级线索" value={metrics.saCount} trend={metrics.total > 0 ? `${((metrics.saCount / metrics.total) * 100).toFixed(0)}%` : undefined} />
            <MetricCard label="待跟进" value={metrics.pending} />
            <MetricCard label="已预约诊断" value={metrics.scheduled} />
            <MetricCard label="无效线索" value={metrics.invalid} />
            <MetricCard label="无效率" value={`${metrics.invalidRate}%`} />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-2 gap-4">
            <Card title="信号类型分布">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={signalTypeData} layout="vertical" margin={{ left: 80 }}>
                    <XAxis type="number" tick={{ fontSize: 12 }} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#0369A1" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card title="推荐产品包分布">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={packageData}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, percent }: any) => `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {packageData.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card title="地区分布" className="col-span-2">
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={provinceData} margin={{ left: 60 }}>
                    <XAxis type="category" dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis type="number" tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#334155" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
