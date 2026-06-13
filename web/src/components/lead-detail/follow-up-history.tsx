"use client";

import { formatDate } from "@/lib/utils";
import type { FollowUpOut } from "@/lib/types";

interface FollowUpHistoryProps {
  followUps: FollowUpOut[];
  compact?: boolean;
}

export function FollowUpHistory({ followUps, compact }: FollowUpHistoryProps) {
  if (!followUps || followUps.length === 0) {
    return <p className="text-sm text-muted">暂无跟进记录</p>;
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {followUps.map((fu) => (
          <div key={fu.id} className="p-2 bg-bg-muted rounded-lg text-xs">
            <div className="flex items-center justify-between">
              <span className="font-medium text-foreground">{fu.result}</span>
              <span className="text-muted">{formatDate(fu.created_at)}</span>
            </div>
            {fu.notes && <p className="text-muted mt-0.5">{fu.notes}</p>}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {followUps.map((fu) => (
        <div key={fu.id} className="flex items-start gap-3 pb-3 border-b border-border/50 last:border-0">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-cta/10 text-cta text-xs flex items-center justify-center font-medium">
            {fu.channel === "phone" ? "电" : fu.channel === "wechat" ? "微" : "其"}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-foreground">{fu.result}</span>
              <span className="text-xs text-muted">{formatDate(fu.created_at)}</span>
            </div>
            {fu.notes && <p className="text-xs text-muted mt-0.5 truncate">{fu.notes}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}
