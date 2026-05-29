"use client";

import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { listFollowUps } from "@/lib/api-client";
import { FollowUpHistory } from "./follow-up-history";
import type { FollowUpOut } from "@/lib/types";

interface FollowUpRecordsProps {
  leadId: string;
}

export function FollowUpRecords({ leadId }: FollowUpRecordsProps) {
  const { data: followUps, error, isLoading, mutate } = useSWR<FollowUpOut[]>(
    `followups-${leadId}`,
    () => listFollowUps(leadId)
  );

  return (
    <Card title="跟进记录">
      {error ? (
        <ErrorState onRetry={() => mutate()} />
      ) : isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : (
        <FollowUpHistory followUps={followUps ?? []} />
      )}
    </Card>
  );
}
