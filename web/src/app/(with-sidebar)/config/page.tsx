"use client";

import { useState } from "react";
import { SourcesTab } from "@/components/config/sources-tab";
import { KeywordsTab } from "@/components/config/keywords-tab";
import { ScoringTab } from "@/components/config/scoring-tab";
import { PackagesTab } from "@/components/config/packages-tab";
import { ScriptsTab } from "@/components/config/scripts-tab";

const TABS = [
  { key: "sources", label: "数据源", Component: SourcesTab },
  { key: "keywords", label: "关键词组", Component: KeywordsTab },
  { key: "scoring", label: "评分规则", Component: ScoringTab },
  { key: "packages", label: "产品包", Component: PackagesTab },
  { key: "scripts", label: "话术模板", Component: ScriptsTab },
] as const;

export default function ConfigPage() {
  const [activeTab, setActiveTab] = useState("sources");
  const ActiveComponent = TABS.find((t) => t.key === activeTab)?.Component ?? SourcesTab;

  return (
    <div className="px-8 py-6">
      <h1 className="font-heading text-2xl font-bold text-primary mb-1">
        配置
      </h1>
      <p className="text-sm text-muted mb-6">系统配置与参数管理</p>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-bg-elevated rounded-xl border border-border p-1">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm cursor-pointer transition-colors duration-150 ${
              activeTab === tab.key
                ? "bg-primary text-white font-medium"
                : "text-muted hover:text-foreground hover:bg-bg-muted"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <ActiveComponent />
    </div>
  );
}
