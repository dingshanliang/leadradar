import { Suspense } from "react";
import { MetricCard } from "@/components/dashboard/metric-card";
import { SignalTypeChart } from "@/components/dashboard/signal-type-chart";
import { PackagePieChart } from "@/components/dashboard/package-pie-chart";
import { ProvinceBarChart } from "@/components/dashboard/province-bar-chart";
import { Card } from "@/components/ui/card";
import { getServerStats } from "@/lib/server-api";
import { DashboardSkeleton } from "./loading";

export const dynamic = "force-dynamic";

async function DashboardContent() {
  const stats = await getServerStats();

  return (
    <>
      {/* Metrics */}
      <div className="grid grid-cols-6 gap-4 mb-6">
        <MetricCard label="线索总数" value={stats.total} />
        <MetricCard
          label="S/A 级线索"
          value={stats.sa_count}
          trend={
            stats.total > 0
              ? `${((stats.sa_count / stats.total) * 100).toFixed(0)}%`
              : undefined
          }
        />
        <MetricCard label="待跟进" value={stats.pending} />
        <MetricCard label="已预约诊断" value={stats.scheduled} />
        <MetricCard label="无效线索" value={stats.invalid} />
        <MetricCard label="无效率" value={`${stats.invalid_rate}%`} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4">
        <Card title="信号类型分布">
          <div className="h-64">
            <SignalTypeChart data={stats.signal_type_distribution} />
          </div>
        </Card>

        <Card title="推荐产品包分布">
          <div className="h-64">
            <PackagePieChart data={stats.package_distribution} />
          </div>
        </Card>

        <Card title="地区分布" className="col-span-2">
          <div className="h-48">
            <ProvinceBarChart data={stats.province_distribution} />
          </div>
        </Card>
      </div>
    </>
  );
}

export default function DashboardPage() {
  return (
    <div className="px-8 py-6">
      <h1 className="font-heading text-2xl font-bold text-primary mb-1">
        信号看板
      </h1>
      <p className="text-sm text-muted mb-6">数据概览与分布分析</p>

      <Suspense fallback={<DashboardSkeleton />}>
        <DashboardContent />
      </Suspense>
    </div>
  );
}
