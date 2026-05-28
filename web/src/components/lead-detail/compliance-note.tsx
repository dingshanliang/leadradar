import { cn } from "@/lib/utils";
import type { LeadStatus } from "@/lib/types";

interface ComplianceNoteProps {
  status: LeadStatus;
}

export function ComplianceNote({ status }: ComplianceNoteProps) {
  if (status !== "blocked") return null;

  return (
    <div className={cn(
      "rounded-xl border-2 border-red-300 bg-red-50 p-4"
    )}>
      <div className="flex items-center gap-2">
        <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
        <p className="text-sm font-semibold text-red-800">
          此联系人已明确拒绝联系，请勿再次拨打
        </p>
      </div>
      <p className="text-xs text-red-600 mt-1 ml-7">
        该线索已加入屏蔽列表，继续联系将违反合规要求
      </p>
    </div>
  );
}
