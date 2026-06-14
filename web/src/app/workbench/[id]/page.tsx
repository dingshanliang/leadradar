"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useMemo, useRef, useState } from "react";
import useSWR, { mutate as globalMutate } from "swr";
import {
  createFollowUp,
  getLeadDetail,
  getMeta,
  listFollowUps,
  updateLeadStatus,
} from "@/lib/api-client";
import { DUE_FOLLOW_UP_COUNT_KEY } from "@/hooks/use-due-follow-up-count";
import { Button } from "@/components/ui/button";
import { CopyButton } from "@/components/ui/copy-button";
import { GradeBadge } from "@/components/leads/grade-badge";
import { StatusBadge } from "@/components/leads/status-badge";
import { ErrorState } from "@/components/ui/error-state";
import {
  CALL_RESULT_CATEGORIES,
  FOLLOW_UP_SUGGESTIONS,
  SIGNAL_TYPE_LABELS,
} from "@/lib/constants";
import { FollowUpHistory } from "@/components/lead-detail/follow-up-history";
import {
  formatBudget,
  formatDateTimeLocal,
  parseSuggestionDuration,
} from "@/lib/utils";
import { validateLeadStatus } from "@/lib/schemas";
import type { FollowUpOut, Grade, LeadDetail } from "@/lib/types";

interface CallResultsMeta {
  call_results?: Record<string, { reasons: string[] }>;
  follow_up_suggestions?: Record<string, string>;
}

