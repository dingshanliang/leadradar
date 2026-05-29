import { describe, it, expect } from "vitest";
import {
  scoringRulesUpdateSchema,
  leadStatusUpdateSchema,
  followUpCreateSchema,
  validateScoringRules,
  validateLeadStatus,
  validateFollowUpCreate,
} from "../schemas";

// ── scoringRulesUpdateSchema ──────────────────────────────────────

describe("scoringRulesUpdateSchema", () => {
  const validPayload = {
    version: "0.1",
    max_scores: {
      budget_strength: 35,
      scenario_fit: 25,
      timing: 20,
      reachability: 10,
      leverage: 10,
    },
    grades: { S: 85, A: 70, B: 55, C: 40, D: 0 },
    budget_strength: {
      procurement_intent: 35,
      tender_notice: 35,
    },
    scenario_fit: {
      region_brand_or_association: 10,
      prepackaged_food: 8,
    },
    timing: {
      procurement_expected_within_3_months: 20,
      newly_published_tender: 18,
    },
    reachability: {
      procurement_contact: 10,
      agency_phone: 8,
    },
    leverage: {
      multi_org_region_brand_project: 10,
      winning_service_provider: 8,
    },
  };

  it("accepts valid scoring config payload", () => {
    const result = scoringRulesUpdateSchema.safeParse(validPayload);
    expect(result.success).toBe(true);
  });

  it("rejects negative max_score values", () => {
    const payload = {
      ...validPayload,
      max_scores: { ...validPayload.max_scores, budget_strength: -5 },
    };
    const result = scoringRulesUpdateSchema.safeParse(payload);
    expect(result.success).toBe(false);
  });

  it("rejects max_score values exceeding 100", () => {
    const payload = {
      ...validPayload,
      max_scores: { ...validPayload.max_scores, budget_strength: 150 },
    };
    const result = scoringRulesUpdateSchema.safeParse(payload);
    expect(result.success).toBe(false);
  });

  it("rejects negative grade threshold values", () => {
    const payload = {
      ...validPayload,
      grades: { S: 85, A: -10, B: 55, C: 40, D: 0 },
    };
    const result = scoringRulesUpdateSchema.safeParse(payload);
    expect(result.success).toBe(false);
  });

  it("rejects grade threshold values exceeding 100", () => {
    const payload = {
      ...validPayload,
      grades: { S: 110, A: 70, B: 55, C: 40, D: 0 },
    };
    const result = scoringRulesUpdateSchema.safeParse(payload);
    expect(result.success).toBe(false);
  });

  it("rejects negative sub-score values", () => {
    const payload = {
      ...validPayload,
      budget_strength: { procurement_intent: -5, tender_notice: 35 },
    };
    const result = scoringRulesUpdateSchema.safeParse(payload);
    expect(result.success).toBe(false);
  });

  it("rejects missing required grade keys", () => {
    const payload = {
      ...validPayload,
      grades: { S: 85, A: 70, B: 55, C: 40 },
      // D is missing
    };
    const result = scoringRulesUpdateSchema.safeParse(payload);
    expect(result.success).toBe(false);
  });

  it("rejects non-string version", () => {
    const payload = { ...validPayload, version: 123 };
    const result = scoringRulesUpdateSchema.safeParse(payload);
    expect(result.success).toBe(false);
  });

  it("rejects empty object", () => {
    const result = scoringRulesUpdateSchema.safeParse({});
    expect(result.success).toBe(false);
  });
});

// ── validateScoringRules (semantic validation) ────────────────────

