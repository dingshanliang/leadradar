import { Card } from "@/components/ui/card";
import { GradeBadge } from "@/components/leads/grade-badge";
import type { ScoreBrief } from "@/lib/types";

interface ScoreBreakdownProps {
  score: ScoreBrief;
}

const DIMENSIONS = [
  { key: "budget_strength_score", label: "预算强度", max: 35 },
  { key: "scenario_fit_score", label: "场景匹配", max: 25 },
  { key: "timing_score", label: "时间窗口", max: 20 },
  { key: "reachability_score", label: "可触达性", max: 10 },
  { key: "leverage_score", label: "成交杠杆", max: 10 },
] as const;

export function ScoreBreakdown({ score }: ScoreBreakdownProps) {
  return (
    <Card title="评分明细">
      <div className="flex items-center gap-3 mb-4">
        <span className="font-mono text-3xl font-bold text-primary">
          {score.total_score}
        </span>
        <GradeBadge grade={score.grade as any} />
      </div>
      <div className="space-y-3">
        {DIMENSIONS.map((dim) => {
          const value = score[dim.key];
          const pct = Math.round((value / dim.max) * 100);
          return (
            <div key={dim.key}>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-muted">{dim.label}</span>
                <span className="font-mono font-medium text-foreground">
                  {value}/{dim.max}
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-cta rounded-full transition-all duration-500"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