export default function WorkbenchPage() {
  const params = useParams();
  const router = useRouter();
  const leadId = params.id as string;

  const { data: lead, error: leadError, isLoading, mutate: mutateLead } =
    useSWR<LeadDetail>(`lead-${leadId}`, () => getLeadDetail(leadId));
  const {
    data: followUps,
    error: followUpsError,
    mutate: mutateFollowUps,
  } = useSWR<FollowUpOut[]>(`followups-${leadId}`, () => listFollowUps(leadId));
  const { data: meta } = useSWR<CallResultsMeta>("meta", async () =>
    getMeta() as Promise<CallResultsMeta>
  );

  const callResults = useMemo(
    () => meta?.call_results ?? CALL_RESULT_CATEGORIES,
    [meta]
  );
  const followUpSuggestions = useMemo(
    () => meta?.follow_up_suggestions ?? FOLLOW_UP_SUGGESTIONS,
    [meta]
  );

  const [channel, setChannel] = useState("phone");
  const [category, setCategory] = useState("");
  const [reason, setReason] = useState("");
  const [nextActionAt, setNextActionAt] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const submittingRef = useRef(false);

  const categories = useMemo(() => Object.keys(callResults), [callResults]);
  const reasons = useMemo(
    () => (category ? callResults[category]?.reasons ?? [] : []),
    [category, callResults]
  );

  const applySuggestion = useCallback(
    (cat: string) => {
      const rule = followUpSuggestions[cat];
      if (!rule) return;
      const ms = parseSuggestionDuration(rule);
      if (ms == null) return;
      setNextActionAt(formatDateTimeLocal(new Date(Date.now() + ms)));
    },
    [followUpSuggestions]
  );

  const handleCategoryChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const cat = e.target.value;
      setCategory(cat);
      setReason("");
      setFormError("");
      if (cat) applySuggestion(cat);
    },
    [applySuggestion]
  );

  const handleReasonChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const value = e.target.value;
      setReason(value);
      if (value) setFormError("");
    },
    []
  );

  const handleSubmit = useCallback(async () => {
    if (submittingRef.current) return;
    if (!category) return;
    if (!reason) {
      setFormError("请选择具体原因");
      return;
    }

    submittingRef.current = true;
    setSubmitting(true);
    setFormError("");

    try {
      const mappedStatus =
        CALL_RESULT_CATEGORIES[category as keyof typeof CALL_RESULT_CATEGORIES]
          ?.status;

      await createFollowUp(leadId, {
        channel,
        result_category: category,
        reason,
        notes: notes || undefined,
        next_action_at: nextActionAt || undefined,
      });

      if (mappedStatus) {
        await updateLeadStatus(leadId, mappedStatus);
      }

      setChannel("phone");
      setCategory("");
      setReason("");
      setNotes("");
      setNextActionAt("");
      mutateFollowUps();
      mutateLead();
      globalMutate(DUE_FOLLOW_UP_COUNT_KEY);
    } catch (err) {
      const message = err instanceof Error ? err.message : "提交失败，请重试";
      setFormError(message);
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }, [
    leadId,
    channel,
    category,
    reason,
    notes,
    nextActionAt,
    mutateFollowUps,
    mutateLead,
  ]);

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
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M15.75 19.5L8.25 12l7.5-7.5"
            />
          </svg>
          返回
        </button>

        <div className="space-y-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="font-heading text-lg font-bold text-primary">
                {org.name}
              </h2>
              <GradeBadge grade={lead.score.grade as Grade} />
            </div>
            {statusResult.success && <StatusBadge status={statusResult.data} />}
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted">信号类型</span>
              <span className="font-medium">
                {SIGNAL_TYPE_LABELS[signal.signal_type] ?? signal.signal_type}
              </span>
            </div>
            {signal.budget_amount != null && (
              <div className="flex justify-between">
                <span className="text-muted">预算金额</span>
                <span className="font-mono font-bold text-primary">
                  {formatBudget(signal.budget_amount)}
                </span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-muted">推荐产品包</span>
              <span className="font-medium text-xs">
                {lead.recommended_package ?? "-"}
              </span>
            </div>
          </div>

          {/* Evidence */}
          {signal.evidence_text && (
            <div className="p-3 bg-bg-muted rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-medium text-secondary">证据</p>
                <CopyButton text={signal.evidence_text} />
              </div>
              <p className="text-xs text-foreground leading-relaxed">
                {signal.evidence_text}
              </p>
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
              <p className="text-base text-foreground leading-relaxed">
                {script.opening}
              </p>
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
                <li
                  key={i}
                  className="flex items-start gap-3 p-3 bg-bg-elevated rounded-lg border border-border"
                >
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cta text-white text-xs flex items-center justify-center font-medium">
                    {i + 1}
                  </span>
                  <span className="text-sm text-foreground leading-relaxed">
                    {q}
                  </span>
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
            <label htmlFor="channel" className="text-xs text-muted block mb-1">
              渠道
            </label>
            <select
              id="channel"
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
            <label
              htmlFor="result-category"
              className="text-xs text-muted block mb-1"
            >
              结果类别
            </label>
            <select
              id="result-category"
              value={category}
              onChange={handleCategoryChange}
              className="w-full text-sm border border-border rounded-lg px-3 py-2 bg-bg-elevated cursor-pointer focus:outline-none focus:ring-1 focus:ring-cta"
            >
              <option value="">请选择...</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="reason" className="text-xs text-muted block mb-1">
              具体原因
            </label>
            <select
              id="reason"
              value={reason}
              onChange={handleReasonChange}
              disabled={!category}
              className="w-full text-sm border border-border rounded-lg px-3 py-2 bg-bg-elevated cursor-pointer focus:outline-none focus:ring-1 focus:ring-cta disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">
                {category ? "请选择..." : "请先选择结果类别"}
              </option>
              {reasons.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="next-action-at"
              className="text-xs text-muted block mb-1"
            >
              下次跟进时间
            </label>
            <input
              id="next-action-at"
              type="datetime-local"
              step={3600}
              value={nextActionAt}
              onChange={(e) => setNextActionAt(e.target.value)}
              className="w-full text-sm border border-border rounded-lg px-3 py-2 bg-bg-elevated focus:outline-none focus:ring-1 focus:ring-cta"
            />
          </div>

          <div>
            <label htmlFor="notes" className="text-xs text-muted block mb-1">
              备注
            </label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full text-sm border border-border rounded-lg px-3 py-2 bg-bg-elevated resize-none focus:outline-none focus:ring-1 focus:ring-cta"
              placeholder="记录关键信息..."
            />
          </div>

          {formError && (
            <p className="text-xs text-danger" role="alert">
              {formError}
            </p>
          )}

          <Button
            onClick={handleSubmit}
            disabled={!category || submitting}
            className="w-full"
          >
            {submitting ? "提交中..." : "提交跟进"}
          </Button>
        </div>

        {/* History */}
        {followUpsError ? (
          <div className="mt-6 pt-4 border-t border-border">
            <p className="text-xs text-muted mb-3">历史跟进</p>
            <ErrorState
              message="跟进记录加载失败"
              onRetry={() => mutateFollowUps()}
            />
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
