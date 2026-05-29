"use client";

import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { getConfig } from "@/lib/api-client";
import type { AppConfig } from "@/lib/types";

export function KeywordsTab() {
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
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {config?.keyword_groups.map((group) => (
        <Card key={group.name} title={group.name}>
          <p className="text-xs text-muted mb-3">{group.description}</p>
          <div className="flex flex-wrap gap-1.5">
            {group.keywords.map((kw) => (
              <span
                key={kw}
                className="px-2 py-0.5 bg-gray-100 text-xs text-foreground rounded"
              >
                {kw}
              </span>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}
