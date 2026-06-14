"use client";

import { useState } from "react";
import { createManualTask } from "@/lib/api-client";
import type { Source } from "@/lib/types";

interface TaskFormProps {
  sources: Source[];
  onCreated: (taskId: string) => void;
}

export function TaskForm({ sources, onCreated }: TaskFormProps) {
  const availableSources = sources.filter((s) => s.source_key);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [keywordMode, setKeywordMode] = useState<"by_group" | "by_keyword">("by_group");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleSource = (key: string) => {
    setSelectedSources((prev) =>
      prev.includes(key) ? prev.filter((s) => s !== key) : [...prev, key]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedSources.length === 0) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const task = await createManualTask({
        source_keys: selectedSources,
        keyword_mode: keywordMode,
      });
      onCreated(task.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败，请重试");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 bg-bg-elevated rounded-xl border border-border">
      <fieldset>
        <legend className="text-sm font-medium mb-2">选择信息渠道</legend>
        <div className="flex flex-wrap gap-2">
          {availableSources.map((source) => (
            <label
              key={source.source_key}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer text-sm transition-colors focus-within:ring-2 focus-within:ring-primary ${
                selectedSources.includes(source.source_key!)
                  ? "border-primary bg-primary/[0.06] text-primary"
                  : "border-border hover:bg-bg-muted"
              }`}
            >
              <input
                type="checkbox"
                className="sr-only"
                checked={selectedSources.includes(source.source_key!)}
                onChange={() => toggleSource(source.source_key!)}
              />
              {source.name}
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="text-sm font-medium mb-2">关键词模式</legend>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              value="by_group"
              checked={keywordMode === "by_group"}
              onChange={() => setKeywordMode("by_group")}
            />
            按关键词组生成
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              value="by_keyword"
              checked={keywordMode === "by_keyword"}
              onChange={() => setKeywordMode("by_keyword")}
            />
            按关键词生成
          </label>
        </div>
      </fieldset>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <button
        type="submit"
        disabled={selectedSources.length === 0 || isSubmitting}
        className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium disabled:bg-primary/50 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
      >
        {isSubmitting ? "提交中..." : "生成线索"}
      </button>
    </form>
  );
}
