import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { FollowUpHistory } from "../follow-up-history";
import type { FollowUpOut } from "@/lib/types";

type FollowUpItem = FollowUpOut & {
  result_category?: string | null;
  reason?: string | null;
};

function makeFollowUp(overrides?: Partial<FollowUpItem>): FollowUpItem {
  return {
    id: "fu-1",
    lead_id: "lead-1",
    channel: "phone",
    result: "未接通:无人接听",
    result_category: "未接通",
    reason: "无人接听",
    notes: null,
    next_action_at: null,
    created_at: "2026-06-14T08:00:00Z",
    ...overrides,
  };
}

describe.each([
  { name: "full", compact: false },
  { name: "compact", compact: true },
])("FollowUpHistory ($name)", ({ compact }) => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-14T10:00:00Z"));
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  // ── AC-01: History item shows category and reason tags ───────────
  it("test_ac01_shows_category_and_reason_tags", () => {
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[makeFollowUp()]}
      />
    );

    expect(screen.getByText("未接通")).toBeInTheDocument();
    expect(screen.getByText("无人接听")).toBeInTheDocument();
  });

  // ── AC-01-E1: Legacy follow-up without category shows fallback ───
  it("test_ac01_e1_legacy_fallback_without_category", () => {
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[
          makeFollowUp({
            result: "未接通",
            result_category: null,
            reason: null,
          }),
        ]}
      />
    );

    expect(screen.getByText("未接通 (legacy)")).toBeInTheDocument();
    expect(screen.queryByText("未接通")).not.toBeInTheDocument();
  });

  // ── AC-01-B1: Empty notes do not render collapse control ─────────
  it("test_ac01_b1_empty_notes_no_expand", () => {
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[makeFollowUp({ notes: "" })]}
      />
    );

    expect(screen.queryByRole("button", { name: "展开" })).not.toBeInTheDocument();
  });

  // ── AC-02: Overdue next_action_at is shown in red ────────────────
  it("test_ac02_overdue_next_action_at_red", () => {
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[
          makeFollowUp({ next_action_at: "2026-06-14T09:00:00Z" }),
        ]}
      />
    );

    const nextAt = screen.getByTestId("next-action-at");
    expect(nextAt).toHaveClass("text-danger");
  });

  // ── AC-02-E1: Future next_action_at is not highlighted ───────────
  it("test_ac02_e1_future_next_action_at_normal", () => {
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[
          makeFollowUp({ next_action_at: "2026-06-14T11:00:00Z" }),
        ]}
      />
    );

    const nextAt = screen.getByTestId("next-action-at");
    expect(nextAt).not.toHaveClass("text-danger");
    expect(nextAt).toHaveClass("text-foreground");
  });

  // ── AC-02-B1: Missing next_action_at shows dash ──────────────────
  it("test_ac02_b1_missing_next_action_at_dash", () => {
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[makeFollowUp({ next_action_at: null })]}
      />
    );

    expect(screen.getByTestId("next-action-at")).toHaveTextContent("-");
  });

  // ── AC-03: Long notes are folded by default ──────────────────────
  it("test_ac03_long_notes_folded_by_default", () => {
    const notes = "a".repeat(150);
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[makeFollowUp({ notes })]}
      />
    );

    const notesEl = screen.getByTestId("follow-up-notes");
    expect(notesEl).toHaveTextContent("a".repeat(60));
    expect(notesEl).not.toHaveTextContent("a".repeat(61));
    expect(screen.getByRole("button", { name: "展开" })).toBeInTheDocument();
  });

  // ── AC-03-E1: Clicking expand shows full notes ───────────────────
  it("test_ac03_e1_click_expand_shows_full_notes", () => {
    const notes = "a".repeat(150);
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[makeFollowUp({ notes })]}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "展开" }));

    const notesEl = screen.getByTestId("follow-up-notes");
    expect(notesEl).toHaveTextContent(notes);
    expect(screen.getByRole("button", { name: "收起" })).toBeInTheDocument();
  });

  // ── AC-03-B1: Notes exactly 60 characters are not folded ─────────
  it("test_ac03_b1_exactly_sixty_not_folded", () => {
    const notes = "b".repeat(60);
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[makeFollowUp({ notes })]}
      />
    );

    expect(screen.getByTestId("follow-up-notes")).toHaveTextContent(notes);
    expect(screen.queryByRole("button", { name: "展开" })).not.toBeInTheDocument();
  });

  // ── AC-03-B2: Notes shorter than 60 characters are not folded ────
  it("test_ac03_b2_shorter_than_sixty_not_folded", () => {
    const notes = "c".repeat(30);
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[makeFollowUp({ notes })]}
      />
    );

    expect(screen.getByTestId("follow-up-notes")).toHaveTextContent(notes);
    expect(screen.queryByRole("button", { name: "展开" })).not.toBeInTheDocument();
  });

  // ── AC-03-B3: Notes with multibyte CJK characters count correctly ─
  it("test_ac03_b3_cjk_characters_count_correctly", () => {
    const notes = "客".repeat(40);
    render(
      <FollowUpHistory
        compact={compact}
        followUps={[makeFollowUp({ notes })]}
      />
    );

    expect(screen.getByTestId("follow-up-notes")).toHaveTextContent(notes);
    expect(screen.queryByRole("button", { name: "展开" })).not.toBeInTheDocument();
  });
});
