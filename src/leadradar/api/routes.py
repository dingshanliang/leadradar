from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from openpyxl import Workbook
from sqlmodel import Session, select

from leadradar.api.schemas import (
    CallScript,
    ConfigOut,
    DistributionItem,
    DocumentOut,
    EnumItem,
    FollowUpCreate,
    FollowUpOut,
    KeywordGroup,
    LeadDetail,
    LeadListItem,
    MetaOut,
    OrganizationBrief,
    ProductPackage,
    ScoreBrief,
    ScoringDimension,
    SignalBrief,
    SourceOut,
    StatsOut,
    StatusUpdate,
)
from leadradar.db import get_session
from leadradar.models import (
    SIGNAL_TYPE_LABELS,
    FollowUp,
    Lead,
    LeadScore,
    LeadStatus,
    Organization,
    RawDocument,
    Signal,
    Source,
)
from leadradar.services.call_script import generate_call_script as _gen_script

router = APIRouter(prefix="/api/v1")


# ── Stats ─────────────────────────────────────────────────────────


@router.get("/stats", response_model=StatsOut)
def get_stats(session: Session = Depends(get_session)):
    rows = session.exec(
        select(Lead, LeadScore, Organization, Signal)
        .join(LeadScore, LeadScore.lead_id == Lead.id)
        .join(Organization, Organization.id == Lead.organization_id)
        .outerjoin(Signal, Signal.id == Lead.primary_signal_id)
    ).all()

    total = len(rows)
    sa_count = sum(1 for _, score, _, _ in rows if score.grade in ("S", "A"))
    pending = sum(
        1 for lead, _, _, _ in rows
        if lead.lead_status.value in ("new", "qualified")
    )
    scheduled = sum(
        1 for lead, _, _, _ in rows if lead.lead_status.value == "diagnosis_scheduled"
    )
    invalid = sum(1 for lead, _, _, _ in rows if lead.lead_status.value == "invalid")
    invalid_rate = f"{(invalid / total * 100):.1f}" if total > 0 else "0"

    def _distribution(key_fn):
        counts: dict[str, int] = {}
        for lead, _, org, signal in rows:
            k = key_fn(lead, org, signal)
            counts[k] = counts.get(k, 0) + 1
        return [
            DistributionItem(name=k, count=v)
            for k, v in sorted(counts.items(), key=lambda x: -x[1])
        ]

    return StatsOut(
        total=total,
        sa_count=sa_count,
        pending=pending,
        scheduled=scheduled,
        invalid=invalid,
        invalid_rate=invalid_rate,
        signal_type_distribution=_distribution(
            lambda _, __, signal: signal.signal_type if signal else "unknown"
        )[:8],
        package_distribution=_distribution(
            lambda lead, _, __: lead.recommended_package or "未分类"
        ),
        province_distribution=_distribution(
            lambda _, org, __: org.province or "未知"
        )[:8],
    )


# ── Sources ───────────────────────────────────────────────────────


