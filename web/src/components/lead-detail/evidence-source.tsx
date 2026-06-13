import { Card } from "@/components/ui/card";
import { CopyButton } from "@/components/ui/copy-button";
import type { SignalBrief } from "@/lib/types";

interface EvidenceSourceProps {
  signal: SignalBrief;
}

export function EvidenceSource({ signal }: EvidenceSourceProps) {
  return (
    <Card title="证据来源">
      <div className="space-y-3">
        {signal.evidence_text && (
          <div className="flex items-start justify-between gap-3 p-3 bg-bg-muted rounded-lg">
            <p className="text-sm text-foreground leading-relaxed">
              {signal.evidence_text}
            </p>
            <CopyButton text={signal.evidence_text} />
          </div>
        )}
        {signal.source_url && (
          <div className="flex items-center gap-2 text-xs text-muted">
            <span>来源：</span>
            <a
              href={signal.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cta hover:text-cta-hover transition-colors duration-150 break-all"
            >
              {signal.source_url}
            </a>
          </div>
        )}
        <div className="flex items-center gap-2 text-xs text-muted">
          <span>置信度：</span>
          <span className="font-mono font-medium text-foreground">
            {(signal.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </Card>
  );
}
