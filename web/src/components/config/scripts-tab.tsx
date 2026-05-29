"use client";

import { Card } from "@/components/ui/card";

export function ScriptsTab() {
  return (
    <Card>
      <div className="text-center py-8">
        <p className="text-sm text-muted">话术模板由系统根据信号类型自动生成</p>
        <p className="text-xs text-muted mt-1">在线索详情页或工作台查看具体话术</p>
      </div>
    </Card>
  );
}
