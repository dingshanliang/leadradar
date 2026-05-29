from __future__ import annotations

import json
from typing import Tuple

from sqlmodel import Session, select

from leadradar.llm.extraction import LLMProvider, validate_extraction
from leadradar.models import (
    ExtractionRun,
    ExtractionRunStatus,
    Lead,
    LeadScore,
    Organization,
    RawDocument,
    Signal,
)
from leadradar.schemas import ExtractionResult, LeadScoringInput
from leadradar.scoring import score_lead
from leadradar.services.flag_derivation import default_engine
from leadradar.services.lead_conversion import (
    LeadConversionEngine,
    OrganizationData,
)


# ── T-501: RawDocument → ExtractionRun → Signal ───────────────


async def document_to_signal(
    *,
    document: RawDocument,
    llm: LLMProvider,
    session: Session,
) -> Tuple[ExtractionRun, Signal | None]:
    """Extract a Signal from a RawDocument via LLM.

    Returns (ExtractionRun, Signal | None). Signal is None when the
    document is judged irrelevant by the LLM.
    """
    result = await llm.extract(
        text=document.extracted_text or "",
        url=document.url,
        title=document.title,
    )
    result = validate_extraction(result)

    meta = getattr(result, "__extraction_meta", None)

    extraction_run = ExtractionRun(
        raw_document_id=document.id,
        llm_provider=llm.__class__.__name__,
        model="mock-v1",
        raw_response=result.model_dump_json(),
        parsed_json=result.model_dump_json(),
        confidence=result.confidence,
        status=ExtractionRunStatus.COMPLETED,
        input_tokens=meta.input_tokens if meta else None,
        output_tokens=meta.output_tokens if meta else None,
        latency_ms=meta.latency_ms if meta else None,
    )
    session.add(extraction_run)

    if not result.is_relevant:
        session.commit()
        session.refresh(extraction_run)
        return extraction_run, None

    signal = _extraction_result_to_signal(result, document)
    session.add(signal)
    session.commit()
    session.refresh(extraction_run)
    session.refresh(signal)

    return extraction_run, signal


def _extraction_result_to_signal(result: ExtractionResult, document: RawDocument) -> Signal:
    """Map an ExtractionResult to a Signal model instance."""
    evidence_texts = [e.text for e in result.evidence]
    return Signal(
        raw_document_id=document.id,
        signal_type=result.signal_type,
        title=result.project_name or document.title,
        summary=result.need_summary,
        budget_amount=result.budget_amount.value if result.budget_amount else None,
        expected_time=result.expected_time,
        published_at=document.published_at,
        matched_keywords_json=json.dumps(result.matched_keywords, ensure_ascii=False),
        source_url=document.url,
        evidence_text="\n".join(evidence_texts),
        confidence=result.confidence,
    )


# ── T-502: Signal → Organization → Lead → LeadScore ───────────


def signal_to_scored_lead(
    *,
    signal: Signal,
    session: Session,
) -> Tuple[Organization, Lead, LeadScore]:
    """Convert a Signal into a scored Lead.

    Finds or creates the Organization, creates a Lead, derives scoring
    flags, and produces a LeadScore.
    """
    extraction_run = _get_extraction_run_for_signal(signal, session)
    extraction_result = _parse_extraction_result(extraction_run)

    # Pure conversion: no DB side effects
    conversion = LeadConversionEngine(flag_engine=default_engine()).convert(
        signal, extraction_result
    )

    # Persistence: organisation (with dedup), lead, score
    org = _persist_organization(conversion.organization_data, session)
    signal.organization_id = org.id
    session.add(signal)

    lead = Lead(
        organization_id=org.id,
        primary_signal_id=signal.id,
        customer_type=conversion.lead_data.customer_type,
        recommended_package=conversion.lead_data.recommended_package,
        budget_bucket=conversion.lead_data.budget_bucket,
        lead_status=conversion.lead_data.lead_status,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)

    lead_score = LeadScore(
        lead_id=lead.id,
        total_score=conversion.lead_score_data.total_score,
        grade=conversion.lead_score_data.grade,
        budget_strength_score=conversion.lead_score_data.budget_strength_score,
        scenario_fit_score=conversion.lead_score_data.scenario_fit_score,
        timing_score=conversion.lead_score_data.timing_score,
        reachability_score=conversion.lead_score_data.reachability_score,
        leverage_score=conversion.lead_score_data.leverage_score,
        score_reason_json=conversion.lead_score_data.score_reason_json,
    )
    session.add(lead_score)
    session.commit()
    session.refresh(org)
    session.refresh(lead)
    session.refresh(lead_score)

    return org, lead, lead_score


def _get_extraction_run_for_signal(signal: Signal, session: Session) -> ExtractionRun | None:
    """Find the ExtractionRun that produced this Signal."""
    statement = select(ExtractionRun).where(ExtractionRun.raw_document_id == signal.raw_document_id)
    return session.exec(statement).first()


def _parse_extraction_result(extraction_run: ExtractionRun | None) -> ExtractionResult | None:
    if not extraction_run or not extraction_run.parsed_json:
        return None
    try:
        return ExtractionResult.model_validate_json(extraction_run.parsed_json)
    except Exception:
        return None


def _persist_organization(
    data: OrganizationData,
    session: Session,
) -> Organization:
    """Find existing org by normalized name or create a new one."""
    if data.normalized_name:
        existing = session.exec(
            select(Organization).where(Organization.normalized_name == data.normalized_name)
        ).first()
        if existing:
            return existing

    org = Organization(
        name=data.name,
        normalized_name=data.normalized_name,
        province=data.province,
        city=data.city,
        county=data.county,
        organization_type=data.organization_type,
    )
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


# ── Existing helpers ───────────────────────────────────────────


def generate_call_opening(customer_name: str, signal_title: str, recommended_package: str) -> str:
    return (
        f"您好，我看到贵单位/贵司近期有【{signal_title}】相关公开信息。"
        f"我们做的是食品和农产品包装二维码、数字标签、溯源和区域品牌数据管理工具。"
        f"想确认一下，这块是否涉及【{recommended_package}】相关需求？"
    )


def score_demo_lead() -> dict:
    result = score_lead(
        LeadScoringInput(
            signal_type="procurement_intent",
            scenario_flags=["region_brand_or_association", "agri_product_brand"],
            timing_flags=["procurement_expected_within_3_months"],
            reachability_flags=["agency_phone"],
            leverage_flags=["multi_org_region_brand_project"],
        )
    )
    return result.model_dump()
