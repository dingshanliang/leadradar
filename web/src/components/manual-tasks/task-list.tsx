"use client";

import type { ManualTaskOut } from "@/lib/types";

interface TaskListProps {
  tasks: ManualTaskOut[];
  selectedTaskId: string | null;
  onSelect: (taskId: string) => void;
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

export function TaskList({ tasks, selectedTaskId, onSelect }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <p className="text-sm text-muted py-4">暂无手动生成任务</p>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <button
          key={task.id}
          onClick={() => onSelect(task.id)}
          className={`w-full text-left p-3 rounded-lg border transition-colors ${
            selectedTaskId === task.id
              ? "border-primary bg-primary/[0.06]"
              : "border-border hover:bg-bg-muted"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">
              {new Date(task.created_at).toLocaleString("zh-CN")}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-bg-muted">
              {statusLabel(task.status)}
            </span>
          </div>
          <div className="mt-1 text-xs text-muted">
            渠道 {task.total_subtasks} 个查询 · 生成 {task.created_leads_count} 条 · 跳过 {task.skipped_duplicate_count} 条
          </div>
        </button>
      ))}
    </div>
  );
}
