import { Badge } from "@/components/ui/badge";
import { GRADE_COLORS } from "@/lib/constants";
import type { Grade } from "@/lib/types";

interface GradeBadgeProps {
  grade: Grade;
}

export function GradeBadge({ grade }: GradeBadgeProps) {
  return <Badge className={GRADE_COLORS[grade]}>{grade}</Badge>;
}
