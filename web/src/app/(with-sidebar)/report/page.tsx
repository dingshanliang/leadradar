"use client";

import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { MetricCard } from "@/components/dashboard/metric-card";
import { getWeeklyReport } from "@/lib/api-client";

interface WeeklyData {
  new_leads: number;
  followed_up: number;
  contacted: number;
  scheduled: number;
  won: number;
  lost: number;
  conversion_rate: string;
}

async function fetchWeekly(): Promise<WeeklyData> {
  return getWeeklyReport() as unknown as WeeklyData;
}

export default function ReportPage() {
  const { data, error, isLoading, mutate } = useSWR<WeeklyData>(
    "weekly-report",
    fetchWeekly,
    { revalidateOnFocus: false }
  );

  return (
    <div className="px-8 py-6">
      <h1 className="font-heading text-2xl font-bold text-primary mb-1">
        周报
      </h1>
      <p className="text-sm text-muted mb-6">过去 7 天数据汇总</p>

      {error ? (
        <ErrorState onRetry={() => mutate()} />
      ) : isLoading || !data ? (
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 7 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-4 gap-4 mb-6">
            <MetricCard label="新增线索" value={data.new_leads} />
            <MetricCard label="跟进次数" value={data.followed_up} />
            <MetricCard label="已联系" value={data.contacted} />
            <MetricCard label="已预约" value={data.scheduled} />
            <MetricCard label="已成交" value={data.won} />
            <MetricCard label="已流失" value={data.lost} />
            <MetricCard label="转化率" value={data.conversion_rate} />
          </div>

          <Card title="周报摘要">
            <div className="space-y-2 text-sm">
              <p>本周新增 <span className="font-bold text-primary">{data.new_leads}</span> 条线索，完成 <span className="font-bold text-primary">{data.followed_up}</span> 次跟进。</p>
              <p>联系到决策人 <span className="font-bold text-primary">{data.contacted}</span> 个，预约诊断 <span className="font-bold text-primary">{data.scheduled}</span> 个。</p>
              <p>成交 <span className="font-bold text-emerald-700">{data.won}</span> 个，流失 <span className="font-bold text-red-600">{data.lost}</span> 个，转化率 <span className="font-bold text-primary">{data.conversion_rate}</span>。</p>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
