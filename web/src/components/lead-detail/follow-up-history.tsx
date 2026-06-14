"use client";

import { useState } from "react";
import { cn, formatDate } from "@/lib/utils";
import type { FollowUpOut } from "@/lib/types";

interface FollowUpHistoryProps {
  followUps: FollowUpOut[];
  compact?: boolean;
}

interface FollowUpItem extends FollowUpOut {
  result_category?: string | null;
  reason?: string | null;
}

const NOTES_FOLD_THRESHOLD = 60;

function formatNextActionAt(iso: string | null | undefined): string {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function isOverdue(iso: string): boolean {
  return new Date(iso).getTime() < Date.now();
}

function NotesFolded({
  notes,
  compact,
}: {
  notes: string;
  compact?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const needsFold = notes.length > NOTES_FOLD_THRESHOLD;
  const displayed =
    expanded || !needsFold ? notes : notes.slice(0, NOTES_FOLD_THRESHOLD);

  return (
    <div className={compact ? "mt-1" : "mt-1.5"}>
      <p
        data-testid="follow-up-notes"
        className={cn(
          "text-muted whitespace-pre-wrap",
          compact ? "text-xs" : "text-sm"
        )}
      >
        {displayed}
        {needsFold && !expanded && "…"}
      </p>
      {needsFold && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="text-xs text-cta hover:text-cta-hover mt-0.5 cursor-pointer"
        >
          {expanded ? "收起" : "展开"}
        </button>
      )}
    </div>
  );
}

function HistoryItem({
  fu,
  compact,
}: {
  fu: FollowUpItem;
  compact?: boolean;
}) {
  const categoryTag = fu.result_category?.trim() || null;
  const reasonTag = fu.reason?.trim() || null;
  const legacyResult = !categoryTag && (fu.result?.trim() || null);

  const nextAt = formatNextActionAt(fu.next_action_at);
  const overdue = fu.next_action_at ? isOverdue(fu.next_action_at) : false;

  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-cta/10 text-cta text-xs flex items-center justify-center font-medium">
        {fu.channel === "phone" ? "电" : fu.channel === "wechat" ? "微" : "其"}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          {categoryTag ? (
            <span
              className={cn(
                "inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-cta/10 text-cta",
                compact && "px-1.5 py-0.5"
              )}
            >
              {categoryTag}
            </span>
          ) : legacyResult ? (
            <span className="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-bg-muted text-muted">
              {legacyResult} (legacy)
            </span>
          ) : null}
          {reasonTag ? (
            <span
              className={cn(
                "inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-secondary/10 text-secondary",
                compact && "px-1.5 py-0.5"
              )}
            >
              {reasonTag}
            </span>
          ) : null}
          <span className={cn("text-muted", compact ? "text-[10px]" : "text-xs")}>
            {formatDate(fu.created_at)}
          </span>
        </div>

        {fu.notes ? <NotesFolded notes={fu.notes} compact={compact} /> : null}

        <div
          className={cn(
            "flex items-center gap-2",
            compact ? "mt-1.5 text-xs" : "mt-2 text-sm"
          )}
        >
          <span className="text-muted">下次跟进</span>
          <span
            data-testid="next-action-at"
            className={cn(
              overdue ? "text-danger font-medium" : "text-foreground"
            )}
          >
            {nextAt}
          </span>
        </div>
      </div>
    </div>
  );
}

export function FollowUpHistory({ followUps, compact }: FollowUpHistoryProps) {
  if (!followUps || followUps.length === 0) {
    return <p className="text-sm text-muted">暂无跟进记录</p>;
  }

  const items = followUps as FollowUpItem[];

  if (compact) {
    return (
      <div className="space-y-2">
        {items.map((fu) => (
          <div key={fu.id} className="p-2 bg-bg-muted rounded-lg">
            <HistoryItem fu={fu} compact />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((fu, index) => (
        <div
          key={fu.id}
          className={cn(
            "pb-3 border-b border-border/50 last:border-0 last:pb-0",
            index === 0 ? "pt-0" : "pt-0"
          )}
        >
          <HistoryItem fu={fu} />
        </div>
      ))}
    </div>
  );
}
