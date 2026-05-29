"use client";

import { useState, useMemo, useCallback } from "react";
import useSWR from "swr";
import { getScoringConfig, updateScoringConfig } from "@/lib/api-client";
import {
  scoringRulesUpdateSchema,
  validateScoringRules,
} from "@/lib/schemas";

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
    if (!editedData) return [];

    // Structural validation via zod
    const parseResult = scoringRulesUpdateSchema.safeParse(editedData);
    if (!parseResult.success) {
      return parseResult.error.issues.map(
        (issue) => `${issue.path.join(".")}: ${issue.message}`
      );
    }

    // Semantic/business-rule validation
    return validateScoringRules(parseResult.data);
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
    const num = Number(value);
    if (isNaN(num)) return;
    setEditedData((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      next.max_scores = {
        ...(next.max_scores as Record<string, number>),
        [dim]: num,
      };
      return next;
    });
  }, []);

  const updateGrade = useCallback((grade: string, value: string) => {
    const num = Number(value);
    if (isNaN(num)) return;
    setEditedData((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      next.grades = {
        ...(next.grades as Record<string, number>),
        [grade]: num,
      };
      return next;
    });
  }, []);

  const updateSubScore = useCallback(
    (dim: string, key: string, value: string) => {
      const num = Number(value);
      if (isNaN(num)) return;
      setEditedData((prev) => {
        if (!prev) return prev;
        const next = { ...prev };
        next[dim] = {
          ...(next[dim] as Record<string, number>),
          [key]: num,
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
