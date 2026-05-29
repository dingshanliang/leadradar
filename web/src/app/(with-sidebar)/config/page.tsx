"use client";

import { useState, useMemo, useCallback } from "react";
import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listSources, getConfig, getScoringConfig, updateScoringConfig } from "@/lib/api-client";
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
  const {
    data: scoringConfig,
    isLoading: scoringLoading,
    mutate: mutateScoring,
  } = useSWR<Record<string, unknown>>("scoring-config", getScoringConfig, {
    revalidateOnFocus: false,
  });

  const [isEditingScoring, setIsEditingScoring] = useState(false);
  const [editedScoring, setEditedScoring] = useState<Record<string, unknown> | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const dimNames: Record<string, string> = {
    budget_strength: "预算强度",
    scenario_fit: "场景匹配",
    timing: "时间窗口",
    reachability: "可触达性",
    leverage: "成交杠杆",
  };

  const gradeOrder = ["S", "A", "B", "C", "D"];

  const validationErrors = useMemo(() => {
    const errors: string[] = [];
    if (!editedScoring) return errors;

    const maxScores = editedScoring.max_scores as Record<string, number> | undefined;
    if (maxScores) {
      const total = Object.values(maxScores).reduce((sum, v) => sum + (Number(v) || 0), 0);
      if (total !== 100) {
        errors.push(`维度权重总和必须等于 100，当前为 ${total}`);
      }
    }

    const grades = editedScoring.grades as Record<string, number> | undefined;
    if (grades) {
      const values = gradeOrder.map((g) => Number(grades[g]) || 0);
      for (let i = 0; i < values.length - 1; i++) {
        if (values[i] <= values[i + 1]) {
          errors.push(`等级阈值必须严格递减: ${gradeOrder[i]}(${values[i]}) 应大于 ${gradeOrder[i + 1]}(${values[i + 1]})`);
        }
      }
    }

    const dimensions = ["budget_strength", "scenario_fit", "timing", "reachability", "leverage"];
    for (const dim of dimensions) {
      const maxVal = maxScores?.[dim];
      const subScores = editedScoring[dim] as Record<string, number> | undefined;
      if (subScores && maxVal !== undefined) {
        for (const [key, val] of Object.entries(subScores)) {
          if (Number(val) > Number(maxVal)) {
            errors.push(`${dimNames[dim] || dim}.${key} 的分值 ${val} 超过了该维度满分 ${maxVal}`);
          }
        }
      }
    }

    return errors;
  }, [editedScoring]);

  const isValid = validationErrors.length === 0;

  const startEditing = useCallback(() => {
    if (scoringConfig) {
      setEditedScoring(JSON.parse(JSON.stringify(scoringConfig)));
      setIsEditingScoring(true);
      setSaveError(null);
    }
  }, [scoringConfig]);

  const cancelEditing = useCallback(() => {
    setIsEditingScoring(false);
    setEditedScoring(null);
    setSaveError(null);
  }, []);

  const handleSave = useCallback(async () => {
    if (!editedScoring || !isValid) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      await updateScoringConfig(editedScoring);
      await mutateScoring();
      setIsEditingScoring(false);
      setEditedScoring(null);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setIsSaving(false);
    }
  }, [editedScoring, isValid, mutateScoring]);

  const updateMaxScore = (dim: string, value: string) => {
    setEditedScoring((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      next.max_scores = { ...(next.max_scores as Record<string, number>), [dim]: Number(value) || 0 };
      return next;
    });
  };

  const updateGrade = (grade: string, value: string) => {
    setEditedScoring((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      next.grades = { ...(next.grades as Record<string, number>), [grade]: Number(value) || 0 };
      return next;
    });
  };

  const updateSubScore = (dim: string, key: string, value: string) => {
    setEditedScoring((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      next[dim] = { ...(next[dim] as Record<string, number>), [key]: Number(value) || 0 };
      return next;
    });
  };

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
        <div className="space-y-4">
          {/* Action bar */}
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-medium text-foreground">评分规则配置</h2>
            {isEditingScoring ? (
              <div className="flex gap-2">
                <button
                  onClick={cancelEditing}
                  className="px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-gray-50 transition-colors"
                  disabled={isSaving}
                >
                  取消
                </button>
                <button
                  onClick={handleSave}
                  disabled={!isValid || isSaving}
                  className={`px-3 py-1.5 text-sm rounded-lg text-white transition-colors ${
                    isValid && !isSaving
                      ? "bg-primary hover:bg-primary/90"
                      : "bg-gray-300 cursor-not-allowed"
                  }`}
                >
                  {isSaving ? "保存中..." : "保存"}
                </button>
              </div>
            ) : (
              <button
                onClick={startEditing}
                className="px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-gray-50 transition-colors"
              >
                编辑
              </button>
            )}
          </div>

          {/* Validation errors */}
          {validationErrors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 space-y-1">
              {validationErrors.map((err) => (
                <p key={err} className="text-sm text-red-600">
                  {err}
                </p>
              ))}
            </div>
          )}

          {/* Save error */}
          {saveError && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-sm text-red-600">{saveError}</p>
            </div>
          )}

          {scoringLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : (
            <>
              {/* Max Scores */}
              <Card title="维度权重">
                <div className="space-y-3">
                  {scoringConfig?.max_scores != null ? (
                    Object.entries(scoringConfig.max_scores as Record<string, number>).map(
                      ([key, val]) => (
                        <div key={key} className="flex items-center gap-4">
                          <div className="w-24">
                            <p className="text-sm text-foreground">{dimNames[key] || key}</p>
                          </div>
                          {isEditingScoring && editedScoring ? (
                            <input
                              type="number"
                              min={0}
                              max={100}
                              value={
                                (editedScoring.max_scores as Record<string, number>)?.[key] ?? val
                              }
                              onChange={(e) => updateMaxScore(key, e.target.value)}
                              className="w-20 px-2 py-1 text-sm border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                            />
                          ) : (
                            <div className="flex-1">
                              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-cta rounded-full"
                                  style={{ width: `${val}%` }}
                                />
                              </div>
                            </div>
                          )}
                          <div className="w-10 text-right">
                            <span className="font-mono text-sm font-bold text-primary">
                              {isEditingScoring && editedScoring
                                ? (editedScoring.max_scores as Record<string, number>)?.[key] ?? val
                                : val}
                            </span>
                          </div>
                        </div>
                      )
                    )
                  ) : null}
                  <div className="flex justify-end pt-2 border-t border-border/50">
                    <p className="text-xs text-muted">
                      权重总和：
                      <span className="font-mono font-bold text-primary">
                        {isEditingScoring && editedScoring
                          ? Object.values(
                              (editedScoring.max_scores as Record<string, number>) || {}
                            ).reduce((sum, v) => sum + (Number(v) || 0), 0)
                          : Object.values(
                              (scoringConfig?.max_scores as Record<string, number>) || {}
                            ).reduce((sum, v) => sum + (Number(v) || 0), 0)}
                      </span>
                      / 100
                    </p>
                  </div>
                </div>
              </Card>

              {/* Grades */}
              <Card title="等级阈值">
                <div className="flex gap-4">
                  {gradeOrder.map((g) => {
                    const grades = isEditingScoring && editedScoring
                      ? (editedScoring.grades as Record<string, number>)
                      : (scoringConfig?.grades as Record<string, number>);
                    const value = grades?.[g] ?? 0;
                    return (
                      <div key={g} className="flex-1">
                        <div className="text-center mb-2">
                          <span
                            className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                              g === "S"
                                ? "bg-emerald-100 text-emerald-700"
                                : g === "A"
                                ? "bg-blue-100 text-blue-700"
                                : g === "B"
                                ? "bg-amber-100 text-amber-700"
                                : g === "C"
                                ? "bg-orange-100 text-orange-700"
                                : "bg-gray-100 text-gray-500"
                            }`}
                          >
                            {g}
                          </span>
                        </div>
                        {isEditingScoring && editedScoring ? (
                          <input
                            type="number"
                            min={0}
                            max={100}
                            value={value}
                            onChange={(e) => updateGrade(g, e.target.value)}
                            disabled={g === "D"}
                            className="w-full px-2 py-1 text-sm text-center border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary disabled:bg-gray-50 disabled:text-gray-400"
                          />
                        ) : (
                          <p className="text-center font-mono text-sm font-bold text-primary">
                            {value}
                          </p>
                        )}
                        <p className="text-center text-xs text-muted mt-1">
                          {g === "S"
                            ? "≥" + value
                            : g === "D"
                            ? "<" + (grades?.["C"] ?? 40)
                            : `${value}–${(grades?.[gradeOrder[gradeOrder.indexOf(g) - 1]] ?? 100) - 1}`}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </Card>

              {/* Dimension sub-scores */}
              {[
                "budget_strength",
                "scenario_fit",
                "timing",
                "reachability",
                "leverage",
              ].map((dim) => {
                const subScores = isEditingScoring && editedScoring
                  ? (editedScoring[dim] as Record<string, number>)
                  : (scoringConfig?.[dim] as Record<string, number>);
                if (!subScores) return null;
                return (
                  <Card key={dim} title={dimNames[dim] || dim}>
                    <div className="space-y-2">
                      {Object.entries(subScores).map(([key, val]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-sm text-muted">{key}</span>
                          {isEditingScoring && editedScoring ? (
                            <input
                              type="number"
                              min={0}
                              max={100}
                              value={val}
                              onChange={(e) => updateSubScore(dim, key, e.target.value)}
                              className="w-16 px-2 py-1 text-sm text-right border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                            />
                          ) : (
                            <span className="font-mono text-sm font-medium text-foreground">
                              {val}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </Card>
                );
              })}
            </>
          )}
        </div>
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