@router.get("/meta", response_model=MetaOut)
def get_meta():
    return MetaOut(
        signal_types=[
            EnumItem(key=k, label=v) for k, v in SIGNAL_TYPE_LABELS.items()
        ],
        statuses=[
            EnumItem(key=s.value, label=s.label) for s in LeadStatus
        ],
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
    query = (
        select(Lead, LeadScore, Organization, Signal)
        .join(LeadScore, LeadScore.lead_id == Lead.id)
        .join(Organization, Organization.id == Lead.organization_id)
        .outerjoin(Signal, Signal.id == Lead.primary_signal_id)
        .order_by(Lead.created_at.desc())
    )
    if grade:
        query = query.where(LeadScore.grade == grade.upper())
    if status:
        query = query.where(Lead.lead_status == status)
    if signal_type:
        query = query.where(Signal.signal_type == signal_type)

    query = query.offset(offset).limit(limit)
    rows = session.exec(query).all()

    results = []
    for lead, score, org, signal in rows:
        results.append(
            LeadListItem(
                id=lead.id,
                organization_name=org.name,
                customer_type=lead.customer_type,
                recommended_package=lead.recommended_package,
                budget_bucket=lead.budget_bucket,
                signal_type=signal.signal_type if signal else None,
                province=org.province,
                lead_status=lead.lead_status.value if isinstance(lead.lead_status, LeadStatus) else lead.lead_status,
                total_score=score.total_score,
                grade=score.grade,
                created_at=lead.created_at,
            )
        )
    return results


# ── Export (MUST be before /leads/{lead_id} to avoid path collision) ──


@router.get("/leads/export")
def export_leads(
    format: Literal["csv", "xlsx"] = Query(...),
    grade: str | None = None,
    session: Session = Depends(get_session),
):
    query = (
        select(Lead, LeadScore, Organization, Signal)
        .join(LeadScore, LeadScore.lead_id == Lead.id)
        .join(Organization, Organization.id == Lead.organization_id)
        .outerjoin(Signal, Signal.id == Lead.primary_signal_id)
    )
    if grade:
        query = query.where(LeadScore.grade == grade.upper())

    rows = session.exec(query).all()

    columns = [
        "organization_name",
        "lead_status",
        "grade",
        "total_score",
        "customer_type",
        "recommended_package",
        "budget_bucket",
        "signal_type",
        "budget_amount",
        "source_url",
        "evidence_text",
    ]

    data_rows = []
    for lead, score, org, signal in rows:
        data_rows.append({
            "organization_name": org.name,
            "lead_status": lead.lead_status.value if isinstance(lead.lead_status, LeadStatus) else lead.lead_status,
            "grade": score.grade,
            "total_score": score.total_score,
            "customer_type": lead.customer_type or "",
            "recommended_package": lead.recommended_package or "",
            "budget_bucket": lead.budget_bucket or "",
            "signal_type": signal.signal_type if signal else "",
            "budget_amount": signal.budget_amount if signal else "",
            "source_url": signal.source_url if signal else "",
            "evidence_text": signal.evidence_text if signal else "",
        })

    if format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data_rows)
        return _csv_response(buf.getvalue(), "leads.csv")
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "线索列表"
        ws.append(columns)
        for row in data_rows:
            ws.append([row[c] for c in columns])
        buf = io.BytesIO()
        wb.save(buf)
        return _xlsx_response(buf.getvalue(), "leads.xlsx")


# ── Lead Detail ───────────────────────────────────────────────────


@router.get("/leads/{lead_id}", response_model=LeadDetail)
def get_lead_detail(lead_id: UUID, session: Session = Depends(get_session)):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    score = session.exec(
        select(LeadScore).where(LeadScore.lead_id == lead_id)
    ).first()

    org = session.get(Organization, lead.organization_id) if lead.organization_id else None

    signal = session.get(Signal, lead.primary_signal_id) if lead.primary_signal_id else None

    if not score or not org or not signal:
        raise HTTPException(status_code=404, detail="Incomplete lead data")

    script_data = _gen_script(
        customer_type=lead.customer_type,
        organization_name=org.name,
        signal_title=signal.title,
        signal_type=signal.signal_type,
        recommended_package=lead.recommended_package,
        budget_amount=signal.budget_amount,
    )

    return LeadDetail(
        id=lead.id,
        organization=OrganizationBrief(
            id=org.id,
            name=org.name,
            province=org.province,
            city=org.city,
            county=org.county,
            organization_type=org.organization_type,
        ),
        signal=SignalBrief(
            id=signal.id,
            signal_type=signal.signal_type,
            title=signal.title,
            budget_amount=signal.budget_amount,
            source_url=signal.source_url,
            evidence_text=signal.evidence_text,
            confidence=signal.confidence,
            created_at=signal.created_at,
        ),
        score=ScoreBrief(
            total_score=score.total_score,
            grade=score.grade,
            budget_strength_score=score.budget_strength_score,
            scenario_fit_score=score.scenario_fit_score,
            timing_score=score.timing_score,
            reachability_score=score.reachability_score,
            leverage_score=score.leverage_score,
        ),
        call_script=CallScript(**script_data),
        customer_type=lead.customer_type,
        recommended_package=lead.recommended_package,
        budget_bucket=lead.budget_bucket,
        lead_status=lead.lead_status.value if isinstance(lead.lead_status, LeadStatus) else lead.lead_status,
        owner=lead.owner,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


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
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    follow_up = FollowUp(
        lead_id=lead_id,
        contact_id=body.contact_id,
        channel=body.channel,
        result=body.result,
        notes=body.notes,
    )
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    return follow_up


@router.get("/leads/{lead_id}/follow-ups", response_model=list[FollowUpOut])
def list_follow_ups(lead_id: UUID, session: Session = Depends(get_session)):
    follow_ups = session.exec(
        select(FollowUp)
        .where(FollowUp.lead_id == lead_id)
        .order_by(FollowUp.created_at.desc())
    ).all()
    return follow_ups


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
