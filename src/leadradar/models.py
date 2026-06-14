from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class LeadStatus(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CALLED = "called"
    CONNECTED = "connected"
    DIAGNOSIS_SCHEDULED = "diagnosis_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    WON = "won"
    LOST = "lost"
    INVALID = "invalid"
    BLOCKED = "blocked"

    @property
    def label(self) -> str:
        return {
            "new": "新建",
            "qualified": "已验证",
            "called": "已拨打",
            "connected": "已接通",
            "diagnosis_scheduled": "已预约诊断",
            "proposal_sent": "已发送方案",
            "won": "已成交",
            "lost": "已流失",
            "invalid": "无效",
            "blocked": "已屏蔽",
        }[self.value]


class ManualTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_FAILED = "partial_failed"


class ManualSubtaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class KeywordMode(str, Enum):
    BY_GROUP = "by_group"
    BY_KEYWORD = "by_keyword"


SIGNAL_TYPE_LABELS: dict[str, str] = {
    "procurement_intent": "采购意向",
    "tender_notice": "招标公告",
    "winning_notice": "中标公告",
    "contract_notice": "合同公告",
    "certification_registry": "认证登记",
    "recruiting_signal": "招聘信号",
    "exhibition_signal": "展会信号",
    "product_launch": "产品发布",
    "packaging_upgrade": "包装升级",
    "channel_partner": "渠道合作",
    "company_website": "企业官网",
    "news_report": "新闻报道",
}


class Source(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    source_type: str
    source_key: Optional[str] = None
    base_url: Optional[str] = None
    priority: Optional[str] = None
    crawl_mode: Optional[str] = None
    enabled: bool = True
    rate_limit_per_minute: int = 20
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CrawlTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlTask(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_id: Optional[UUID] = Field(default=None, foreign_key="source.id")
    query: Optional[str] = None
    status: CrawlTaskStatus = CrawlTaskStatus.PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExtractionRunStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionRun(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    raw_document_id: UUID = Field(foreign_key="rawdocument.id")
    llm_provider: str
    model: str
    prompt_version: str = "0.1"
    raw_response: Optional[str] = None
    parsed_json: Optional[str] = None
    confidence: float = 0.0
    status: ExtractionRunStatus = ExtractionRunStatus.PENDING
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RawDocument(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_id: Optional[UUID] = Field(default=None, foreign_key="source.id")
    url: str
    title: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    raw_html: Optional[str] = None
    extracted_text: Optional[str] = None
    content_hash: Optional[str] = None
    document_type: Optional[str] = None
    parse_status: str = "pending"


class Organization(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    normalized_name: Optional[str] = None
    organization_type: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    industry: Optional[str] = None
    official_website: Optional[str] = None
    public_phone: Optional[str] = None
    public_email: Optional[str] = None
    credit_code: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Signal(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    raw_document_id: Optional[UUID] = Field(default=None, foreign_key="rawdocument.id")
    organization_id: Optional[UUID] = Field(default=None, foreign_key="organization.id")
    signal_type: str
    title: Optional[str] = None
    summary: Optional[str] = None
    budget_amount: Optional[float] = None
    expected_time: Optional[str] = None
    published_at: Optional[datetime] = None
    matched_keywords_json: Optional[str] = None
    source_url: Optional[str] = None
    evidence_text: Optional[str] = None
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Lead(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, foreign_key="organization.id")
    primary_signal_id: Optional[UUID] = Field(default=None, foreign_key="signal.id")
    customer_type: Optional[str] = None
    recommended_package: Optional[str] = None
    budget_bucket: Optional[str] = None
    lead_status: LeadStatus = LeadStatus.NEW
    owner: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LeadScore(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    lead_id: UUID = Field(foreign_key="lead.id")
    total_score: int
    grade: str
    budget_strength_score: int = 0
    scenario_fit_score: int = 0
    timing_score: int = 0
    reachability_score: int = 0
    leverage_score: int = 0
    score_reason_json: Optional[str] = None
    version: str = "0.1"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Contact(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, foreign_key="organization.id")
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source_url: Optional[str] = None
    is_public_business_contact: bool = True
    do_not_contact: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FollowUp(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    lead_id: UUID = Field(foreign_key="lead.id")
    contact_id: Optional[UUID] = Field(default=None, foreign_key="contact.id")
    channel: str
    result: str
    notes: Optional[str] = None
    next_action_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Blocklist(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, foreign_key="organization.id")
    contact_value_hash: Optional[str] = None
    reason: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ManualTask(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    keyword_mode: KeywordMode = KeywordMode.BY_GROUP
    status: ManualTaskStatus = ManualTaskStatus.PENDING
    total_subtasks: int = 0
    completed_subtasks: int = 0
    created_leads_count: int = 0
    skipped_duplicate_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class ManualSubtask(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    manual_task_id: UUID = Field(foreign_key="manualtask.id")
    source_key: str
    source_id: UUID = Field(foreign_key="source.id")
    query: str
    keyword_group: str
    keyword: Optional[str] = None
    status: ManualSubtaskStatus = ManualSubtaskStatus.PENDING
    created_leads_count: int = 0
    skipped_duplicate_count: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
