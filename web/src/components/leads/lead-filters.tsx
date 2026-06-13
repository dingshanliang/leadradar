"use client";

import { GRADE_COLORS, STATUS_LABELS as FALLBACK_STATUS } from "@/lib/constants";
import { useMeta } from "@/hooks/use-meta";
import type { Grade, LeadFilters, LeadStatus } from "@/lib/types";

const GRADES: Grade[] = ["S", "A", "B", "C", "D"];
const STATUSES: LeadStatus[] = ["new", "qualified", "called", "connected", "diagnosis_scheduled", "proposal_sent", "won", "lost", "invalid", "blocked"];

interface LeadFiltersBarProps {
  filters: LeadFilters;
  onChange: (filters: LeadFilters) => void;
}

export function LeadFiltersBar({ filters, onChange }: LeadFiltersBarProps) {
  const { signalTypeLabels, statusLabels } = useMeta();
  const signalTypes = Object.entries(signalTypeLabels);

  const update = (patch: Partial<LeadFilters>) => {
    onChange({ ...filters, ...patch, offset: 0 });
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Grade */}
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-muted font-medium">等级</span>
        <div className="flex gap-1">
          {GRADES.map((g) => (
            <button
              key={g}
              onClick={() => update({ grade: filters.grade === g ? undefined : g })}
              className={`px-2 py-0.5 rounded text-xs font-medium cursor-pointer transition-colors duration-150 ${
                filters.grade === g
                  ? GRADE_COLORS[g]
                  : "bg-bg-muted text-muted hover:bg-border"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      <div className="w-px h-5 bg-border" />

      {/* Status */}
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-muted font-medium">状态</span>
        <select
          value={filters.status ?? ""}
          onChange={(e) => update({ status: e.target.value || undefined })}
          className="text-xs border border-border rounded-lg px-2 py-1 bg-bg-elevated text-foreground cursor-pointer focus:outline-none focus:ring-1 focus:ring-cta"
        >
          <option value="">全部</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{statusLabels[s] ?? FALLBACK_STATUS[s] ?? s}</option>
          ))}
        </select>
      </div>

      <div className="w-px h-5 bg-border" />

      {/* Signal Type */}
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-muted font-medium">信号</span>
        <select
          value={filters.signal_type ?? ""}
          onChange={(e) => update({ signal_type: e.target.value || undefined })}
          className="text-xs border border-border rounded-lg px-2 py-1 bg-bg-elevated text-foreground cursor-pointer focus:outline-none focus:ring-1 focus:ring-cta"
        >
          <option value="">全部</option>
          {signalTypes.map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {/* Clear */}
      {(filters.grade || filters.status || filters.signal_type) && (
        <button
          onClick={() => onChange({ limit: 50, offset: 0 })}
          className="text-xs text-muted hover:text-foreground cursor-pointer"
        >
          清除筛选
        </button>
      )}
    </div>
  );
}
