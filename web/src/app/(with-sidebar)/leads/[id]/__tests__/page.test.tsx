import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, fireEvent, waitFor, cleanup } from "@testing-library/react";
import {
  createFollowUp,
  getLeadDetail,
  listBlocklist,
  unblockOrganization,
} from "@/lib/api-client";
import { SIGNAL_TYPE_LABELS } from "@/lib/constants";
import type { LeadDetail } from "@/lib/types";
import LeadDetailPage from "../page";

vi.mock("next/navigation", () => ({
  __esModule: true,
  useParams: () => ({ id: "lead-1" }),
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}));

const swrMock = vi.hoisted(() => ({
  values: {} as Record<string, unknown>,
  mutate: vi.fn(),
}));

vi.mock("swr", () => ({
  __esModule: true,
  default: (key: string) => ({
    data: swrMock.values[key] ?? null,
    error: null,
    isLoading: false,
    mutate: swrMock.mutate,
  }),
  mutate: () => Promise.resolve(),
  useSWRConfig: () => ({ mutate: swrMock.mutate }),
}));

vi.mock("@/hooks/use-meta", () => ({
  useMeta: () => ({
    signalTypeLabels: SIGNAL_TYPE_LABELS,
    error: null,
    mutate: vi.fn(),
  }),
}));

vi.mock("@/lib/api-client", () => ({
  getLeadDetail: vi.fn(),
  createFollowUp: vi.fn(),
  listBlocklist: vi.fn(),
  unblockOrganization: vi.fn(),
}));

function makeLead(overrides?: Partial<LeadDetail>): LeadDetail {
  return {
    id: "lead-1",
    organization: {
      id: "org-1",
      name: "测试机构",
      province: null,
      city: null,
      county: null,
      organization_type: null,
    },
    signal: {
      id: "sig-1",
      signal_type: "procurement_intent",
      title: "测试信号",
      budget_amount: 100000,
      source_url: "http://example.com/notice",
      evidence_text: "测试证据",
      confidence: 0.9,
      created_at: "2026-01-01T00:00:00Z",
    },
    score: {
      total_score: 80,
      grade: "A",
      budget_strength_score: 10,
      scenario_fit_score: 10,
      timing_score: 10,
      reachability_score: 10,
      leverage_score: 10,
    },
    call_script: {
      opening: "您好，我是测试销售",
      questions: ["您目前有包装升级计划吗？"],
      wechat_follow_up: "稍后我把资料发给您",
    },
    customer_type: null,
    recommended_package: null,
    budget_bucket: null,
    lead_status: "new",
    owner: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("LeadDetailPage - blacklist", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getLeadDetail).mockResolvedValue(makeLead());
    vi.mocked(listBlocklist).mockResolvedValue([]);
    vi.mocked(createFollowUp).mockResolvedValue({
      id: "fu-1",
      lead_id: "lead-1",
      channel: "phone",
      result: "无效:不需要服务",
      result_category: "无效",
      reason: "不需要服务",
      notes: null,
      next_action_at: null,
      created_at: "2026-06-14T08:00:00Z",
    });
    vi.mocked(unblockOrganization).mockResolvedValue(undefined);
    swrMock.values = {
      "lead-lead-1": makeLead(),
      blocklist: [],
    };
  });

  afterEach(() => {
    cleanup();
  });

  // ── AC-05: Block button visible for non-blocked lead ─────────────
  it("test_ac05_block_button_visible_for_non_blocked_lead", () => {
    const utils = render(<LeadDetailPage />);
    expect(utils.getByRole("button", { name: "屏蔽" })).toBeInTheDocument();
    expect(
      utils.queryByRole("button", { name: "解除屏蔽" })
    ).not.toBeInTheDocument();
  });

  // ── AC-05-E1: Block button hidden for blocked lead ───────────────
  it("test_ac05_e1_unblock_button_visible_for_blocked_lead", () => {
    swrMock.values = {
      "lead-lead-1": makeLead({ lead_status: "blocked" }),
      blocklist: [
        {
          id: "block-1",
          organization_id: "org-1",
          reason: "不需要服务",
          created_at: "2026-06-14T08:00:00Z",
        },
      ],
    };

    const utils = render(<LeadDetailPage />);
    expect(
      utils.queryByRole("button", { name: "屏蔽" })
    ).not.toBeInTheDocument();
    expect(utils.getByRole("button", { name: "解除屏蔽" })).toBeInTheDocument();
  });

  // ── AC-06: Clicking unblock restores lead status ─────────────────
  it("test_ac06_click_unblock_restores_lead_status", async () => {
    swrMock.values = {
      "lead-lead-1": makeLead({ lead_status: "blocked" }),
      blocklist: [
        {
          id: "block-1",
          organization_id: "org-1",
          reason: "不需要服务",
          created_at: "2026-06-14T08:00:00Z",
        },
      ],
    };

    const utils = render(<LeadDetailPage />);
    fireEvent.click(utils.getByRole("button", { name: "解除屏蔽" }));

    await waitFor(() =>
      expect(unblockOrganization).toHaveBeenCalledWith("block-1")
    );
    expect(swrMock.mutate).toHaveBeenCalled();
  });
});
