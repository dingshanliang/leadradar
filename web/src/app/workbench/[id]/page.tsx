"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useCallback } from "react";
import useSWR from "swr";
import { getLeadDetail, createFollowUp, updateLeadStatus, listFollowUps } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { CopyButton } from "@/components/ui/copy-button";
import { GradeBadge } from "@/components/leads/grade-badge";
import { StatusBadge } from "@/components/leads/status-badge";
import { ErrorState } from "@/components/ui/error-state";
import { CALL_RESULTS } from "@/lib/constants";
import { useMeta } from "@/hooks/use-meta";
import { FollowUpHistory } from "@/components/lead-detail/follow-up-history";
import { formatBudget } from "@/lib/utils";
import { validateLeadStatus } from "@/lib/schemas";
import type { FollowUpOut, Grade, LeadDetail } from "@/lib/types";

export default function WorkbenchPage() {
  const params = useParams();
  const router = useRouter();
  const leadId = params.id as string;

  const { data: lead, error: leadError, isLoading, mutate: mutateLead } = useSWR<LeadDetail>(
    `lead-${leadId}`,
    () => getLeadDetail(leadId)
  );
  const { data: followUps, error: followUpsError, mutate: mutateFollowUps } = useSWR<FollowUpOut[]>(
    `followups-${leadId}`,
    () => listFollowUps(leadId)
  );

  const { signalTypeLabels } = useMeta();
  const [channel, setChannel] = useState("phone");
  const [result, setResult] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = useCallback(async () => {
    if (!result) return;
    setSubmitting(true);
    try {
      const selected = CALL_RESULTS.find((r) => r.value === result);
      await createFollowUp(leadId, { channel, result, notes: notes || undefined });
      if (selected) {
        await updateLeadStatus(leadId, selected.status);
      }
      setResult("");
      setNotes("");
      mutateFollowUps();
      mutateLead();
    } catch (err) {
      console.error("Failed to submit follow-up:", err);
    } finally {
      setSubmitting(false);
    }
  }, [leadId, channel, result, notes, mutateFollowUps, mutateLead]);

  if (leadError) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <ErrorState onRetry={() => mutateLead()} />
      </div>
    );
  }

  if (isLoading || !lead) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-cta border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-muted mt-3">加载中...</p>
        </div>
      </div>
    );
  }

  const script = lead.call_script;
  const signal = lead.signal;
  const org = lead.organization;
  const statusResult = validateLeadStatus(lead.lead_status);

  return (
    <div className="flex min-h-screen">
      {/* Left Panel: Customer Info */}
      <div className="w-80 border-r border-border bg-bg-elevated p-6 overflow-y-auto flex-shrink-0">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-xs text-muted hover:text-foreground mb-6 cursor-pointer"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
          返回
        </button>

        <div className="space-y-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="font-heading text-lg font-bold text-primary">{org.name}</h2>
              <GradeBadge grade={lead.score.grade as Grade} />
            </div>
            {statusResult.success && <StatusBadge status={statusResult.data} />}
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted">信号类型</span>
              <span className="font-medium">{signalTypeLabels[signal.signal_type] ?? signal.signal_type}</span>
            </div>
            {signal.budget_amount != null && (
              <div className="flex justify-between">
                <span className="text-muted">预算金额</span>
                <span className="font-mono font-bold text-primary">{formatBudget(signal.budget_amount)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-muted">推荐产品包</span>
              <span className="font-medium text-xs">{lead.recommended_package ?? "-"}</span>
            </div>
          </div>

          {/* Evidence */}
          {signal.evidence_text && (
            <div className="p-3 bg-bg-muted rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-medium text-secondary">证据</p>
                <CopyButton text={signal.evidence_text} />
              </div>
              <p className="text-xs text-foreground leading-relaxed">{signal.evidence_text}</p>
            </div>
          )}

          {signal.source_url && (
            <a
              href={signal.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-xs text-cta hover:text-cta-hover break-all"
            >
              查看原始公告 →
            </a>
          )}
        </div>
      </div>

      {/* Center Panel: Call Script */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Opening */}
          <div>
            <h3 className="text-sm font-semibold text-secondary mb-3 uppercase tracking-wide">
              开场白
            </h3>
            <div className="p-5 bg-primary/[0.03] rounded-xl border border-primary/10">
              <p className="text-base text-foreground leading-relaxed">{script.opening}</p>
              <div className="mt-3">
                <CopyButton text={script.opening} label="复制开场白" />
              </div>
            </div>
          </div>

          {/* Questions */}
          <div>
            <h3 className="text-sm font-semibold text-secondary mb-3 uppercase tracking-wide">
              诊断问题
            </h3>
            <ol className="space-y-3">
              {script.questions.map((q, i) => (
                <li key={i} className="flex items-start gap-3 p-3 bg-bg-elevated rounded-lg border border-border">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cta text-white text-xs flex items-center justify-center font-medium">
                    {i + 1}
                  </span>
                  <span className="text-sm text-foreground leading-relaxed">{q}</span>
                </li>
              ))}
            </ol>
          </div>

          {/* WeChat follow-up */}
          <div>
            <h3 className="text-sm font-semibold text-secondary mb-3 uppercase tracking-wide">
              微信跟进
            </h3>
            <div className="p-4 bg-bg-elevated rounded-lg border border-border">
              <p className="text-sm text-foreground">{script.wechat_follow_up}</p>
              <div className="mt-2">
                <CopyButton text={script.wechat_follow_up} label="复制话术" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel: Follow-up Form */}
      <div className="w-80 border-l border-border bg-bg-elevated p-6 overflow-y-auto flex-shrink-0">
        <h3 className="text-sm font-semibold text-secondary mb-4 uppercase tracking-wide">
          跟进记录
        </h3>

        {/* Form */}
        <div className="space-y-3">
          <div>
            <label className="text-xs text-muted block mb-1">渠道</label>
            <select
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="w-full text-sm border border-border rounded-lg px-3 py-2 bg-bg-elevated cursor-pointer focus:outline-none focus:ring-1 focus:ring-cta"
            >
              <option value="phone">电话</option>
              <option value="wechat">微信</option>
              <option value="email">邮件</option>
              <option value="other">其他</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-muted block mb-1">通话结果</label>
            <select
              value={result}
              onChange={(e) => setResult(e.target.value)}
              className="w-full text-sm border border-border rounded-lg px-3 py-2 bg-bg-elevated cursor-pointer focus:outline-none focus:ring-1 focus:ring-cta"
            >
              <option value="">请选择...</option>
              {CALL_RESULTS.map((r) => (
                <option key={r.value} value={r.value}>{r.value}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-muted block mb-1">备注</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full text-sm border border-border rounded-lg px-3 py-2 bg-bg-elevated resize-none focus:outline-none focus:ring-1 focus:ring-cta"
              placeholder="记录关键信息..."
            />
          </div>

          <Button
            onClick={handleSubmit}
            disabled={!result || submitting}
            className="w-full"
          >
            {submitting ? "提交中..." : "提交跟进"}
          </Button>
        </div>

        {/* History */}
        {followUpsError ? (
          <div className="mt-6 pt-4 border-t border-border">
            <p className="text-xs text-muted mb-3">历史跟进</p>
            <ErrorState message="跟进记录加载失败" onRetry={() => mutateFollowUps()} />
          </div>
        ) : followUps && followUps.length > 0 ? (
          <div className="mt-6 pt-4 border-t border-border">
            <p className="text-xs text-muted mb-3">历史跟进</p>
            <FollowUpHistory followUps={followUps} compact />
          </div>
        ) : null}
      </div>
    </div>
  );
}
