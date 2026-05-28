import { Card } from "@/components/ui/card";
import { CopyButton } from "@/components/ui/copy-button";
import type { CallScript } from "@/lib/types";

interface CallOpeningProps {
  script: CallScript;
}

export function CallOpening({ script }: CallOpeningProps) {
  return (
    <Card title="电话话术">
      <div className="space-y-4">
        {/* Opening */}
        <div>
          <p className="text-xs text-muted mb-2">开场白</p>
          <div className="flex items-start justify-between gap-3 p-4 bg-primary/[0.03] rounded-lg border border-primary/10">
            <p className="text-sm text-foreground leading-relaxed">
              {script.opening}
            </p>
            <CopyButton text={script.opening} />
          </div>
        </div>

        {/* Questions */}
        <div>
          <p className="text-xs text-muted mb-2">诊断问题</p>
          <ol className="space-y-2">
            {script.questions.map((q, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-cta/10 text-cta text-xs flex items-center justify-center font-medium">
                  {i + 1}
                </span>
                <span className="text-foreground">{q}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* WeChat follow-up */}
        <div>
          <p className="text-xs text-muted mb-2">微信跟进话术</p>
          <div className="flex items-start justify-between gap-3 p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-foreground">{script.wechat_follow_up}</p>
            <CopyButton text={script.wechat_follow_up} />
          </div>
        </div>
      </div>
    </Card>
  );
}
