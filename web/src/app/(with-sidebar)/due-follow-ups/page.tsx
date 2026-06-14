"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useDueFollowUps } from "@/hooks/use-due-follow-ups";
import { formatDueTime } from "@/lib/utils";

export default function DueFollowUpsPage() {
  const router = useRouter();
  const { followUps, error, isLoading, mutate } = useDueFollowUps();

  return (
    <div className="px-8 py-6">
      <div className="mb-6">
        <h1 className="font-heading text-2xl font-bold text-primary">
          到期跟进
        </h1>
        <p className="text-sm text-muted mt-1">
          按到期时间排序，优先处理最紧急的跟进
        </p>
      </div>

      <div className="bg-bg-elevated rounded-xl border border-border p-4">
        {error ? (
          <ErrorState onRetry={() => mutate()} />
        ) : isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : followUps.length === 0 ? (
          <EmptyState title="暂无到期跟进" />
        ) : (
          <ul className="divide-y divide-border">
            {followUps.map((item) => (
              <li
                key={item.follow_up_id}
                className="flex items-center justify-between py-4 px-2"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground truncate">
                    {item.organization_name ?? "未知机构"}
                  </p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted">
                    <span>{formatDueTime(item.next_action_at)}</span>
                    <span className="truncate">{item.result}</span>
                  </div>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => router.push(`/workbench/${item.lead_id}`)}
                >
                  进入工作台
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
