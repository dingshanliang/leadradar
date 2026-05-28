"use client";

import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listFollowUps } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";
import type { FollowUpOut } from "@/lib/types";

interface FollowUpRecordsProps {
  leadId: string;
}

export function FollowUpRecords({ leadId }: FollowUpRecordsProps) {
  const { data: followUps, isLoading } = useSWR<FollowUpOut[]>(
    `followups-${leadId}`,
    () => listFollowUps(leadId)
  );

  return (
    <Card title="跟进记录">
      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : !followUps || followUps.length === 0 ? (
        <p className="text-sm text-muted">暂无跟进记录</p>
      ) : (
        <div className="space-y-3">
          {followUps.map((fu) => (
            <div key={fu.id} className="flex items-start gap-3 pb-3 border-b border-border/50 last:border-0">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-cta/10 text-cta text-xs flex items-center justify-center font-medium">
                {fu.channel === "phone" ? "电" : fu.channel === "wechat" ? "微" : "其"}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">
                    {fu.result}
                  </span>
                  <span className="text-xs text-muted">{formatDate(fu.created_at)}</span>
                </div>
                {fu.notes && (
                  <p className="text-xs text-muted mt-0.5 truncate">{fu.notes}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
