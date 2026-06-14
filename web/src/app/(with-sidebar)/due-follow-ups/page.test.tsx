import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

const mockUseDueFollowUps = vi.fn(() => ({
  followUps: [],
  error: null,
  isLoading: false,
  mutate: vi.fn(),
}));
vi.mock("@/hooks/use-due-follow-ups", () => ({
  useDueFollowUps: () => mockUseDueFollowUps(),
}));

import DueFollowUpsPage from "./page";

describe("Due follow-ups list page (AC-03)", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it("AC-03: renders due follow-ups sorted by next_action_at", () => {
    mockUseDueFollowUps.mockReturnValue({
      followUps: [
        {
          follow_up_id: "fu-1",
          lead_id: "lead-1",
          organization_name: "机构A",
          next_action_at: "2026-06-14T10:00:00Z",
          result: "未接通:无人接听",
        },
        {
          follow_up_id: "fu-2",
          lead_id: "lead-2",
          organization_name: "机构B",
          next_action_at: "2026-06-14T09:00:00Z",
          result: "接通有意向",
        },
      ],
      error: null,
      isLoading: false,
      mutate: vi.fn(),
    });

    render(<DueFollowUpsPage />);

    expect(screen.getByText("机构A")).toBeInTheDocument();
    expect(screen.getByText("机构B")).toBeInTheDocument();
    expect(screen.getAllByText("进入工作台")).toHaveLength(2);
  });

  it("AC-03-E1: shows empty state when the list is empty", () => {
    mockUseDueFollowUps.mockReturnValue({
      followUps: [],
      error: null,
      isLoading: false,
      mutate: vi.fn(),
    });

    render(<DueFollowUpsPage />);

    expect(screen.getByText("暂无到期跟进")).toBeInTheDocument();
  });

  it("AC-03-E2: shows error state with retry button", () => {
    const mutate = vi.fn();
    mockUseDueFollowUps.mockReturnValue({
      followUps: [],
      error: new Error("load failed"),
      isLoading: false,
      mutate,
    });

    render(<DueFollowUpsPage />);

    const retryButton = screen.getByText("重试");
    expect(retryButton).toBeInTheDocument();
    fireEvent.click(retryButton);
    expect(mutate).toHaveBeenCalled();
  });

  it("AC-03-B1: clicking 进入工作台 navigates to workbench", async () => {
    mockUseDueFollowUps.mockReturnValue({
      followUps: [
        {
          follow_up_id: "fu-1",
          lead_id: "lead-id",
          organization_name: "机构A",
          next_action_at: "2026-06-14T10:00:00Z",
          result: "未接通:无人接听",
        },
      ],
      error: null,
      isLoading: false,
      mutate: vi.fn(),
    });

    render(<DueFollowUpsPage />);

    fireEvent.click(screen.getByText("进入工作台"));
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/workbench/lead-id");
    });
  });
});
