"use client";

import useSWR from "swr";
import { getManualTask, listManualTasks } from "@/lib/api-client";
import type { ManualTaskOut } from "@/lib/types";

export function useManualTasks() {
  const { data, error, isLoading, mutate } = useSWR<ManualTaskOut[]>(
    "manual-tasks",
    listManualTasks,
    { refreshInterval: 3000, revalidateOnFocus: true }
  );
  return { tasks: data ?? [], error, isLoading, mutate };
}

export function useManualTask(taskId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<ManualTaskOut>(
    taskId ? `manual-task:${taskId}` : null,
    () => getManualTask(taskId!),
    { refreshInterval: 3000, revalidateOnFocus: true }
  );
  return { task: data, error, isLoading, mutate };
}
