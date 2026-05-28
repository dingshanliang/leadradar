"use client";

import { useState } from "react";
import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listSources, getConfig } from "@/lib/api-client";
import type { Source, AppConfig } from "@/lib/types";

const TABS = [
  { key: "sources", label: "数据源" },
  { key: "keywords", label: "关键词组" },
  { key: "scoring", label: "评分规则" },
  { key: "packages", label: "产品包" },
  { key: "scripts", label: "话术模板" },
];

export default function ConfigPage() {
  const [activeTab, setActiveTab] = useState("sources");
  const { data: sources, isLoading: sourcesLoading } = useSWR<Source[]>(
    "sources",
    listSources,
    { revalidateOnFocus: false }
  );
  const { data: config, isLoading: configLoading } = useSWR<AppConfig>(
    "config",
    getConfig,
    { revalidateOnFocus: false }
  );

  return (
    <div className="px-8 py-6">
      <h1 className="font-heading text-2xl font-bold text-primary mb-1">
        配置
      </h1>
      <p className="text-sm text-muted mb-6">系统配置与参数管理</p>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-white rounded-xl border border-border p-1">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm cursor-pointer transition-colors duration-150 ${
              activeTab === tab.key
                ? "bg-primary text-white font-medium"
                : "text-muted hover:text-foreground hover:bg-gray-50"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === "sources" && (
        <div className="space-y-3">
          {sourcesLoading ? (
            Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16" />)
          ) : !sources || sources.length === 0 ? (
            <Card>
              <p className="text-sm text-muted">暂无数据源配置</p>
            </Card>
          ) : (
            sources.map((src) => (
              <Card key={src.id} padding>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground">{src.name}</p>
                    <p className="text-xs text-muted mt-0.5">
                      {src.source_type} · 限速 {src.rate_limit_per_minute}/min
                    </p>
                  </div>
                  <span className={`inline-flex items-center gap-1.5 text-xs ${src.enabled ? "text-emerald-700" : "text-gray-400"}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${src.enabled ? "bg-emerald-500" : "bg-gray-300"}`} />
                    {src.enabled ? "启用" : "禁用"}
                  </span>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {activeTab === "keywords" && (
        <div className="grid grid-cols-2 gap-4">
          {configLoading ? (
            Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32" />)
          ) : config?.keyword_groups.map((group) => (
            <Card key={group.name} title={group.name}>
              <p className="text-xs text-muted mb-3">{group.description}</p>
              <div className="flex flex-wrap gap-1.5">
                {group.keywords.map((kw) => (
                  <span key={kw} className="px-2 py-0.5 bg-gray-100 text-xs text-foreground rounded">
                    {kw}
                  </span>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}

      {activeTab === "scoring" && (
        <Card>
          {configLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8" />)}
            </div>
          ) : (
            <div className="space-y-4">
              {config?.scoring_dimensions.map((dim) => (
                <div key={dim.name} className="flex items-center gap-4 pb-4 border-b border-border/50 last:border-0">
                  <div className="w-24">
                    <p className="text-sm font-medium text-foreground">{dim.name}</p>
                  </div>
                  <div className="flex-1">
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-cta rounded-full"
                        style={{ width: `${dim.max_score}%` }}
                      />
                    </div>
                  </div>
                  <div className="w-10 text-right">
                    <span className="font-mono text-sm font-bold text-primary">{dim.max_score}</span>
                  </div>
                  <div className="w-48">
                    <p className="text-xs text-muted">{dim.description}</p>
                  </div>
                </div>
              ))}
              <div className="flex justify-end pt-2">
                <p className="text-xs text-muted">总分满分：<span className="font-mono font-bold text-primary">
                  {config?.scoring_dimensions.reduce((sum, d) => sum + d.max_score, 0) ?? 100}
                </span></p>
              </div>
            </div>
          )}
        </Card>
      )}

      {activeTab === "packages" && (
        <div className="grid grid-cols-2 gap-4">
          {configLoading ? (
            Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)
          ) : config?.product_packages.map((pkg) => (
            <Card key={pkg.name} title={pkg.name}>
              <p className="text-xs text-muted mb-1">目标客户：{pkg.target}</p>
              <p className="text-sm text-foreground">{pkg.desc}</p>
            </Card>
          ))}
        </div>
      )}

      {activeTab === "scripts" && (
        <Card>
          <div className="text-center py-8">
            <p className="text-sm text-muted">话术模板由系统根据信号类型自动生成</p>
            <p className="text-xs text-muted mt-1">在线索详情页或工作台查看具体话术</p>
          </div>
        </Card>
      )}
    </div>
  );
}
