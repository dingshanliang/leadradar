import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, fireEvent, waitFor, cleanup } from "@testing-library/react";
import {
  createFollowUp,
  getLeadDetail,
  getMeta,
  listFollowUps,
  updateLeadStatus,
} from "@/lib/api-client";
import { ApiError } from "@/lib/fetch-utils";
import { SIGNAL_TYPE_LABELS } from "@/lib/constants";
import { formatDateTimeLocal } from "@/lib/utils";
import type { LeadDetail, FollowUpOut } from "@/lib/types";
import WorkbenchPage from "../page";

vi.mock("next/navigation", () => ({
  __esModule: true,
  useParams: () => ({ id: "lead-1" }),
  useRouter: () => ({ back: vi.fn(), push: vi.fn() }),
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
  listFollowUps: vi.fn(),
  createFollowUp: vi.fn(),
  updateLeadStatus: vi.fn(),
  getMeta: vi.fn(),
}));

const metaWithCallResults = {
  signal_types: [{ key: "procurement_intent", label: "采购意向" }],
  statuses: [{ key: "new", label: "新建" }],
  grades: ["S", "A", "B", "C", "D"],
  budget_buckets: ["<10万"],
  call_results: {
    未接通: { reasons: ["无人接听", "关机", "占线"] },
    接通有意向: { reasons: ["需方案", "约演示", "询价"] },
    无效: { reasons: ["不需要服务"] },
  },
  follow_up_suggestions: {
    未接通: "2h",
    接通有意向: "1d",
    无效: "7d",
  },
};

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

