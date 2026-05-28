import { Badge } from "@/components/ui/badge";
import { STATUS_LABELS, STATUS_COLORS } from "@/lib/constants";
import type { LeadStatus } from "@/lib/types";

interface StatusBadgeProps {
  status: LeadStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <Badge className={STATUS_COLORS[status]}>
      {STATUS_LABELS[status] ?? status}
    </Badge>
  );
}
