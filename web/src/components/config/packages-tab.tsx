"use client";

import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { getConfig } from "@/lib/api-client";
import type { AppConfig } from "@/lib/types";

export function PackagesTab() {
  const { data: config, error, isLoading, mutate } = useSWR<AppConfig>(
    "config",
    getConfig,
    { revalidateOnFocus: false }
  );

  if (error) return <ErrorState onRetry={() => mutate()} />;

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {config?.product_packages.map((pkg) => (
        <Card key={pkg.name} title={pkg.name}>
          <p className="text-xs text-muted mb-1">目标客户：{pkg.target}</p>
          <p className="text-sm text-foreground">{pkg.desc}</p>
        </Card>
      ))}
    </div>
  );
}
