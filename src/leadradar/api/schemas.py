from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ── Source ────────────────────────────────────────────────────────


class SourceOut(BaseModel):
    id: UUID
    name: str
    source_type: str
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
    result: str
    notes: str | None = None
    contact_id: UUID | None = None


class FollowUpOut(BaseModel):
    id: UUID
    lead_id: UUID
    contact_id: UUID | None = None
    channel: str
    result: str
    notes: str | None = None
    next_action_at: datetime | None = None
    created_at: datetime
