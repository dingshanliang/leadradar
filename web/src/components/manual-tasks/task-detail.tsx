"use client";

import Link from "next/link";
import type { ManualTaskOut } from "@/lib/types";

interface TaskDetailProps {
  task: ManualTaskOut;
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: "待执行",
    running: "执行中",
    completed: "已完成",
    failed: "失败",
    partial_failed: "部分失败",
  };
  return map[status] ?? status;
}

function subStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: "待执行",
    running: "执行中",
    completed: "完成",
    failed: "失败",
  };
  return map[status] ?? status;
}

export function TaskDetail({ task }: TaskDetailProps) {
  const progress =
    task.total_subtasks > 0
      ? Math.round((task.completed_subtasks / task.total_subtasks) * 100)
      : 0;

  return (
    <div className="space-y-4 p-4 bg-bg-elevated rounded-xl border border-border">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">任务详情</h3>
        <span className="text-xs px-2 py-0.5 rounded-full bg-bg-muted">
          {statusLabel(task.status)}
        </span>
      </div>

      <div>
        <div className="flex justify-between text-xs text-muted mb-1">
          <span>进度</span>
          <span>{task.completed_subtasks} / {task.total_subtasks}</span>
        </div>
        <div className="h-2 bg-bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="p-2 bg-bg-muted rounded-lg">
          <div className="text-lg font-semibold">{task.created_leads_count}</div>
          <div className="text-xs text-muted">新线索</div>
        </div>
        <div className="p-2 bg-bg-muted rounded-lg">
          <div className="text-lg font-semibold">{task.skipped_duplicate_count}</div>
          <div className="text-xs text-muted">跳过重复</div>
        </div>
        <div className="p-2 bg-bg-muted rounded-lg">
          <div className="text-lg font-semibold">
            {task.subtasks.filter((s) => s.status === "failed").length}
          </div>
          <div className="text-xs text-muted">失败</div>
        </div>
      </div>

      {task.error_message && (
        <p className="text-sm text-destructive">{task.error_message}</p>
      )}

      <div className="border-t border-border pt-3">
        <h4 className="text-sm font-medium mb-2">子任务</h4>
        <div className="space-y-1 max-h-64 overflow-auto">
          {task.subtasks.map((sub) => (
            <div
              key={sub.id}
              className="flex items-center justify-between text-sm py-1.5 px-2 rounded bg-bg-muted"
            >
              <span className="truncate flex-1 mr-2" title={sub.query}>
                {sub.query}
              </span>
              <span className="text-xs text-muted whitespace-nowrap">
                {subStatusLabel(sub.status)} · {sub.created_leads_count} 条
              </span>
            </div>
          ))}
        </div>
      </div>

      {task.status === "completed" || task.status === "partial_failed" ? (
        <Link
          href="/"
          className="inline-block text-sm text-primary hover:underline"
        >
          查看新线索 →
        </Link>
      ) : null}
    </div>
  );
}
