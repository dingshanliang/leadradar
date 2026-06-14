"use client";

import useSWR from "swr";
import { getDueFollowUpCount } from "@/lib/api-client";

export const DUE_FOLLOW_UP_COUNT_KEY = "due-follow-up-count";

export function useDueFollowUpCount() {
  const { data, error, isLoading, mutate } = useSWR<
    { count: number },
    Error
  >(DUE_FOLLOW_UP_COUNT_KEY, () => getDueFollowUpCount(), {
    revalidateOnFocus: false,
  });

  return {
    count: data?.count ?? 0,
    error,
    isLoading,
    mutate,
  };
}
