from __future__ import annotations

from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlmodel import Session, select

from leadradar.adapters.export_adapters import CsvExportAdapter, XlsxExportAdapter
from leadradar.api.schemas import (
    BlocklistOut,
    ConfigOut,
    DocumentOut,
    DueFollowUp,
    EnumItem,
    FollowUpCreate,
    FollowUpOut,
    FollowUpSuggestionOut,
    KeywordGroup,
    LeadDetail,
    LeadListItem,
    MetaOut,
    ProductPackage,
    ScoringDimension,
    SourceOut,
    StatsOut,
    StatusUpdate,
    WeeklyReport,
)
from leadradar.auth import User, get_current_user
from leadradar.db import get_session
from leadradar.models import (
    SIGNAL_TYPE_LABELS,
    FollowUp,
    Lead,
    LeadStatus,
    RawDocument,
    Source,
)
from leadradar.services.config_service import (
    ScoringRulesUpdate,
    load_scoring_rules,
    update_scoring_rules,
)
from leadradar.services.lead_export_service import LeadExportService
from leadradar.services.lead_query_service import LeadQueryService
from leadradar.services.follow_up_config import (
    get_follow_up_suggestion as _get_follow_up_suggestion,
    validate_reason,
)
from leadradar.services.blacklist_service import BlacklistService
from leadradar.services.lead_stats_service import LeadStatsService

router = APIRouter(prefix="/api/v1")


# ── Stats ─────────────────────────────────────────────────────────


@router.get("/stats", response_model=StatsOut)
def get_stats(session: Session = Depends(get_session)):
    return LeadStatsService().get_stats(session)


@router.get("/weekly-report", response_model=WeeklyReport)
def get_weekly_report(session: Session = Depends(get_session)):
    return LeadStatsService().get_weekly_report(session)


# ── Sources ───────────────────────────────────────────────────────


@router.get("/meta", response_model=MetaOut)
def get_meta():
    return MetaOut(
        signal_types=[EnumItem(key=k, label=v) for k, v in SIGNAL_TYPE_LABELS.items()],
        statuses=[EnumItem(key=s.value, label=s.label) for s in LeadStatus],
        grades=["S", "A", "B", "C", "D"],
        budget_buckets=["<10万", "10-50万", "50-100万", "100-500万", ">500万"],
    )


@router.get("/config", response_model=ConfigOut)
def get_config():
    import yaml

    data_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"

    with open(data_dir / "keywords.yml", encoding="utf-8") as f:
        kw_raw = yaml.safe_load(f)

    keyword_groups = [
        KeywordGroup(name=k, description=v["description"], keywords=v["keywords"])
        for k, v in kw_raw.get("keyword_groups", {}).items()
    ]

    with open(data_dir / "scoring_rules.yml", encoding="utf-8") as f:
        score_raw = yaml.safe_load(f)

    max_scores = score_raw.get("max_scores", {})
    dim_descriptions = {
        "budget_strength": "预算金额大小和确定性",
        "scenario_fit": "与公司产品服务的匹配度",
        "timing": "采购时间紧迫性",
        "reachability": "联系方式可获得性",
        "leverage": "影响成交的有利因素",
    }
    dim_names = {
        "budget_strength": "预算强度",
        "scenario_fit": "场景匹配",
        "timing": "时间窗口",
        "reachability": "可触达性",
        "leverage": "成交杠杆",
    }
    scoring_dimensions = [
        ScoringDimension(
            name=dim_names.get(k, k),
            max_score=v,
            description=dim_descriptions.get(k, ""),
        )
        for k, v in max_scores.items()
    ]

    product_packages = [
        ProductPackage(
            name="区域品牌数字化管理包",
            target="区域品牌政府",
            desc="品牌数字化管理平台 + 溯源系统 + 包装设计",
        ),
        ProductPackage(
            name="食品企业合规包",
            target="食品企业",
            desc="标签合规 + 检测报告管理 + 溯源系统",
        ),
        ProductPackage(
            name="包装升级方案包",
            target="包装需求企业",
            desc="包装设计 + 印刷管理 + 供应链优化",
        ),
        ProductPackage(
            name="展会数字化展示包",
            target="参展企业",
            desc="电子画册 + 二维码展示 + 客户管理",
        ),
    ]

    return ConfigOut(
        keyword_groups=keyword_groups,
        scoring_dimensions=scoring_dimensions,
        product_packages=product_packages,
    )


