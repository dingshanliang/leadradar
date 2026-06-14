import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// Mock Next.js navigation hooks before importing Sidebar
const mockUsePathname = vi.fn(() => "/");
vi.mock("next/navigation", () => ({
  usePathname: () => mockUsePathname(),
}));

// Mock the due-follow-up count hook
const mockUseDueFollowUpCount = vi.fn(() => ({
  count: 0,
  error: null,
  isLoading: false,
  mutate: vi.fn(),
}));
vi.mock("@/hooks/use-due-follow-up-count", () => ({
  useDueFollowUpCount: () => mockUseDueFollowUpCount(),
}));

import { Sidebar } from "../sidebar";

describe("Sidebar due-follow-up badge (AC-02)", () => {
  it("AC-02: displays a red badge with the due count", () => {
    mockUseDueFollowUpCount.mockReturnValue({
      count: 3,
      error: null,
      isLoading: false,
      mutate: vi.fn(),
    });

    render(<Sidebar />);

    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("3").closest("span")).toHaveClass("bg-danger");
  });

  it("AC-02-E1: hides the badge when the count is zero", () => {
    mockUseDueFollowUpCount.mockReturnValue({
      count: 0,
      error: null,
      isLoading: false,
      mutate: vi.fn(),
    });

    render(<Sidebar />);

    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("AC-02-B1: caps the badge at 99+ and shows exact count in tooltip", () => {
    mockUseDueFollowUpCount.mockReturnValue({
      count: 150,
      error: null,
      isLoading: false,
      mutate: vi.fn(),
    });

    render(<Sidebar />);

    expect(screen.getByText("99+")).toBeInTheDocument();
    expect(screen.getByTitle("150 条到期跟进")).toBeInTheDocument();
  });

  it("AC-02-B2: updates the badge when the count changes", () => {
    mockUseDueFollowUpCount.mockReturnValue({
      count: 2,
      error: null,
      isLoading: false,
      mutate: vi.fn(),
    });

    const { rerender } = render(<Sidebar />);
    expect(screen.getByText("2")).toBeInTheDocument();

    mockUseDueFollowUpCount.mockReturnValue({
      count: 3,
      error: null,
      isLoading: false,
      mutate: vi.fn(),
    });
    rerender(<Sidebar />);

    expect(screen.getByText("3")).toBeInTheDocument();
  });
});
