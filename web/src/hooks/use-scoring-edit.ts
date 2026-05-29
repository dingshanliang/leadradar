"use client";

import { useState, useMemo, useCallback } from "react";
import useSWR from "swr";
import { getScoringConfig, updateScoringConfig } from "@/lib/api-client";

const DIM_NAMES: Record<string, string> = {
  budget_strength: "预算强度",
  scenario_fit: "场景匹配",
  timing: "时间窗口",
  reachability: "可触达性",
  leverage: "成交杠杆",
};

const GRADE_ORDER = ["S", "A", "B", "C", "D"];

const DIMENSIONS = [
  "budget_strength",
  "scenario_fit",
  "timing",
  "reachability",
  "leverage",
];

export { DIM_NAMES, GRADE_ORDER, DIMENSIONS };

export function useScoringEdit() {
  const {
    data: scoringConfig,
    error,
    isLoading,
    mutate,
  } = useSWR<Record<string, unknown>>("scoring-config", getScoringConfig, {
    revalidateOnFocus: false,
  });

  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState<Record<string, unknown> | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const validationErrors = useMemo(() => {
    const errors: string[] = [];
    if (!editedData) return errors;

    const maxScores = editedData.max_scores as Record<string, number> | undefined;
    if (maxScores) {
      const total = Object.values(maxScores).reduce(
        (sum, v) => sum + (Number(v) || 0),
        0
      );
      if (total !== 100) {
        errors.push(`维度权重总和必须等于 100，当前为 ${total}`);
      }
    }

    const grades = editedData.grades as Record<string, number> | undefined;
    if (grades) {
      const values = GRADE_ORDER.map((g) => Number(grades[g]) || 0);
      for (let i = 0; i < values.length - 1; i++) {
        if (values[i] <= values[i + 1]) {
          errors.push(
            `等级阈值必须严格递减: ${GRADE_ORDER[i]}(${values[i]}) 应大于 ${GRADE_ORDER[i + 1]}(${values[i + 1]})`
          );
        }
      }
    }

    for (const dim of DIMENSIONS) {
      const maxVal = maxScores?.[dim];
      const subScores = editedData[dim] as Record<string, number> | undefined;
      if (subScores && maxVal !== undefined) {
        for (const [key, val] of Object.entries(subScores)) {
          if (Number(val) > Number(maxVal)) {
            errors.push(
              `${DIM_NAMES[dim] || dim}.${key} 的分值 ${val} 超过了该维度满分 ${maxVal}`
            );
          }
        }
      }
    }

    return errors;
  }, [editedData]);

  const isValid = validationErrors.length === 0;

  const startEditing = useCallback(() => {
    if (scoringConfig) {
      setEditedData(JSON.parse(JSON.stringify(scoringConfig)));
      setIsEditing(true);
      setSaveError(null);
    }
  }, [scoringConfig]);

  const cancelEditing = useCallback(() => {
    setIsEditing(false);
    setEditedData(null);
    setSaveError(null);
  }, []);

  const save = useCallback(async () => {
    if (!editedData || !isValid) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      await updateScoringConfig(editedData);
      await mutate();
      setIsEditing(false);
      setEditedData(null);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setIsSaving(false);
    }
  }, [editedData, isValid, mutate]);

  const updateMaxScore = useCallback((dim: string, value: string) => {
    setEditedData((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      next.max_scores = {
        ...(next.max_scores as Record<string, number>),
        [dim]: Number(value) || 0,
      };
      return next;
    });
  }, []);

  const updateGrade = useCallback((grade: string, value: string) => {
    setEditedData((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      next.grades = {
        ...(next.grades as Record<string, number>),
        [grade]: Number(value) || 0,
      };
      return next;
    });
  }, []);

  const updateSubScore = useCallback(
    (dim: string, key: string, value: string) => {
      setEditedData((prev) => {
        if (!prev) return prev;
        const next = { ...prev };
        next[dim] = {
          ...(next[dim] as Record<string, number>),
          [key]: Number(value) || 0,
        };
        return next;
      });
    },
    []
  );

  return {
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
  };
}