@router.get("/config/scoring")
def get_scoring_config():
    return load_scoring_rules()


@router.put("/config/scoring")
def put_scoring_config(payload: ScoringRulesUpdate):
    try:
        update_scoring_rules(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True}


@router.get("/sources", response_model=list[SourceOut])
def list_sources(session: Session = Depends(get_session)):
    sources = session.exec(select(Source).order_by(Source.created_at.desc())).all()
    return sources


# ── Documents ─────────────────────────────────────────────────────


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(session: Session = Depends(get_session)):
    docs = session.exec(select(RawDocument).order_by(RawDocument.fetched_at.desc())).all()
    return docs


# ── Leads ─────────────────────────────────────────────────────────


@router.get("/leads", response_model=list[LeadListItem])
def list_leads(
    grade: str | None = None,
    status: str | None = None,
    signal_type: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    return LeadQueryService().list_leads(
        session,
        grade=grade,
        status=status,
        signal_type=signal_type,
        limit=limit,
        offset=offset,
    )


# ── Export (MUST be before /leads/{lead_id} to avoid path collision) ──


@router.get("/leads/export")
def export_leads(
    format: Literal["csv", "xlsx"] = Query(...),
    grade: str | None = None,
    session: Session = Depends(get_session),
):
    rows = LeadExportService().build_export_rows(session, grade=grade)

    if format == "csv":
        adapter = CsvExportAdapter()
        content = adapter.render(rows)
        return _csv_response(content, adapter.filename())
    else:
        adapter = XlsxExportAdapter()
        content = adapter.render(rows)
        return _xlsx_response(content, adapter.filename())


# ── Lead Detail ───────────────────────────────────────────────────


@router.get("/leads/{lead_id}", response_model=LeadDetail)
def get_lead_detail(lead_id: UUID, session: Session = Depends(get_session)):
    detail = LeadQueryService().get_lead_detail(session, lead_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return detail


# ── Lead Status Update ───────────────────────────────────────────


@router.patch("/leads/{lead_id}/status")
def update_lead_status(
    lead_id: UUID,
    body: StatusUpdate,
    session: Session = Depends(get_session),
):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        lead.lead_status = LeadStatus(body.status)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status: {body.status}. Valid: {[s.value for s in LeadStatus]}",
        )

    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


# ── Follow-ups ───────────────────────────────────────────────────


@router.post("/leads/{lead_id}/follow-ups", status_code=201, response_model=FollowUpOut)
def create_follow_up(
    lead_id: UUID,
    body: FollowUpCreate,
    session: Session = Depends(get_session),
):
    from datetime import datetime, timezone

    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    next_action_at = body.next_action_at
    if next_action_at is not None:
        if next_action_at.tzinfo is None:
            next_action_at = next_action_at.replace(tzinfo=timezone.utc)
        if next_action_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=422, detail="下次跟进时间必须晚于当前时间")

    result = body.result
    if not result:
        if not body.result_category:
            raise HTTPException(status_code=422, detail="result_category 字段必填")
        if not body.reason:
            raise HTTPException(status_code=422, detail="reason 字段必填")
        try:
            validate_reason(body.result_category, body.reason)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        result = f"{body.result_category}:{body.reason}"

    follow_up = FollowUp(
        lead_id=lead_id,
        contact_id=body.contact_id,
        channel=body.channel,
        result=result,
        notes=body.notes,
        next_action_at=next_action_at,
    )
    session.add(follow_up)

    if body.result_category == "无效":
        BlacklistService().block_lead_and_organization(
            session,
            lead,
            reason=body.reason or "",
            block_organization=body.block_organization if body.block_organization is not None else True,
        )

    session.commit()
    session.refresh(follow_up)
    return follow_up


