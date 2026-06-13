"use client";

import { useState } from "react";
import { exportLeads } from "@/lib/api-client";

interface ExportButtonProps {
  grade?: string;
}

export function ExportButton({ grade }: ExportButtonProps) {
  const [loading, setLoading] = useState(false);
  const [format, setFormat] = useState<"csv" | "xlsx">("csv");

  const handleExport = async (fmt: "csv" | "xlsx") => {
    setLoading(true);
    try {
      await exportLeads(fmt, grade);
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <select
        value={format}
        onChange={(e) => setFormat(e.target.value as "csv" | "xlsx")}
        className="text-xs border border-border rounded-lg px-2 py-1.5 bg-bg-elevated cursor-pointer focus:outline-none"
      >
        <option value="csv">CSV</option>
        <option value="xlsx">Excel</option>
      </select>
      <button
        onClick={() => handleExport(format)}
        disabled={loading}
        className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-bg-elevated border border-border text-foreground hover:bg-bg-muted cursor-pointer transition-colors duration-150 disabled:opacity-50"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        {loading ? "导出中..." : "导出"}
      </button>
    </div>
  );
}
