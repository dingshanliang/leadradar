"use client";

import useSWR from "swr";
import { listSources } from "@/lib/api-client";
import type { Source } from "@/lib/types";

export function useSources() {
  const { data, error, isLoading } = useSWR<Source[]>("sources", listSources, {
    revalidateOnFocus: false,
  });
  return { sources: data ?? [], error, isLoading };
}
