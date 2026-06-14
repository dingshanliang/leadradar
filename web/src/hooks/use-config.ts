"use client";

import useSWR from "swr";
import { getConfig } from "@/lib/api-client";
import type { AppConfig } from "@/lib/types";

export function useConfig() {
  const { data, error, isLoading, mutate } = useSWR<AppConfig>("config", getConfig, {
    revalidateOnFocus: false,
    dedupingInterval: 60000,
  });
  return { config: data, error, isLoading, mutate };
}
