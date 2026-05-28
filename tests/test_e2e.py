"""T-801: End-to-end demo — feed a sample announcement through the full pipeline."""

import json

import pytest
from sqlalchemy.pool import StaticPool
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
from leadradar.services.call_script import generate_call_script
from leadradar.services.lead_service import document_to_signal, signal_to_scored_lead

# ── Sample procurement announcement (realistic but fictional) ──────

SAMPLE_ANNOUNCEMENT = """
某县农业农村局农产品区域公用品牌建设项目采购意向公告

一、项目概况
为推进我县农产品区域公用品牌建设，提升品牌影响力和市场竞争力，
拟实施品牌数字化管理及包装升级项目。

二、采购单位：某县农业农村局

三、项目预算：180万元

四、主要采购内容
1. 区域品牌数字化管理平台建设
2. 授权企业产品二维码溯源系统
3. 品牌包装设计与印刷（含预包装食品标签合规）
4. 品牌推广与数字化展示

五、预计采购时间：2026年7月

六、联系方式
采购代理机构：某县政府采购中心
地址：某县政务服务中心三楼

某县农业农村局
2026年5月26日
"""


@pytest.fixture
def engine():
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(e)
    return e


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def llm():
    return MockLLMProvider()


# ═══════════════════════════════════════════════════════════════════
# Full pipeline: Document → Extraction → Signal → Lead → Score → Script
# ═══════════════════════════════════════════════════════════════════


class TestEndToEndPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline_produces_all_artifacts(self, session, llm):
        """The complete pipeline should produce all 6 artifacts from a single announcement."""
        # Step 0: Create source and document
        source = Source(name="某省政府采购网", source_type="government_procurement")
        session.add(source)
        session.commit()
        session.refresh(source)

        document = RawDocument(
            source_id=source.id,
            url="https://example.gov.cn/notice/mx-nyc-2026-001",
            title="某县农业农村局农产品区域公用品牌建设项目采购意向公告",
            extracted_text=SAMPLE_ANNOUNCEMENT.strip(),
            parse_status="completed",
            document_type="government_procurement",
        )
        session.add(document)
        session.commit()
        session.refresh(document)

        # ── Step 1: RawDocument → ExtractionRun + Signal ──────────
        extraction_run, signal = await document_to_signal(
            document=document,
            llm=llm,
            session=session,
        )

        # Verify ExtractionRun
        assert extraction_run is not None
        assert extraction_run.status == ExtractionRunStatus.COMPLETED
        assert extraction_run.confidence > 0
        assert extraction_run.raw_response is not None
        assert extraction_run.parsed_json is not None

        # Verify Signal was produced (MockLLMProvider returns is_relevant=True)
        assert signal is not None
        assert signal.signal_type == "procurement_intent"
        assert signal.title is not None
        assert signal.budget_amount == 1_800_000
        assert signal.confidence > 0
        assert signal.source_url == document.url
        assert signal.evidence_text is not None

        # ── Step 2: Signal → Organization + Lead + LeadScore ──────
        org, lead, score = signal_to_scored_lead(
            signal=signal,
            session=session,
        )

        # Verify Organization
        assert org is not None
        assert org.name == "某县农业农村局"
        assert org.normalized_name is not None

        # Verify Lead
        assert lead is not None
        assert lead.organization_id == org.id
        assert lead.primary_signal_id == signal.id
        assert lead.lead_status == LeadStatus.NEW
        assert lead.customer_type == "region_brand_government"
        assert lead.recommended_package is not None
        assert lead.budget_bucket == "100-500万"

        # Verify LeadScore
        assert score is not None
        assert score.lead_id == lead.id
        assert score.total_score > 0
        assert score.grade in ("S", "A", "B", "C", "D")
        assert score.budget_strength_score > 0
        reasons = json.loads(score.score_reason_json) if score.score_reason_json else []
        assert len(reasons) > 0

        # ── Step 3: Generate Call Script ──────────────────────────
        script = generate_call_script(
            customer_type=lead.customer_type,
            organization_name=org.name,
            signal_title=signal.title,
            signal_type=signal.signal_type,
            recommended_package=lead.recommended_package,
            budget_amount=signal.budget_amount,
        )

        assert "opening" in script
        assert "questions" in script
        assert "wechat_follow_up" in script
        assert "某县农业农村局" in script["opening"]
        assert len(script["questions"]) >= 3
        assert "区域品牌数字化管理包" in script["wechat_follow_up"]

    @pytest.mark.asyncio
    async def test_pipeline_persists_all_entities(self, session, llm):
        """All pipeline artifacts should be queryable from the database after processing."""
        source = Source(name="测试源", source_type="government_procurement")
        session.add(source)
        session.commit()

        document = RawDocument(
            source_id=source.id,
            url="https://example.gov.cn/test-002",
            title="某县品牌建设采购意向",
            extracted_text=SAMPLE_ANNOUNCEMENT.strip(),
            parse_status="completed",
        )
        session.add(document)
        session.commit()

        _, signal = await document_to_signal(document=document, llm=llm, session=session)
        assert signal is not None

        signal_to_scored_lead(signal=signal, session=session)

        # Verify all entities are queryable
        assert len(session.exec(select(Source)).all()) == 1
        assert len(session.exec(select(RawDocument)).all()) == 1
        assert len(session.exec(select(ExtractionRun)).all()) == 1
        assert len(session.exec(select(Signal)).all()) == 1
        assert len(session.exec(select(Organization)).all()) == 1
        assert len(session.exec(select(Lead)).all()) == 1
        assert len(session.exec(select(LeadScore)).all()) == 1

    @pytest.mark.asyncio
    async def test_pipeline_scores_consistent_with_direct_scoring(self, session, llm):
        """The score produced by pipeline should match direct scoring engine output."""
        from leadradar.scoring import score_lead
        from leadradar.schemas import LeadScoringInput

        source = Source(name="测试源", source_type="government_procurement")
        session.add(source)
        session.commit()

        document = RawDocument(
            source_id=source.id,
            url="https://example.gov.cn/test-003",
            title="品牌建设采购意向",
            extracted_text=SAMPLE_ANNOUNCEMENT.strip(),
            parse_status="completed",
        )
        session.add(document)
        session.commit()

        _, signal = await document_to_signal(document=document, llm=llm, session=session)
        assert signal is not None

        _, _, score = signal_to_scored_lead(signal=signal, session=session)

        # The pipeline score should be a valid LeadScoringResult
        assert score.total_score >= 0
        assert score.total_score <= 100
        assert score.budget_strength_score + score.scenario_fit_score + \
            score.timing_score + score.reachability_score + score.leverage_score == \
            score.total_score

    @pytest.mark.asyncio
    async def test_pipeline_irrelevant_document_produces_no_lead(self, session):
        """A document judged irrelevant should not produce a Signal or Lead."""
        from leadradar.schemas import ExtractionResult

        class IrrelevantMockProvider(MockLLMProvider):
            async def extract(self, *, text, url=None, title=None):
                from leadradar.schemas import Evidence as Ev
                return ExtractionResult(
                    is_relevant=False,
                    signal_type="irrelevant",
                    confidence=0.1,
                    evidence=[Ev(field="title", text="某县乡村道路维修项目")],
                    uncertainties=["not related to packaging or procurement"],
                )

        llm = IrrelevantMockProvider()

        source = Source(name="测试源", source_type="government_procurement")
        session.add(source)
        session.commit()

        document = RawDocument(
            source_id=source.id,
            url="https://example.gov.cn/test-irrelevant",
            title="某县道路维修招标公告",
            extracted_text="本工程为某县乡村道路维修项目...",
            parse_status="completed",
        )
        session.add(document)
        session.commit()

        extraction_run, signal = await document_to_signal(
            document=document, llm=llm, session=session,
        )

        assert extraction_run is not None
        assert signal is None  # No signal for irrelevant docs
        assert len(session.exec(select(Lead)).all()) == 0
        assert len(session.exec(select(LeadScore)).all()) == 0
