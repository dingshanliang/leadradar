/**
 * Zod schemas for defensive runtime validation on the frontend.
 *
 * These schemas validate data BEFORE it is sent to the API, catching
 * malformed payloads early. The backend already validates via Pydantic,
 * but frontend validation provides faster feedback and prevents unnecessary
 * network round-trips.
 *
 * Only covers critical write operations:
 * - Scoring config updates
 * - Lead status updates
 * - Follow-up creation
 */
import { z } from "zod";

// ── Shared constants ───────────────────────────────────────────────

export const LEAD_STATUSES = [
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
] as const;

export const GRADE_KEYS = ["S", "A", "B", "C", "D"] as const;

const DIMENSION_KEYS = [
  "budget_strength",
  "scenario_fit",
  "timing",
  "reachability",
  "leverage",
] as const;

// ── Reusable sub-schemas ───────────────────────────────────────────

/** A score mapping: string keys → numbers in [0, 100] */
const scoreRecord = z.record(z.string(), z.number().min(0).max(100));

/** Grade thresholds: S/A/B/C/D → number in [0, 100] */
const gradeThresholds = z.object({
  S: z.number().min(0).max(100),
  A: z.number().min(0).max(100),
  B: z.number().min(0).max(100),
  C: z.number().min(0).max(100),
  D: z.number().min(0).max(100),
});

// ── ScoringRulesUpdate schema ──────────────────────────────────────

export const scoringRulesUpdateSchema = z.object({
  version: z.string().min(1),
  max_scores: scoreRecord,
  grades: gradeThresholds,
  budget_strength: scoreRecord,
  scenario_fit: scoreRecord,
  timing: scoreRecord,
  reachability: scoreRecord,
  leverage: scoreRecord,
});

export type ScoringRulesUpdate = z.infer<typeof scoringRulesUpdateSchema>;

// ── LeadStatusUpdate schema ────────────────────────────────────────

export const leadStatusUpdateSchema = z.object({
  status: z.enum(LEAD_STATUSES),
});

export type LeadStatusUpdate = z.infer<typeof leadStatusUpdateSchema>;

// ── FollowUpCreate schema ──────────────────────────────────────────

export const followUpCreateSchema = z
  .object({
    channel: z.string().min(1),
    result: z.string().min(1).optional(),
    result_category: z.string().min(1).optional(),
    reason: z.string().min(1).optional(),
    notes: z.string().nullable().optional(),
    next_action_at: z.string().nullable().optional(),
    contact_id: z.string().nullable().optional(),
  })
  .refine(
    (data) => {
      if (data.result) return true;
      return Boolean(data.result_category && data.reason);
    },
    {
      message: "必须提供 result 或 result_category 与 reason",
      path: ["result"],
    }
  );

export type FollowUpCreateInput = z.infer<typeof followUpCreateSchema>;

// ── Semantic validation helpers ────────────────────────────────────

/**
 * Validates business rules beyond what zod structural checks can do:
 * 1. max_scores weights must sum to exactly 100
 * 2. Grade thresholds must be strictly decreasing: S > A > B > C > D
 * 3. Each sub-score must not exceed its dimension's max_score
 *
 * Returns an array of human-readable error strings (empty = valid).
 */
export function validateScoringRules(
  data: ScoringRulesUpdate
): string[] {
  const errors: string[] = [];

  // 1. max_scores total must be 100
  const maxScores = data.max_scores;
  const total = Object.values(maxScores).reduce(
    (sum, v) => sum + (Number(v) || 0),
    0
  );
  if (total !== 100) {
    errors.push(`维度权重总和必须等于 100，当前为 ${total}`);
  }

  // 2. Grade thresholds strictly decreasing
  const gradeOrder = GRADE_KEYS as readonly string[];
  for (let i = 0; i < gradeOrder.length - 1; i++) {
    const curr = data.grades[gradeOrder[i] as keyof typeof data.grades];
    const next = data.grades[gradeOrder[i + 1] as keyof typeof data.grades];
    if (curr <= next) {
      errors.push(
        `等级阈值必须严格递减: ${gradeOrder[i]}(${curr}) 应大于 ${gradeOrder[i + 1]}(${next})`
      );
    }
  }

  // 3. Sub-scores must not exceed dimension max_score
  for (const dim of DIMENSION_KEYS) {
    const maxVal = maxScores[dim];
    if (maxVal === undefined) continue;
    const subScores = data[dim] as Record<string, number>;
    if (!subScores) continue;
    for (const [key, val] of Object.entries(subScores)) {
      if (Number(val) > Number(maxVal)) {
        errors.push(
          `${dim}.${key} 的分值 ${val} 超过了该维度满分 ${maxVal}`
        );
      }
    }
  }

  return errors;
}

/**
 * Quick helper to validate a lead status string.
 * Returns a SafeParseReturnType so callers can branch on `.success`.
 */
export function validateLeadStatus(status: string) {
  return z.enum(LEAD_STATUSES).safeParse(status);
}

/**
 * Quick helper to validate a grade string.
 * Returns a SafeParseReturnType so callers can branch on `.success`.
 */
export function validateGrade(grade: string) {
  return z.enum(GRADE_KEYS).safeParse(grade);
}

/**
 * Quick helper to validate a follow-up create payload.
 * Returns a SafeParseReturnType so callers can branch on `.success`.
 */
export function validateFollowUpCreate(data: unknown) {
  return followUpCreateSchema.safeParse(data);
}

// ── TypeScript union types derived from zod constants ────────────

/** Strict union of all valid lead-status values. */
export type LeadStatus = (typeof LEAD_STATUSES)[number];

/** Strict union of all valid grade values. */
export type Grade = (typeof GRADE_KEYS)[number];
