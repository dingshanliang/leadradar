import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/leads/status-badge";
import { formatDate } from "@/lib/utils";
import type { LeadDetail } from "@/lib/types";

interface BasicInfoProps {
  lead: LeadDetail;
}

export function BasicInfo({ lead }: BasicInfoProps) {
  const org = lead.organization;
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-heading text-xl font-bold text-primary">
            {org.name}
          </h2>
          <div className="flex items-center gap-3 mt-2 text-sm text-muted">
            {org.province && <span>{org.province}{org.city ? ` ${org.city}` : ""}{org.county ? ` ${org.county}` : ""}</span>}
            {org.organization_type && <span>{org.organization_type}</span>}
          </div>
        </div>
        <StatusBadge status={lead.lead_status} />
      </div>
      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-border">
        <div>
          <p className="text-xs text-muted">客户类型</p>
          <p className="text-sm font-medium mt-0.5">{lead.customer_type ?? "-"}</p>
        </div>
        <div>
          <p className="text-xs text-muted">预算区间</p>
          <p className="text-sm font-medium mt-0.5">{lead.budget_bucket ?? "-"}</p>
        </div>
        <div>
          <p className="text-xs text-muted">发现时间</p>
          <p className="text-sm font-medium mt-0.5">{formatDate(lead.created_at)}</p>
        </div>
      </div>
    </Card>
  );
}
