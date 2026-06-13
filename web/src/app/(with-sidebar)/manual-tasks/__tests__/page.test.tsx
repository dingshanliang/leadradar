import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ManualTasksPage from "../page";

vi.mock("@/hooks/use-manual-tasks", () => ({
  useManualTasks: () => ({
    tasks: [],
    error: null,
    isLoading: false,
    mutate: vi.fn(),
  }),
  useManualTask: () => ({
    task: null,
    error: null,
    isLoading: false,
    mutate: vi.fn(),
  }),
}));

vi.mock("@/hooks/use-sources", () => ({
  useSources: () => ({
    sources: [
      { id: "s1", source_key: "test_source", name: "测试源 A", source_type: "government_procurement", enabled: true, rate_limit_per_minute: 20 },
    ],
    error: null,
    isLoading: false,
  }),
}));

describe("ManualTasksPage", () => {
  it("renders form and empty task list", () => {
    render(<ManualTasksPage />);
    expect(screen.getByText("手动生成线索")).toBeInTheDocument();
    expect(screen.getByText("生成线索")).toBeInTheDocument();
    expect(screen.getByText("测试源 A")).toBeInTheDocument();
  });
});
