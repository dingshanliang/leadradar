"""Tests for T-501 (document_to_signal) and T-502 (signal_to_scored_lead)."""

import json

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from leadradar.llm.extraction import MockLLMProvider
from leadradar.models import (
    ExtractionRun,
    ExtractionRunStatus,
    Lead,
    LeadScore,
    LeadStatus,
    Organization,
    RawDocument,
    Signal,
    Source,
)
from leadradar.services.lead_service import (
    document_to_signal,
    signal_to_scored_lead,
)


@pytest.fixture
def engine():
    e = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(e)
    return e


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def sample_source(session):
    source = Source(name="测试数据源", source_type="government_procurement")
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@pytest.fixture
def sample_document(session, sample_source):
    doc = RawDocument(
        source_id=sample_source.id,
        url="https://example.gov.cn/notice/001",
        title="某县农产品区域公用品牌建设项目采购意向",
        extracted_text=(
            "采购单位：某县农业农村局\n"
            "预算金额：180万元\n"
            "预计采购时间：2026年7月\n"
            "采购需求：区域公用品牌建设、农产品品牌推广、包装设计、数字化展示。"
        ),
        parse_status="completed",
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


@pytest.fixture
def llm_provider():
    return MockLLMProvider()


# ════════════════════════════════════════════════════════════════
# T-501: RawDocument → ExtractionRun → Signal
# ════════════════════════════════════════════════════════════════


class TestDocumentToSignal:
    @pytest.mark.asyncio
    async def test_creates_extraction_run(self, session, sample_document, llm_provider):
        extraction_run, signal = await document_to_signal(
            document=sample_document,
            llm=llm_provider,
            session=session,
        )
        assert isinstance(extraction_run, ExtractionRun)
        assert extraction_run.raw_document_id == sample_document.id
        assert extraction_run.status == ExtractionRunStatus.COMPLETED
        assert extraction_run.llm_provider == "MockLLMProvider"
        assert extraction_run.raw_response is not None

    @pytest.mark.asyncio
    async def test_creates_signal(self, session, sample_document, llm_provider):
        extraction_run, signal = await document_to_signal(
            document=sample_document,
            llm=llm_provider,
            session=session,
        )
        assert isinstance(signal, Signal)
        assert signal.raw_document_id == sample_document.id
        assert signal.signal_type == "procurement_intent"
        assert signal.confidence > 0
        assert signal.evidence_text is not None

    @pytest.mark.asyncio
    async def test_signal_has_budget(self, session, sample_document, llm_provider):
        _, signal = await document_to_signal(
            document=sample_document,
            llm=llm_provider,
            session=session,
        )
        assert signal.budget_amount == 1800000

    @pytest.mark.asyncio
    async def test_signal_has_matched_keywords(self, session, sample_document, llm_provider):
        _, signal = await document_to_signal(
            document=sample_document,
            llm=llm_provider,
            session=session,
        )
        keywords = json.loads(signal.matched_keywords_json)
        assert len(keywords) > 0

    @pytest.mark.asyncio
    async def test_signal_has_source_url(self, session, sample_document, llm_provider):
        _, signal = await document_to_signal(
            document=sample_document,
            llm=llm_provider,
            session=session,
        )
        assert signal.source_url == sample_document.url

    @pytest.mark.asyncio
    async def test_extraction_run_persists_parsed_json(
        self, session, sample_document, llm_provider
    ):
        extraction_run, _ = await document_to_signal(
            document=sample_document,
            llm=llm_provider,
            session=session,
        )
        parsed = json.loads(extraction_run.parsed_json)
        assert parsed["is_relevant"] is True
        assert "signal_type" in parsed

    @pytest.mark.asyncio
    async def test_records_persisted_in_db(self, session, sample_document, llm_provider):
        await document_to_signal(document=sample_document, llm=llm_provider, session=session)

        runs = session.exec(select(ExtractionRun)).all()
        assert len(runs) == 1

        signals = session.exec(select(Signal)).all()
        assert len(signals) == 1


# ════════════════════════════════════════════════════════════════
# T-502: Signal → Organization → Lead → LeadScore
# ════════════════════════════════════════════════════════════════


class TestSignalToScoredLead:
    async def _make_signal(self, session, sample_document, llm_provider):
        _, signal = await document_to_signal(
            document=sample_document,
            llm=llm_provider,
            session=session,
        )
        session.refresh(signal)
        return signal

    @pytest.mark.asyncio
    async def test_creates_organization(self, session, sample_document, llm_provider):
        signal = await self._make_signal(session, sample_document, llm_provider)
        org, lead, score = signal_to_scored_lead(signal=signal, session=session)

        assert isinstance(org, Organization)
        assert "农业农村局" in org.name

    @pytest.mark.asyncio
    async def test_creates_lead(self, session, sample_document, llm_provider):
        signal = await self._make_signal(session, sample_document, llm_provider)
        org, lead, score = signal_to_scored_lead(signal=signal, session=session)

        assert isinstance(lead, Lead)
        assert lead.organization_id == org.id
        assert lead.primary_signal_id == signal.id
        assert lead.lead_status == LeadStatus.NEW
        assert lead.customer_type is not None

    @pytest.mark.asyncio
    async def test_creates_lead_score(self, session, sample_document, llm_provider):
        signal = await self._make_signal(session, sample_document, llm_provider)
        org, lead, score = signal_to_scored_lead(signal=signal, session=session)

        assert isinstance(score, LeadScore)
        assert score.lead_id == lead.id
        assert score.total_score > 0
        assert score.grade in {"S", "A", "B", "C", "D"}
        assert score.score_reason_json is not None

    @pytest.mark.asyncio
    async def test_lead_score_s_grade_for_procurement(self, session, sample_document, llm_provider):
        signal = await self._make_signal(session, sample_document, llm_provider)
        _, _, score = signal_to_scored_lead(signal=signal, session=session)
        assert score.total_score >= 85
        assert score.grade == "S"

    @pytest.mark.asyncio
    async def test_records_persisted_in_db(self, session, sample_document, llm_provider):
        signal = await self._make_signal(session, sample_document, llm_provider)
        signal_to_scored_lead(signal=signal, session=session)

        orgs = session.exec(select(Organization)).all()
        assert len(orgs) == 1

        leads = session.exec(select(Lead)).all()
        assert len(leads) == 1

        scores = session.exec(select(LeadScore)).all()
        assert len(scores) == 1

    @pytest.mark.asyncio
    async def test_idempotent_organization(self, session, sample_document, llm_provider):
        signal = await self._make_signal(session, sample_document, llm_provider)
        signal_to_scored_lead(signal=signal, session=session)

        signal2 = Signal(
            raw_document_id=signal.raw_document_id,
            signal_type="tender_notice",
            title="再次招标",
            budget_amount=200000,
            confidence=0.9,
        )
        session.add(signal2)
        session.commit()
        session.refresh(signal2)

        org2, _, _ = signal_to_scored_lead(signal=signal2, session=session)
        all_orgs = session.exec(select(Organization)).all()
        assert len(all_orgs) == 1
        assert org2.name == all_orgs[0].name


# ════════════════════════════════════════════════════════════════
# Integration: full pipeline end-to-end
# ════════════════════════════════════════════════════════════════


class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_document_to_scored_lead(self, session, sample_document, llm_provider):
        _, signal = await document_to_signal(
            document=sample_document,
            llm=llm_provider,
            session=session,
        )
        session.refresh(signal)

        org, lead, score = signal_to_scored_lead(signal=signal, session=session)

        assert signal.organization_id == org.id
        assert lead.organization_id == org.id
        assert lead.primary_signal_id == signal.id
        assert score.lead_id == lead.id
        assert score.total_score >= 85
        assert score.grade == "S"
