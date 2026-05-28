"use client";

import { useState, useCallback } from "react";
import { LeadTable } from "@/components/leads/lead-table";
import { LeadFiltersBar } from "@/components/leads/lead-filters";
import { ExportButton } from "@/components/leads/export-button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useLeads } from "@/hooks/use-leads";
import type { LeadFilters } from "@/lib/types";

export default function LeadPoolPage() {
  const [filters, setFilters] = useState<LeadFilters>({ limit: 50, offset: 0 });
  const { leads, isLoading, mutate } = useLeads(filters);

  const handleStatusChange = useCallback(() => {
    mutate();
  }, [mutate]);

  return (
    <div className="px-8 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading text-2xl font-bold text-primary">
            线索池
          </h1>
          <p className="text-sm text-muted mt-1">
            按评分排序，快速找到最值得跟进的商机
          </p>
        </div>
        <ExportButton grade={filters.grade} />
      </div>

      {/* Filters */}
      <div className="mb-4 p-4 bg-white rounded-xl border border-border">
        <LeadFiltersBar filters={filters} onChange={setFilters} />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-border p-4">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : leads.length === 0 ? (
          <EmptyState
            title="暂无线索"
            description="开始采集数据后，线索会出现在这里"
          />
        ) : (
          <>
            <LeadTable
              leads={leads}
              onStatusChange={handleStatusChange}
            />
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
              <p className="text-xs text-muted">
                共 {leads.length} 条线索
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() =>
                    setFilters((f) => ({
                      ...f,
                      offset: Math.max(0, (f.offset ?? 0) - (f.limit ?? 50)),
                    }))
                  }
                  disabled={(filters.offset ?? 0) === 0}
                  className="text-xs px-3 py-1.5 rounded-lg border border-border hover:bg-gray-50 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-150"
                >
                  上一页
                </button>
                <button
                  onClick={() =>
                    setFilters((f) => ({
                      ...f,
                      offset: (f.offset ?? 0) + (f.limit ?? 50),
                    }))
                  }
                  disabled={leads.length < (filters.limit ?? 50)}
                  className="text-xs px-3 py-1.5 rounded-lg border border-border hover:bg-gray-50 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-150"
                >
                  下一页
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
