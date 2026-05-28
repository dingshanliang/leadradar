"use client";

import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { BasicInfo } from "@/components/lead-detail/basic-info";
import { ScoreBreakdown } from "@/components/lead-detail/score-breakdown";
import { EvidenceSource } from "@/components/lead-detail/evidence-source";
import { CallOpening } from "@/components/lead-detail/call-opening";
import { FollowUpRecords } from "@/components/lead-detail/follow-up-records";
import { ComplianceNote } from "@/components/lead-detail/compliance-note";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getLeadDetail } from "@/lib/api-client";
import { SIGNAL_TYPE_LABELS } from "@/lib/constants";
import { formatBudget } from "@/lib/utils";
import type { LeadDetail } from "@/lib/types";

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const leadId = params.id as string;

  const { data: lead, isLoading, error } = useSWR<LeadDetail>(
    `lead-${leadId}`,
    () => getLeadDetail(leadId)
  );

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <p className="text-lg font-medium text-foreground">线索未找到</p>
          <p className="text-sm text-muted mt-1">{error.message}</p>
          <Button variant="secondary" className="mt-4" onClick={() => router.push("/")}>
            返回线索池
          </Button>
        </div>
      </div>
    );
  }

  if (isLoading || !lead) {
    return (
      <div className="p-8">
        <Skeleton className="h-8 w-48 mb-6" />
        <Skeleton className="h-32 w-full mb-4" />
        <div className="grid grid-cols-2 gap-4">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      </div>
    );
  }

  const signal = lead.signal;

  return (
    <div className="px-8 py-6 max-w-6xl">
      {/* Back nav */}
      <button
        onClick={() => router.push("/")}
        className="flex items-center gap-1 text-sm text-muted hover:text-foreground mb-4 cursor-pointer transition-colors duration-150"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
        返回线索池
      </button>

      {/* Compliance warning */}
      <ComplianceNote status={lead.lead_status} />

      {/* Basic info */}
      <div className="mt-4">
        <BasicInfo lead={lead} />
      </div>

      {/* Middle row: Score + Signal/Budget + Package */}
      <div className="grid grid-cols-3 gap-4 mt-4">
        <ScoreBreakdown score={lead.score} />
        <Card title="信号摘要">
          <div className="space-y-3">
            <div>
              <p className="text-xs text-muted">信号类型</p>
              <p className="text-sm font-medium mt-0.5">
                {SIGNAL_TYPE_LABELS[signal.signal_type] ?? signal.signal_type}
              </p>
            </div>
            {signal.title && (
              <div>
                <p className="text-xs text-muted">项目名称</p>
                <p className="text-sm font-medium mt-0.5">{signal.title}</p>
              </div>
            )}
            {signal.budget_amount != null && (
              <div>
                <p className="text-xs text-muted">预算金额</p>
                <p className="text-lg font-bold text-primary font-mono mt-0.5">
                  {formatBudget(signal.budget_amount)}
                </p>
              </div>
            )}
          </div>
        </Card>
        <Card title="推荐产品包">
          <p className="text-base font-semibold text-primary">
            {lead.recommended_package ?? "待评估"}
          </p>
          <p className="text-xs text-muted mt-2">
            基于信号类型、预算区间和客户类型自动推荐
          </p>
          <Button
            variant="secondary"
            className="mt-4"
            onClick={() => router.push(`/workbench/${lead.id}`)}
          >
            进入工作台
          </Button>
        </Card>
      </div>

      {/* Evidence */}
      <div className="mt-4">
        <EvidenceSource signal={signal} />
      </div>

      {/* Call script + Follow-ups */}
      <div className="grid grid-cols-2 gap-4 mt-4">
        <CallOpening script={lead.call_script} />
        <FollowUpRecords leadId={lead.id} />
      </div>
    </div>
  );
}
