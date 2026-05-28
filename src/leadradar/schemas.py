from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


ProductPackage = Literal[
    "数字标签合规启动包",
    "溯源信任包",
    "包装扫码增长包",
    "区域品牌数字化管理包",
    "渠道白标工具包",
]

SignalType = Literal[
    "procurement_intent",
    "tender_notice",
    "winning_notice",
    "contract_notice",
    "certification_registry",
    "recruiting_signal",
    "exhibition_signal",
    "product_launch",
    "packaging_upgrade",
    "channel_partner",
    "company_website",
    "news_report",
    "irrelevant",
]


class Evidence(BaseModel):
    field: str
    text: str


class BudgetAmount(BaseModel):
    value: float | None = None
    currency: str = "CNY"
    raw: str | None = None


class Region(BaseModel):
    province: str | None = None
    city: str | None = None
    county: str | None = None


class ExtractionResult(BaseModel):
    is_relevant: bool
    signal_type: SignalType
    customer_type: str | None = None
    organization_name: str | None = None
    project_name: str | None = None
    budget_amount: BudgetAmount | None = None
    expected_time: str | None = None
    region: Region | None = None
    need_summary: str | None = None
    matched_keywords: list[str] = Field(default_factory=list)
    product_fit: list[ProductPackage] = Field(default_factory=list)
    budget_source_guess: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    uncertainties: list[str] = Field(default_factory=list)


class LeadScoringInput(BaseModel):
    signal_type: str
    scenario_flags: list[str] = Field(default_factory=list)
    timing_flags: list[str] = Field(default_factory=list)
    reachability_flags: list[str] = Field(default_factory=list)
    leverage_flags: list[str] = Field(default_factory=list)


class LeadScoringResult(BaseModel):
    total_score: int
    grade: Literal["S", "A", "B", "C", "D"]
    breakdown: dict[str, int]
    reasons: list[str]
