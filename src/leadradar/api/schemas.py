from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, model_validator


# ── User ──────────────────────────────────────────────────────────


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    display_name: str | None = None


# ── Source ────────────────────────────────────────────────────────


class SourceOut(BaseModel):
    id: UUID
    name: str
    source_type: str
    source_key: str | None = None
    base_url: str | None = None
    priority: str | None = None
    enabled: bool = True
    rate_limit_per_minute: int = 20
    created_at: datetime


# ── Document ──────────────────────────────────────────────────────


class DocumentOut(BaseModel):
    id: UUID
    source_id: UUID | None = None
    url: str
    title: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime
    parse_status: str
    document_type: str | None = None


# ── Signal (nested in lead detail) ───────────────────────────────


class SignalBrief(BaseModel):
    id: UUID
    signal_type: str
    title: str | None = None
    budget_amount: float | None = None
    source_url: str | None = None
    evidence_text: str | None = None
    confidence: float
    created_at: datetime


# ── Organization (nested in lead detail) ──────────────────────────


class OrganizationBrief(BaseModel):
    id: UUID
    name: str
    province: str | None = None
    city: str | None = None
    county: str | None = None
    organization_type: str | None = None


# ── Score (nested in lead detail & list) ──────────────────────────


class ScoreBrief(BaseModel):
    total_score: int
    grade: str
    budget_strength_score: int = 0
    scenario_fit_score: int = 0
    timing_score: int = 0
    reachability_score: int = 0
    leverage_score: int = 0


# ── Lead list item ────────────────────────────────────────────────


class LeadListItem(BaseModel):
    id: UUID
    organization_name: str | None = None
    customer_type: str | None = None
    recommended_package: str | None = None
    budget_bucket: str | None = None
    signal_type: str | None = None
    province: str | None = None
    lead_status: str
    total_score: int
    grade: str
    created_at: datetime


# ── Lead detail ───────────────────────────────────────────────────


class CallScript(BaseModel):
    opening: str
    questions: list[str]
    wechat_follow_up: str


class LeadDetail(BaseModel):
    id: UUID
    organization: OrganizationBrief
    signal: SignalBrief
    score: ScoreBrief
    call_script: CallScript
    customer_type: str | None = None
    recommended_package: str | None = None
    budget_bucket: str | None = None
    lead_status: str
    owner: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Status update ─────────────────────────────────────────────────


class StatusUpdate(BaseModel):
    status: str


# ── Follow-up ─────────────────────────────────────────────────────


class FollowUpCreate(BaseModel):
    channel: str
    result: str | None = None
    result_category: str | None = None
    reason: str | None = None
    notes: str | None = None
    next_action_at: datetime | None = None
    contact_id: UUID | None = None


class FollowUpOut(BaseModel):
    id: UUID
    lead_id: UUID
    contact_id: UUID | None = None
    channel: str
    result: str
    result_category: str | None = None
    reason: str | None = None
    notes: str | None = None
    next_action_at: datetime | None = None
    created_at: datetime

    @model_validator(mode="after")
    def _derive_category_and_reason(self) -> "FollowUpOut":
        if ":" in self.result:
            self.result_category, self.reason = self.result.split(":", 1)
        else:
            self.result_category = None
            self.reason = None
        return self


class FollowUpSuggestionOut(BaseModel):
    result: str
    next_action_at: datetime | None = None


# ── Stats ─────────────────────────────────────────────────────────


class DistributionItem(BaseModel):
    name: str
    count: int


class StatsOut(BaseModel):
    total: int
    sa_count: int
    pending: int
    scheduled: int
    invalid: int
    invalid_rate: str
    signal_type_distribution: list[DistributionItem]
    package_distribution: list[DistributionItem]
    province_distribution: list[DistributionItem]


# ── Meta ─────────────────────────────────────────────────────────


class EnumItem(BaseModel):
    key: str
    label: str


class MetaOut(BaseModel):
    signal_types: list[EnumItem]
    statuses: list[EnumItem]
    grades: list[str]
    budget_buckets: list[str]


# ── Config ───────────────────────────────────────────────────────


class KeywordGroup(BaseModel):
    name: str
    description: str
    keywords: list[str]


class ScoringDimension(BaseModel):
    name: str
    max_score: int
    description: str


class ProductPackage(BaseModel):
    name: str
    target: str
    desc: str


class ConfigOut(BaseModel):
    keyword_groups: list[KeywordGroup]
    scoring_dimensions: list[ScoringDimension]
    product_packages: list[ProductPackage]


# ── Weekly Report ────────────────────────────────────────────────


class WeeklyReport(BaseModel):
    new_leads: int
    followed_up: int
    contacted: int
    scheduled: int
    won: int
    lost: int
    conversion_rate: str



# ── Manual Generation ─────────────────────────────────────────────


class ManualTaskCreate(BaseModel):
    source_keys: list[str]
    keyword_mode: str = "by_group"
    keyword_groups: list[str] | None = None
    keywords: list[str] | None = None


class ManualSubtaskOut(BaseModel):
    id: UUID
    source_key: str
    source_id: UUID
    query: str
    keyword_group: str
    keyword: str | None = None
    status: str
    created_leads_count: int
    skipped_duplicate_count: int
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ManualTaskOut(BaseModel):
    id: UUID
    keyword_mode: str
    status: str
    total_subtasks: int
    completed_subtasks: int
    created_leads_count: int
    skipped_duplicate_count: int
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    subtasks: list[ManualSubtaskOut] = []