@router.get("/leads/{lead_id}/follow-ups", response_model=list[FollowUpOut])
def list_follow_ups(lead_id: UUID, session: Session = Depends(get_session)):
    follow_ups = session.exec(
        select(FollowUp).where(FollowUp.lead_id == lead_id).order_by(FollowUp.created_at.desc())
    ).all()
    return follow_ups


# ── Due follow-ups ───────────────────────────────────────────────


@router.get("/follow-ups/due", response_model=list[DueFollowUp])
def list_due_follow_ups(
    _user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    from leadradar.services.due_follow_up_service import DueFollowUpService

    return DueFollowUpService().list_due_follow_ups(session)


class DueFollowUpCount(BaseModel):
    count: int


@router.get("/follow-ups/due/count", response_model=DueFollowUpCount)
def get_due_follow_up_count(
    _user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    from leadradar.services.due_follow_up_service import DueFollowUpService

    return DueFollowUpCount(count=DueFollowUpService().count_due_follow_ups(session))


# ── Follow-up suggestion ──────────────────────────────────────────


@router.get("/follow-up-suggestion", response_model=FollowUpSuggestionOut)
def get_follow_up_suggestion(
    result: str = Query(...),
):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    suggested_at = _get_follow_up_suggestion(result, now=now)
    return FollowUpSuggestionOut(result=result, next_action_at=suggested_at)


# ── Crawl ─────────────────────────────────────────────────────────


class CrawlRequest(BaseModel):
    query: str
    source: str = "ccgp"


@router.post("/crawl/trigger")
async def trigger_crawl(body: CrawlRequest, session: Session = Depends(get_session)):
    from leadradar.crawlers.ggzy import CaptchaRequiredError
    from leadradar.crawlers.registry import get_providers
    from leadradar.services.crawler_service import CrawlerService

    try:
        search, fetch = get_providers(body.source)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = CrawlerService(session=session, search=search, fetch=fetch)
    try:
        task = await service.crawl(body.query)
    except CaptchaRequiredError as e:
        return {
            "task_id": None,
            "status": "captcha_required",
            "message": "GGZY requires CAPTCHA verification",
            "captcha_token": e.captcha_token,
        }

    return {
        "task_id": str(task.id),
        "status": task.status.value,
        "message": task.error_message or "completed",
    }


class PipelineRequest(BaseModel):
    query: str
    source: str = "ccgp"


@router.post("/pipeline/run")
async def run_pipeline(body: PipelineRequest, session: Session = Depends(get_session)):
    from leadradar.crawlers.registry import get_providers
    from leadradar.llm.extraction import MockLLMProvider
    from leadradar.services.pipeline import run_pipeline as _run_pipeline

    try:
        search, fetch = get_providers(body.source)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = await _run_pipeline(
        query=body.query,
        session=session,
        search=search,
        fetch=fetch,
        llm=MockLLMProvider(),
    )
    return {
        "documents": len(result.documents),
        "leads": len(result.leads),
        "skipped_irrelevant": result.skipped_irrelevant,
        "errors": result.errors,
    }


# ── Blocklist ─────────────────────────────────────────────────────


@router.get("/blocklist", response_model=list[BlocklistOut])
def list_blocklist(
    _user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return BlacklistService().list_blocklist(session)


@router.delete("/blocklist/{block_id}", status_code=204)
def delete_blocklist_record(
    block_id: UUID,
    _user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    success = BlacklistService().unblock_organization(session, block_id)
    if not success:
        raise HTTPException(status_code=404, detail="Blocklist record not found")
    return Response(status_code=204)


# ── Response helpers ──────────────────────────────────────────────


def _csv_response(content: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _xlsx_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
