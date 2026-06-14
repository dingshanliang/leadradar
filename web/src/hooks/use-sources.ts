"use client";

import useSWR from "swr";
import { listSources } from "@/lib/api-client";
import type { Source } from "@/lib/types";

export function useSources() {
  const { data, error, isLoading, mutate } = useSWR<Source[]>("sources", listSources, {
    revalidateOnFocus: true,
  });
  return { sources: data ?? [], error, isLoading, mutate };
}