describe("WorkbenchPage - workbench-follow-up-form", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getLeadDetail).mockResolvedValue(makeLead());
    vi.mocked(listFollowUps).mockResolvedValue([]);
    vi.mocked(getMeta).mockResolvedValue(metaWithCallResults);
    vi.mocked(createFollowUp).mockImplementation((leadId, data) => {
      return Promise.resolve({
        id: "fu-1",
        lead_id: leadId,
        channel: (data as { channel: string }).channel,
        result: `${(data as { result_category: string }).result_category}:${(data as { reason: string }).reason}`,
        result_category: (data as { result_category: string }).result_category,
        reason: (data as { reason: string }).reason,
        notes: (data as { notes?: string | null }).notes ?? null,
        next_action_at: (data as { next_action_at?: string | null }).next_action_at ?? null,
        created_at: "2026-06-14T08:00:00Z",
      } as FollowUpOut);
    });
    swrMock.values = {
      "lead-lead-1": makeLead(),
      "followups-lead-1": [],
      meta: metaWithCallResults,
    };
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  // ── AC-01: Datetime picker visible ───────────────────────────────
  it("test_ac01_datetime_picker_visible", () => {
    const utils = render(<WorkbenchPage />);
    const input = utils.getByLabelText("下次跟进时间");
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute("type", "datetime-local");
    expect(input).toHaveAttribute("step", "3600");
  });

  // ── AC-01-E1: Submit disabled when result not selected ───────────
  it("test_ac01_e1_submit_disabled_without_result", () => {
    const utils = render(<WorkbenchPage />);
    const dt = utils.getByLabelText("下次跟进时间");
    fireEvent.change(dt, { target: { value: "2026-06-14T10:00" } });
    expect(utils.getByRole("button", { name: "提交跟进" })).toBeDisabled();
  });

  // ── AC-01-B1: Default next_action_at from backend suggestion ──────
  it("test_ac01_b1_default_next_action_suggestion", () => {
    const nowSpy = vi
      .spyOn(Date, "now")
      .mockReturnValue(new Date("2026-06-14T08:00:00.000Z").getTime());
    const utils = render(<WorkbenchPage />);
    fireEvent.change(utils.getByLabelText("结果类别"), {
      target: { value: "未接通" },
    });
    const expected = formatDateTimeLocal(
      new Date(Date.now() + 2 * 60 * 60 * 1000)
    );
    expect(utils.getByLabelText("下次跟进时间")).toHaveValue(expected);
    nowSpy.mockRestore();
  });

  // ── AC-01-B2: User can clear next_action_at ──────────────────────
  it("test_ac01_b2_clear_next_action_at", async () => {
    const utils = render(<WorkbenchPage />);
    fireEvent.change(utils.getByLabelText("结果类别"), {
      target: { value: "未接通" },
    });
    fireEvent.change(utils.getByLabelText("具体原因"), {
      target: { value: "无人接听" },
    });
    fireEvent.change(utils.getByLabelText("下次跟进时间"), {
      target: { value: "" },
    });
    fireEvent.click(utils.getByRole("button", { name: "提交跟进" }));

    await waitFor(() => expect(createFollowUp).toHaveBeenCalledTimes(1));
    const payload = vi.mocked(createFollowUp).mock.calls[0][1];
    expect(payload.next_action_at).toBeUndefined();
  });

  // ── AC-02: Category select populates reason select ───────────────
  it("test_ac02_category_populates_reason_select", () => {
    const utils = render(<WorkbenchPage />);
    const reason = utils.getByLabelText("具体原因") as HTMLSelectElement;
    expect(reason).toBeDisabled();

    fireEvent.change(utils.getByLabelText("结果类别"), {
      target: { value: "未接通" },
    });

    expect(reason).not.toBeDisabled();
    const optionValues = Array.from(reason.options).map((o) => o.value);
    expect(optionValues).toContain("无人接听");
    expect(optionValues).toContain("关机");
    expect(optionValues).toContain("占线");
  });

  // ── AC-02-E1: Reason select disabled until category chosen ───────
  it("test_ac02_e1_reason_disabled_until_category_chosen", () => {
    const utils = render(<WorkbenchPage />);
    const reason = utils.getByLabelText("具体原因");
    expect(reason).toBeDisabled();
    expect(utils.getByText("请先选择结果类别")).toBeInTheDocument();
  });

  // ── AC-02-E2: Submit without reason shows validation error ───────
  it("test_ac02_e2_submit_without_reason_shows_error", async () => {
    const utils = render(<WorkbenchPage />);
    fireEvent.change(utils.getByLabelText("结果类别"), {
      target: { value: "未接通" },
    });
    fireEvent.click(utils.getByRole("button", { name: "提交跟进" }));

    await waitFor(() =>
      expect(utils.getByText("请选择具体原因")).toBeInTheDocument()
    );
    expect(createFollowUp).not.toHaveBeenCalled();
  });

  // ── AC-02-B1: Changing category resets reason ────────────────────
  it("test_ac02_b1_changing_category_resets_reason", async () => {
    const utils = render(<WorkbenchPage />);
    fireEvent.change(utils.getByLabelText("结果类别"), {
      target: { value: "未接通" },
    });
    fireEvent.change(utils.getByLabelText("具体原因"), {
      target: { value: "无人接听" },
    });
    expect((utils.getByLabelText("具体原因") as HTMLSelectElement).value).toBe(
      "无人接听"
    );

    fireEvent.change(utils.getByLabelText("结果类别"), {
      target: { value: "接通有意向" },
    });
    expect((utils.getByLabelText("具体原因") as HTMLSelectElement).value).toBe(
      ""
    );

    fireEvent.click(utils.getByRole("button", { name: "提交跟进" }));
    await waitFor(() =>
      expect(utils.getByText("请选择具体原因")).toBeInTheDocument()
    );
  });

  // ── AC-03: Submit creates follow-up, refreshes history, resets ───
  it("test_ac03_submit_creates_follow_up_refreshes_resets", async () => {
    vi.mocked(updateLeadStatus).mockResolvedValue(undefined);

    const utils = render(<WorkbenchPage />);
    fireEvent.change(utils.getByLabelText("渠道"), {
      target: { value: "phone" },
    });
    fireEvent.change(utils.getByLabelText("结果类别"), {
      target: { value: "未接通" },
    });
    fireEvent.change(utils.getByLabelText("具体原因"), {
      target: { value: "无人接听" },
    });
    const nextAt = "2026-12-31T10:00";
    fireEvent.change(utils.getByLabelText("下次跟进时间"), {
      target: { value: nextAt },
    });
    fireEvent.click(utils.getByRole("button", { name: "提交跟进" }));

    await waitFor(() => expect(createFollowUp).toHaveBeenCalledTimes(1));
    expect(createFollowUp).toHaveBeenCalledWith(
      "lead-1",
      expect.objectContaining({
        channel: "phone",
        result_category: "未接通",
        reason: "无人接听",
        next_action_at: nextAt,
      })
    );
    expect(updateLeadStatus).toHaveBeenCalledWith("lead-1", "called");
    expect(swrMock.mutate).toHaveBeenCalled();

    expect(
      (utils.getByLabelText("结果类别") as HTMLSelectElement).value
    ).toBe("");
    expect((utils.getByLabelText("具体原因") as HTMLSelectElement).value).toBe(
      ""
    );
  });

  // ── AC-03-E1: API error shows error state and preserves values ───
  it("test_ac03_e1_api_error_preserves_values", async () => {
    vi.mocked(createFollowUp).mockRejectedValue(
      new ApiError(422, "结果类别与原因不匹配")
    );

    const utils = render(<WorkbenchPage />);
    fireEvent.change(utils.getByLabelText("结果类别"), {
      target: { value: "未接通" },
    });
    fireEvent.change(utils.getByLabelText("具体原因"), {
      target: { value: "无人接听" },
    });
    const nextAt = "2026-12-31T10:00";
    fireEvent.change(utils.getByLabelText("下次跟进时间"), {
      target: { value: nextAt },
    });
    fireEvent.change(utils.getByLabelText("备注"), {
      target: { value: "test note" },
    });
    fireEvent.click(utils.getByRole("button", { name: "提交跟进" }));

    await waitFor(() =>
      expect(utils.getByText("结果类别与原因不匹配")).toBeInTheDocument()
    );
    expect(
      (utils.getByLabelText("结果类别") as HTMLSelectElement).value
    ).toBe("未接通");
    expect((utils.getByLabelText("具体原因") as HTMLSelectElement).value).toBe(
      "无人接听"
    );
    expect(utils.getByLabelText("下次跟进时间")).toHaveValue(nextAt);
    expect(utils.getByLabelText("备注")).toHaveValue("test note");
  });

  // ── AC-03-B1: Double-clicking submit does not duplicate ──────────
  it("test_ac03_b1_double_click_does_not_duplicate", async () => {
    let resolve!: (value: FollowUpOut) => void;
    const promise = new Promise<FollowUpOut>((res) => {
      resolve = res;
    });
    vi.mocked(createFollowUp).mockReturnValue(promise);

    const utils = render(<WorkbenchPage />);
    fireEvent.change(utils.getByLabelText("结果类别"), {
      target: { value: "未接通" },
    });
    fireEvent.change(utils.getByLabelText("具体原因"), {
      target: { value: "无人接听" },
    });

    const btn = utils.getByRole("button", { name: "提交跟进" });
    fireEvent.click(btn);
    fireEvent.click(btn);

    expect(createFollowUp).toHaveBeenCalledTimes(1);
    expect(btn).toBeDisabled();

    resolve({
      id: "fu-1",
      lead_id: "lead-1",
      channel: "phone",
      result: "未接通:无人接听",
      result_category: "未接通",
      reason: "无人接听",
      notes: null,
      next_action_at: null,
      created_at: "2026-06-14T08:00:00Z",
    });

    await waitFor(() =>
      expect(utils.getByRole("button", { name: "提交跟进" })).toBeInTheDocument()
    );
    expect(createFollowUp).toHaveBeenCalledTimes(1);
  });

  // ── AC-01-B2: Block organization checkbox defaults to false ───────
  it("test_ac01_b2_block_organization_checkbox_defaults_unchecked", async () => {
    vi.mocked(updateLeadStatus).mockResolvedValue(undefined);

    const utils = render(<WorkbenchPage />);
    fireEvent.change(utils.getByLabelText("结果类别"), {
      target: { value: "无效" },
    });
    fireEvent.change(utils.getByLabelText("具体原因"), {
      target: { value: "不需要服务" },
    });

    const checkbox = utils.getByLabelText(
      "同时屏蔽整个机构"
    ) as HTMLInputElement;
    expect(checkbox).toBeInTheDocument();
    expect(checkbox.checked).toBe(false);

    fireEvent.click(utils.getByRole("button", { name: "提交跟进" }));

    await waitFor(() => expect(createFollowUp).toHaveBeenCalledTimes(1));
    expect(createFollowUp).toHaveBeenCalledWith(
      "lead-1",
      expect.objectContaining({
        result_category: "无效",
        reason: "不需要服务",
        block_organization: false,
      })
    );
    expect(updateLeadStatus).toHaveBeenCalledWith("lead-1", "blocked");
  });
});
