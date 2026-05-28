"use client";

import useSWR from "swr";
import { MetricCard } from "@/components/dashboard/metric-card";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getStats } from "@/lib/api-client";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";

const PIE_COLORS = ["#0369A1", "#059669", "#D97706", "#7C3AED", "#EA580C", "#DC2626", "#0F172A"];

export default function DashboardPage() {
  const { data: stats, isLoading } = useSWR(
    "stats",
    getStats,
    { revalidateOnFocus: false }
  );

  return (
    <div className="px-8 py-6">
      <h1 className="font-heading text-2xl font-bold text-primary mb-1">
        信号看板
      </h1>
      <p className="text-sm text-muted mb-6">数据概览与分布分析</p>

      {isLoading || !stats ? (
        <div className="grid grid-cols-6 gap-4 mb-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : (
        <>
          {/* Metrics */}
          <div className="grid grid-cols-6 gap-4 mb-6">
            <MetricCard label="线索总数" value={stats.total} />
            <MetricCard label="S/A 级线索" value={stats.sa_count} trend={stats.total > 0 ? `${((stats.sa_count / stats.total) * 100).toFixed(0)}%` : undefined} />
            <MetricCard label="待跟进" value={stats.pending} />
            <MetricCard label="已预约诊断" value={stats.scheduled} />
            <MetricCard label="无效线索" value={stats.invalid} />
            <MetricCard label="无效率" value={`${stats.invalid_rate}%`} />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-2 gap-4">
            <Card title="信号类型分布">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.signal_type_distribution} layout="vertical" margin={{ left: 80 }}>
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
                      data={stats.package_distribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      dataKey="count"
                      label={({ name, percent }: any) => `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {stats.package_distribution.map((_, i) => (
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
                  <BarChart data={stats.province_distribution} margin={{ left: 60 }}>
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
