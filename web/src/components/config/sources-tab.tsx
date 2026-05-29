"use client";

import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { listSources } from "@/lib/api-client";
import type { Source } from "@/lib/types";

export function SourcesTab() {
  const { data: sources, error, isLoading, mutate } = useSWR<Source[]>(
    "sources",
    listSources,
    { revalidateOnFocus: false }
  );

  if (error) return <ErrorState onRetry={() => mutate()} />;

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16" />
        ))}
      </div>
    );
  }

  if (!sources || sources.length === 0) {
    return (
      <Card>
        <p className="text-sm text-muted">暂无数据源配置</p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {sources.map((src) => (
        <Card key={src.id} padding>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">{src.name}</p>
              <p className="text-xs text-muted mt-0.5">
                {src.source_type} · 限速 {src.rate_limit_per_minute}/min
              </p>
            </div>
            <span
              className={`inline-flex items-center gap-1.5 text-xs ${
                src.enabled ? "text-emerald-700" : "text-gray-400"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  src.enabled ? "bg-emerald-500" : "bg-gray-300"
                }`}
              />
              {src.enabled ? "启用" : "禁用"}
            </span>
          </div>
        </Card>
      ))}
    </div>
  );
}