describe("validateScoringRules", () => {
  it("returns errors when max_scores total is not 100", () => {
    const payload = {
      version: "0.1",
      max_scores: { budget_strength: 30, scenario_fit: 20 },
      grades: { S: 85, A: 70, B: 55, C: 40, D: 0 },
      budget_strength: {},
      scenario_fit: {},
      timing: {},
      reachability: {},
      leverage: {},
    };
    const result = validateScoringRules(payload);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.stringContaining("权重总和必须等于 100"),
      ])
    );
  });

  it("returns errors when grade thresholds are not strictly decreasing", () => {
    const payload = {
      version: "0.1",
      max_scores: {
        budget_strength: 35,
        scenario_fit: 25,
        timing: 20,
        reachability: 10,
        leverage: 10,
      },
      grades: { S: 70, A: 85, B: 55, C: 40, D: 0 },
      budget_strength: {},
      scenario_fit: {},
      timing: {},
      reachability: {},
      leverage: {},
    };
    const result = validateScoringRules(payload);
    expect(result.length).toBeGreaterThan(0);
    expect(result.some((e) => e.includes("等级阈值"))).toBe(true);
  });

  it("returns errors when sub-score exceeds dimension max_score", () => {
    const payload = {
      version: "0.1",
      max_scores: {
        budget_strength: 35,
        scenario_fit: 25,
        timing: 20,
        reachability: 10,
        leverage: 10,
      },
      grades: { S: 85, A: 70, B: 55, C: 40, D: 0 },
      budget_strength: { procurement_intent: 40 },
      scenario_fit: {},
      timing: {},
      reachability: {},
      leverage: {},
    };
    const result = validateScoringRules(payload);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.stringContaining("超过了该维度满分"),
      ])
    );
  });

  it("returns empty array for valid payload", () => {
    const payload = {
      version: "0.1",
      max_scores: {
        budget_strength: 35,
        scenario_fit: 25,
        timing: 20,
        reachability: 10,
        leverage: 10,
      },
      grades: { S: 85, A: 70, B: 55, C: 40, D: 0 },
      budget_strength: { procurement_intent: 35, tender_notice: 20 },
      scenario_fit: { region_brand: 10 },
      timing: { within_3_months: 20 },
      reachability: { procurement_contact: 10 },
      leverage: { multi_org: 10 },
    };
    const result = validateScoringRules(payload);
    expect(result).toEqual([]);
  });
});

// ── leadStatusUpdateSchema ────────────────────────────────────────

describe("leadStatusUpdateSchema", () => {
  const validStatuses = [
    "new",
    "qualified",
    "called",
    "connected",
    "diagnosis_scheduled",
    "proposal_sent",
    "won",
    "lost",
    "invalid",
    "blocked",
  ];

  validStatuses.forEach((status) => {
    it(`accepts valid status "${status}"`, () => {
      const result = leadStatusUpdateSchema.safeParse({ status });
      expect(result.success).toBe(true);
    });
  });

  it("rejects invalid status value", () => {
    const result = leadStatusUpdateSchema.safeParse({ status: "unknown" });
    expect(result.success).toBe(false);
  });

  it("rejects empty string status", () => {
    const result = leadStatusUpdateSchema.safeParse({ status: "" });
    expect(result.success).toBe(false);
  });

  it("rejects missing status field", () => {
    const result = leadStatusUpdateSchema.safeParse({});
    expect(result.success).toBe(false);
  });

  it("rejects non-string status", () => {
    const result = leadStatusUpdateSchema.safeParse({ status: 123 });
    expect(result.success).toBe(false);
  });
});

// ── validateLeadStatus helper ─────────────────────────────────────

describe("validateLeadStatus", () => {
  it("returns parsed data for valid status", () => {
    const result = validateLeadStatus("new");
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data).toBe("new");
    }
  });

  it("returns error for invalid status", () => {
    const result = validateLeadStatus("garbage");
    expect(result.success).toBe(false);
  });
});

// ── followUpCreateSchema ──────────────────────────────────────────

describe("followUpCreateSchema", () => {
  it("accepts valid follow-up with required fields", () => {
    const result = followUpCreateSchema.safeParse({
      channel: "phone",
      result: "客户有意向",
    });
    expect(result.success).toBe(true);
  });

  it("accepts valid follow-up with optional fields", () => {
    const result = followUpCreateSchema.safeParse({
      channel: "wechat",
      result: "加了微信",
      notes: "客户说下周联系",
      contact_id: "abc-123",
    });
    expect(result.success).toBe(true);
  });

  it("rejects missing channel", () => {
    const result = followUpCreateSchema.safeParse({
      result: "客户有意向",
    });
    expect(result.success).toBe(false);
  });

  it("rejects missing result", () => {
    const result = followUpCreateSchema.safeParse({
      channel: "phone",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty channel string", () => {
    const result = followUpCreateSchema.safeParse({
      channel: "",
      result: "客户有意向",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty result string", () => {
    const result = followUpCreateSchema.safeParse({
      channel: "phone",
      result: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty object", () => {
    const result = followUpCreateSchema.safeParse({});
    expect(result.success).toBe(false);
  });
});

// ── validateFollowUpCreate helper ─────────────────────────────────

describe("validateFollowUpCreate", () => {
  it("returns parsed data for valid input", () => {
    const result = validateFollowUpCreate({
      channel: "phone",
      result: "跟进中",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.channel).toBe("phone");
      expect(result.data.result).toBe("跟进中");
    }
  });
});
