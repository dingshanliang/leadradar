"use client";

import { useState } from "react";
import { STATUS_LABELS, STATUS_COLORS } from "@/lib/constants";
import type { LeadStatus } from "@/lib/types";

const ALL_STATUSES: LeadStatus[] = [
  "new", "qualified", "called", "connected",
  "diagnosis_scheduled", "proposal_sent", "won",
  "lost", "invalid", "blocked",
];

interface StatusDropdownProps {
  current: LeadStatus;
  onChange: (status: LeadStatus) => void;
}

export function StatusDropdown({ current, onChange }: StatusDropdownProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium cursor-pointer transition-colors duration-150 ${STATUS_COLORS[current]}`}
      >
        {STATUS_LABELS[current]}
        <svg className="w-3 h-3 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-1 w-36 bg-white border border-border rounded-lg shadow-lg z-20 py-1">
            {ALL_STATUSES.map((s) => (
              <button
                key={s}
                onClick={() => { onChange(s); setOpen(false); }}
                className={`w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 cursor-pointer ${
                  s === current ? "font-medium text-primary" : "text-foreground"
                }`}
              >
                {STATUS_LABELS[s]}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
