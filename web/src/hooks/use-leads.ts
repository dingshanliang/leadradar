"use client";

import useSWR from "swr";
import { listLeads } from "@/lib/api-client";
import type { LeadFilters, LeadListItem } from "@/lib/types";

function leadsKey(filters: LeadFilters): string {
  return `leads:${filters.grade ?? ""}:${filters.status ?? ""}:${filters.signal_type ?? ""}:${filters.limit ?? 50}:${filters.offset ?? 0}`;
}

export function useLeads(filters: LeadFilters) {
  const { data, error, isLoading, mutate } = useSWR<LeadListItem[]>(
    leadsKey(filters),
    () => listLeads(filters),
    { revalidateOnFocus: false }
  );
  return { leads: data ?? [], error, isLoading, mutate };
}
