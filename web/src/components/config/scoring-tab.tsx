"use client";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { useScoringEdit, DIM_NAMES, GRADE_ORDER, DIMENSIONS } from "@/hooks/use-scoring-edit";

export function ScoringTab() {
  const {
    scoringConfig,
    error,
    isLoading,
    isEditing,
    editedData,
    saveError,
    isSaving,
    validationErrors,
    isValid,
    startEditing,
    cancelEditing,
    save,
    updateMaxScore,
    updateGrade,
    updateSubScore,
    mutate,
  } = useScoringEdit();

  return (
    <div className="space-y-4">
      {/* Action bar */}
      <div className="flex justify-between items-center">
        <h2 className="text-sm font-medium text-foreground">评分规则配置</h2>
        {isEditing ? (
          <div className="flex gap-2">
            <button
              onClick={cancelEditing}
              className="px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-bg-muted transition-colors"
              disabled={isSaving}
            >
              取消
            </button>
            <button
              onClick={save}
              disabled={!isValid || isSaving}
              className={`px-3 py-1.5 text-sm rounded-lg text-white transition-colors ${
                isValid && !isSaving
                  ? "bg-primary hover:bg-primary/90"
                  : "bg-border cursor-not-allowed"
              }`}
            >
              {isSaving ? "保存中..." : "保存"}
            </button>
          </div>
        ) : (
          <button
            onClick={startEditing}
            className="px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-bg-muted transition-colors"
          >
            编辑
          </button>
        )}
      </div>

      {/* Validation errors */}
      {validationErrors.length > 0 && (
        <div className="bg-danger/10 border border-danger/20 rounded-xl p-4 space-y-1">
          {validationErrors.map((err) => (
            <p key={err} className="text-sm text-danger">
              {err}
            </p>
          ))}
        </div>
      )}

      {/* Save error */}
      {saveError && (
        <div className="bg-danger/10 border border-danger/20 rounded-xl p-4">
          <p className="text-sm text-danger">{saveError}</p>
        </div>
      )}

      {error ? (
        <ErrorState onRetry={() => mutate()} />
      ) : isLoading ? (
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
              {scoringConfig?.max_scores != null
                ? Object.entries(
                    scoringConfig.max_scores as Record<string, number>
                  ).map(([key, val]) => (
                    <div key={key} className="flex items-center gap-4">
                      <div className="w-24">
                        <p className="text-sm text-foreground">
                          {DIM_NAMES[key] || key}
                        </p>
                      </div>
                      {isEditing && editedData ? (
                        <input
                          type="number"
                          min={0}
                          max={100}
                          value={
                            (editedData.max_scores as Record<string, number>)?.[
                              key
                            ] ?? val
                          }
                          onChange={(e) => updateMaxScore(key, e.target.value)}
                          className="w-20 px-2 py-1 text-sm border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                        />
                      ) : (
                        <div className="flex-1">
                          <div className="h-3 bg-bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-cta rounded-full"
                              style={{ width: `${val}%` }}
                            />
                          </div>
                        </div>
                      )}
                      <div className="w-10 text-right">
                        <span className="font-mono text-sm font-bold text-primary">
                          {isEditing && editedData
                            ? (editedData.max_scores as Record<string, number>)?.[
                                key
                              ] ?? val
                            : val}
                        </span>
                      </div>
                    </div>
                  ))
                : null}
              <div className="flex justify-end pt-2 border-t border-border/50">
                <p className="text-xs text-muted">
                  权重总和：
                  <span className="font-mono font-bold text-primary">
                    {isEditing && editedData
                      ? Object.values(
                          (editedData.max_scores as Record<string, number>) || {}
                        ).reduce((sum, v) => sum + (Number(v) || 0), 0)
                      : Object.values(
                          (scoringConfig?.max_scores as Record<string, number>) ||
                            {}
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
              {GRADE_ORDER.map((g) => {
                const grades = isEditing && editedData
                  ? (editedData.grades as Record<string, number>)
                  : (scoringConfig?.grades as Record<string, number>);
                const value = grades?.[g] ?? 0;
                return (
                  <div key={g} className="flex-1">
                    <div className="text-center mb-2">
                      <span
                        className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                          g === "S"
                            ? "bg-success/15 text-success"
                            : g === "A"
                            ? "bg-cta/15 text-cta"
                            : g === "B"
                            ? "bg-warning/15 text-warning"
                            : g === "C"
                            ? "bg-warning/15 text-warning"
                            : "bg-bg-muted text-muted"
                        }`}
                      >
                        {g}
                      </span>
                    </div>
                    {isEditing && editedData ? (
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={value}
                        onChange={(e) => updateGrade(g, e.target.value)}
                        disabled={g === "D"}
                        className="w-full px-2 py-1 text-sm text-center border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary disabled:bg-bg-muted disabled:text-muted"
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
                        : `${value}–${
                            (grades?.[GRADE_ORDER[GRADE_ORDER.indexOf(g) - 1]] ??
                              100) - 1
                          }`}
                    </p>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Dimension sub-scores */}
          {DIMENSIONS.map((dim) => {
            const subScores = isEditing && editedData
              ? (editedData[dim] as Record<string, number>)
              : (scoringConfig?.[dim] as Record<string, number>);
            if (!subScores) return null;
            return (
              <Card key={dim} title={DIM_NAMES[dim] || dim}>
                <div className="space-y-2">
                  {Object.entries(subScores).map(([key, val]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-sm text-muted">{key}</span>
                      {isEditing && editedData ? (
                        <input
                          type="number"
                          min={0}
                          max={100}
                          value={val}
                          onChange={(e) =>
                            updateSubScore(dim, key, e.target.value)
                          }
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
  );
}
