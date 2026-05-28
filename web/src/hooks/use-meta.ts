import useSWR from "swr";
import { getMeta } from "@/lib/api-client";
import type { Meta } from "@/lib/types";
import {
  SIGNAL_TYPE_LABELS,
  STATUS_LABELS,
} from "@/lib/constants";

function toLabelMap(items: { key: string; label: string }[]): Record<string, string> {
  const map: Record<string, string> = {};
  for (const item of items) {
    map[item.key] = item.label;
  }
  return map;
}

export function useMeta() {
  const { data: meta } = useSWR<Meta>("meta", getMeta, {
    revalidateOnFocus: false,
    dedupingInterval: 60000,
  });

  const signalTypeLabels = meta
    ? { ...SIGNAL_TYPE_LABELS, ...toLabelMap(meta.signal_types) }
    : SIGNAL_TYPE_LABELS;

  const statusLabels = meta
    ? { ...STATUS_LABELS, ...toLabelMap(meta.statuses) }
    : STATUS_LABELS;

  const grades = meta?.grades ?? ["S", "A", "B", "C", "D"];
  const budgetBuckets = meta?.budget_buckets ?? ["<10万", "10-50万", "50-100万", "100-500万", ">500万"];

  return { signalTypeLabels, statusLabels, grades, budgetBuckets };
}
