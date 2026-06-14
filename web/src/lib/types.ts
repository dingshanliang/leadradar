// Convenience type aliases from auto-generated api-types.ts.
// Do NOT add new hand-written types here.  Add them to the backend Pydantic
// schema and regenerate api-types.ts instead.

import type { components } from "./api-types";

// ── domain types (auto-generated from OpenAPI) ───────────────────

export type Source = components["schemas"]["SourceOut"];
export type Document = components["schemas"]["DocumentOut"];
export type LeadListItem = components["schemas"]["LeadListItem"];
export type OrganizationBrief = components["schemas"]["OrganizationBrief"];
export type SignalBrief = components["schemas"]["SignalBrief"];
export type ScoreBrief = components["schemas"]["ScoreBrief"];
export type CallScript = components["schemas"]["CallScript"];
export type LeadDetail = components["schemas"]["LeadDetail"];
export type FollowUpCreate = components["schemas"]["FollowUpCreate"];
export type FollowUpOut = components["schemas"]["FollowUpOut"];
export type DueFollowUp = components["schemas"]["DueFollowUp"];
export type Stats = components["schemas"]["StatsOut"];
export type Meta = components["schemas"]["MetaOut"];
export type EnumItem = components["schemas"]["EnumItem"];
export type DistributionItem = components["schemas"]["DistributionItem"];
export type AppConfig = components["schemas"]["ConfigOut"];
export type KeywordGroup = components["schemas"]["KeywordGroup"];
export type ScoringDimension = components["schemas"]["ScoringDimension"];
export type ProductPackage = components["schemas"]["ProductPackage"];
export type ManualTaskCreate = components["schemas"]["ManualTaskCreate"];
export type ManualTaskOut = components["schemas"]["ManualTaskOut"];
export type ManualSubtaskOut = components["schemas"]["ManualSubtaskOut"];

// ── filter / query types (not in OpenAPI schemas) ────────────────

export interface LeadFilters {
  grade?: string;
  status?: string;
  signal_type?: string;
  limit?: number;
  offset?: number;
}

// ── enums (derived from schemas.ts for strict typing) ────────────

export type { Grade, LeadStatus } from "./schemas";
