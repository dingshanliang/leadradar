"use client";

import { useState } from "react";
import { TaskForm } from "@/components/manual-tasks/task-form";
import { TaskList } from "@/components/manual-tasks/task-list";
import { TaskDetail } from "@/components/manual-tasks/task-detail";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useManualTask, useManualTasks } from "@/hooks/use-manual-tasks";
import { useSources } from "@/hooks/use-sources";

export default function ManualTasksPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const { tasks, error: tasksError, isLoading: tasksLoading, mutate } = useManualTasks();
  const { task: selectedTask, error: detailError } = useManualTask(selectedTaskId);
  const { sources, isLoading: sourcesLoading } = useSources();

  const handleCreated = (taskId: string) => {
    setSelectedTaskId(taskId);
    mutate();
  };

  return (
    <div className="px-8 py-6">
      <div className="mb-6">
        <h1 className="font-heading text-2xl font-bold text-primary">手动生成线索</h1>
        <p className="text-sm text-muted mt-1">
          选择公开信息渠道，立即采集并生成线索
        </p>
      </div>

      {sourcesLoading ? (
        <Skeleton className="h-40 w-full" />
      ) : sources.length === 0 ? (
        <EmptyState title="无可用渠道" description="请先在配置页添加数据源" />
      ) : (
        <TaskForm sources={sources} onCreated={handleCreated} />
      )}

      <div className="grid grid-cols-12 gap-6 mt-6">
        <div className="col-span-5">
          <h2 className="text-sm font-medium mb-3">任务列表</h2>
          {tasksLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : tasksError ? (
            <ErrorState onRetry={() => mutate()} />
          ) : (
            <TaskList
              tasks={tasks}
              selectedTaskId={selectedTaskId}
              onSelect={setSelectedTaskId}
            />
          )}
        </div>

        <div className="col-span-7">
          <h2 className="text-sm font-medium mb-3">任务详情</h2>
          {!selectedTaskId ? (
            <EmptyState title="未选择任务" description="从左侧选择一项任务查看进度" />
          ) : detailError ? (
            <ErrorState onRetry={() => {}} />
          ) : !selectedTask ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <TaskDetail task={selectedTask} />
          )}
        </div>
      </div>
    </div>
  );
}
