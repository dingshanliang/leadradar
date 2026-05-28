"use client";

import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listFollowUps } from "@/lib/api-client";
import { FollowUpHistory } from "./follow-up-history";
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
      ) : (
        <FollowUpHistory followUps={followUps ?? []} />
      )}
    </Card>
  );
}
