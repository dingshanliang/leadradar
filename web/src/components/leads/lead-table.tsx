"use client";

import Link from "next/link";
import { GradeBadge } from "./grade-badge";
import { StatusDropdown } from "./status-dropdown";
import { SIGNAL_TYPE_LABELS } from "@/lib/constants";
import { formatDate } from "@/lib/utils";
import { updateLeadStatus } from "@/lib/api-client";
import type { LeadListItem, LeadStatus } from "@/lib/types";

interface LeadTableProps {
  leads: LeadListItem[];
  onStatusChange?: () => void;
}

export function LeadTable({ leads, onStatusChange }: LeadTableProps) {
  const handleStatusChange = async (leadId: string, status: LeadStatus) => {
    await updateLeadStatus(leadId, status);
    onStatusChange?.();
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left">
            <th className="pb-3 pr-4 font-medium text-muted text-xs">分数</th>
            <th className="pb-3 pr-4 font-medium text-muted text-xs">等级</th>
            <th className="pb-3 pr-4 font-medium text-muted text-xs">客户名称</th>
            <th className="pb-3 pr-4 font-medium text-muted text-xs">信号类型</th>
            <th className="pb-3 pr-4 font-medium text-muted text-xs">预算区间</th>
            <th className="pb-3 pr-4 font-medium text-muted text-xs">推荐产品包</th>
            <th className="pb-3 pr-4 font-medium text-muted text-xs">状态</th>
            <th className="pb-3 pr-4 font-medium text-muted text-xs">时间</th>
            <th className="pb-3 font-medium text-muted text-xs">操作</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr
              key={lead.id}
              className="border-b border-border/50 hover:bg-gray-50/50 transition-colors duration-100"
            >
              <td className="py-3.5 pr-4">
                <span className="font-mono text-sm font-semibold text-primary">
                  {lead.total_score}
                </span>
              </td>
              <td className="py-3.5 pr-4">
                <GradeBadge grade={lead.grade} />
              </td>
              <td className="py-3.5 pr-4">
                <Link
                  href={`/leads/${lead.id}`}
                  className="text-foreground hover:text-cta font-medium transition-colors duration-150"
                >
                  {lead.organization_name ?? "-"}
                </Link>
              </td>
              <td className="py-3.5 pr-4 text-muted text-xs">
                {lead.signal_type ? (SIGNAL_TYPE_LABELS[lead.signal_type] ?? lead.signal_type) : "-"}
              </td>
              <td className="py-3.5 pr-4 text-xs">
                {lead.budget_bucket ?? "-"}
              </td>
              <td className="py-3.5 pr-4 text-xs text-muted max-w-[160px] truncate">
                {lead.recommended_package ?? "-"}
              </td>
              <td className="py-3.5 pr-4">
                <StatusDropdown
                  current={lead.lead_status}
                  onChange={(s) => handleStatusChange(lead.id, s)}
                />
              </td>
              <td className="py-3.5 pr-4 text-xs text-muted whitespace-nowrap">
                {formatDate(lead.created_at)}
              </td>
              <td className="py-3.5">
                <Link
                  href={`/workbench/${lead.id}`}
                  className="inline-flex items-center gap-1 text-xs text-cta hover:text-cta-hover font-medium transition-colors duration-150"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
                  </svg>
                  工作台
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
