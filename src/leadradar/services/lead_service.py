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
    LeadStatus,
    Organization,
    RawDocument,
    Signal,
)
from leadradar.schemas import ExtractionResult, LeadScoringInput
from leadradar.scoring import score_lead
from leadradar.services.flag_derivation import default_engine


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

    org = _find_or_create_organization(signal, extraction_result, session)
    signal.organization_id = org.id
    session.add(signal)

    scoring_input = default_engine().derive(signal, extraction_result)

    lead = Lead(
        organization_id=org.id,
        primary_signal_id=signal.id,
        customer_type=extraction_result.customer_type if extraction_result else None,
        recommended_package=(
            extraction_result.product_fit[0]
            if extraction_result and extraction_result.product_fit
            else None
        ),
        budget_bucket=_budget_bucket(signal.budget_amount),
        lead_status=LeadStatus.NEW,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)

    scoring_result = score_lead(scoring_input)

    lead_score = LeadScore(
        lead_id=lead.id,
        total_score=scoring_result.total_score,
        grade=scoring_result.grade,
        budget_strength_score=scoring_result.breakdown["budget_strength"],
        scenario_fit_score=scoring_result.breakdown["scenario_fit"],
        timing_score=scoring_result.breakdown["timing"],
        reachability_score=scoring_result.breakdown["reachability"],
        leverage_score=scoring_result.breakdown["leverage"],
        score_reason_json=json.dumps(scoring_result.reasons, ensure_ascii=False),
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


def _find_or_create_organization(
    signal: Signal,
    extraction_result: ExtractionResult | None,
    session: Session,
) -> Organization:
    """Find existing org by name or create a new one."""
    org_name = None
    region = None

    if extraction_result:
        org_name = extraction_result.organization_name
        if extraction_result.region:
            region = extraction_result.region

    if not org_name:
        org = Organization(name="未知机构")
        session.add(org)
        session.commit()
        session.refresh(org)
        return org

    normalized = org_name.strip().lower()
    existing = session.exec(
        select(Organization).where(Organization.normalized_name == normalized)
    ).first()

    if existing:
        return existing

    org = Organization(
        name=org_name,
        normalized_name=normalized,
        province=region.province if region else None,
        city=region.city if region else None,
        county=region.county if region else None,
        organization_type=(extraction_result.customer_type if extraction_result else None),
    )
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def _budget_bucket(amount: float | None) -> str | None:
    if amount is None:
        return None
    if amount < 100_000:
        return "<10万"
    if amount < 500_000:
        return "10-50万"
    if amount < 1_000_000:
        return "50-100万"
    if amount < 5_000_000:
        return "100-500万"
    return ">500万"


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
