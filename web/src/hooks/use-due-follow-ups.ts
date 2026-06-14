"use client";

import useSWR from "swr";
import { getDueFollowUps } from "@/lib/api-client";
import type { DueFollowUp } from "@/lib/types";

const DUE_FOLLOW_UPS_KEY = "due-follow-ups";

export function useDueFollowUps() {
  const { data, error, isLoading, mutate } = useSWR<DueFollowUp[], Error>(
    DUE_FOLLOW_UPS_KEY,
    () => getDueFollowUps(),
    { revalidateOnFocus: false }
  );

  return {
    followUps: data ?? [],
    error,
    isLoading,
    mutate,
  };
}
