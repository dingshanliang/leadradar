"""T-802: Compliance check — verify no automated harassment, personal phone scraping, or bypass capabilities."""

import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool

from leadradar.config import Settings
from leadradar.llm.extraction import validate_extraction
from leadradar.models import Blocklist, Lead, LeadStatus, Organization, Signal
from leadradar.schemas import Evidence, ExtractionResult


# ═══════════════════════════════════════════════════════════════════
# 1. Configuration switches enforce safety boundaries
# ═══════════════════════════════════════════════════════════════════


class TestConfigSafety:
    def test_personal_phone_collection_disabled_by_default(self):
        s = Settings()
        assert s.allow_personal_phone_collection is False

    def test_automated_outbound_calls_disabled_by_default(self):
        s = Settings()
        assert s.allow_automated_outbound_calls is False

    def test_public_business_contacts_allowed_by_default(self):
        s = Settings()
        assert s.allow_public_business_contacts is True

    def test_crawl_rate_limit_is_set(self):
        s = Settings()
        assert s.crawl_requests_per_minute > 0
        assert s.crawl_requests_per_minute <= 60

    def test_crawl_timeout_is_set(self):
        s = Settings()
        assert s.crawl_timeout_seconds > 0


# ═══════════════════════════════════════════════════════════════════
# 2. Anti-fabrication: LLM cannot invent phone numbers or contacts
# ═══════════════════════════════════════════════════════════════════


class TestAntiFabrication:
    def test_personal_phone_in_evidence_flagged(self):
        result = ExtractionResult(
            is_relevant=True,
            signal_type="procurement_intent",
            confidence=0.9,
            evidence=[
                Evidence(field="contact", text="联系电话：13812345678"),
                Evidence(field="budget_amount", text="预算金额：100万元"),
            ],
        )
        validated = validate_extraction(result)
        assert any("phone" in u.lower() for u in validated.uncertainties)

    def test_personal_phone_in_summary_flagged(self):
        result = ExtractionResult(
            is_relevant=True,
            signal_type="procurement_intent",
            confidence=0.9,
            need_summary="采购负责人手机号13987654321，可联系",
            evidence=[
                Evidence(field="title", text="采购公告"),
            ],
        )
        validated = validate_extraction(result)
        assert any("phone" in u.lower() for u in validated.uncertainties)

    def test_confidence_drops_on_phone_detection(self):
        result = ExtractionResult(
            is_relevant=True,
            signal_type="procurement_intent",
            confidence=0.9,
            evidence=[
                Evidence(field="contact", text="手机13900139000"),
            ],
        )
        validated = validate_extraction(result)
        assert validated.confidence < 0.9

    def test_clean_result_not_penalized(self):
        result = ExtractionResult(
            is_relevant=True,
            signal_type="procurement_intent",
            confidence=0.9,
            organization_name="某县农业农村局",
            evidence=[
                Evidence(field="organization_name", text="某县农业农村局"),
                Evidence(field="budget_amount", text="预算金额：180万元"),
            ],
            budget_amount={"value": 1800000, "currency": "CNY", "raw": "180万元"},
        )
        validated = validate_extraction(result)
        assert not any("phone" in u.lower() for u in validated.uncertainties)


# ═══════════════════════════════════════════════════════════════════
# 3. Blocklist: refused contacts must be blocked
# ═══════════════════════════════════════════════════════════════════


class TestBlocklist:
    @pytest.fixture
    def session(self):
        e = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(e)
        with Session(e) as s:
            yield s

    def test_can_add_to_blocklist(self, session):
        entry = Blocklist(
            reason="对方明确拒绝联系",
        )
        session.add(entry)
        session.commit()
        assert len(session.exec(select(Blocklist)).all()) == 1

    def test_blocklist_with_organization(self, session):
        org = Organization(name="拒绝公司")
        session.add(org)
        session.commit()

        entry = Blocklist(
            organization_id=org.id,
            reason="对方明确拒绝联系",
        )
        session.add(entry)
        session.commit()

        blocked = session.exec(select(Blocklist)).first()
        assert blocked.organization_id == org.id
        assert "拒绝" in blocked.reason

    def test_lead_can_be_marked_blocked(self, session):
        org = Organization(name="测试机构")
        session.add(org)
        signal = Signal(signal_type="procurement_intent", evidence_text="测试")
        session.add(signal)
        session.commit()

        lead = Lead(
            organization_id=org.id,
            primary_signal_id=signal.id,
            lead_status=LeadStatus.BLOCKED,
        )
        session.add(lead)
        session.commit()

        assert lead.lead_status == LeadStatus.BLOCKED


# ═══════════════════════════════════════════════════════════════════
# 4. Evidence traceability: every conclusion has source
# ═══════════════════════════════════════════════════════════════════


class TestEvidenceTraceability:
    @pytest.fixture
    def session(self):
        e = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(e)
        with Session(e) as s:
            yield s

    def test_signal_has_source_url(self, session):
        signal = Signal(
            signal_type="procurement_intent",
            source_url="https://example.gov.cn/notice/001",
            evidence_text="预算金额：180万元",
        )
        session.add(signal)
        session.commit()
        assert signal.source_url is not None
        assert signal.evidence_text is not None

    def test_extraction_result_requires_evidence(self):
        """ExtractionResult must have at least one evidence entry."""
        with pytest.raises(Exception):
            ExtractionResult(
                is_relevant=True,
                signal_type="procurement_intent",
                confidence=0.9,
                evidence=[],  # Should fail: min_length=1
            )

    def test_budget_without_evidence_gets_penalty(self):
        result = ExtractionResult(
            is_relevant=True,
            signal_type="procurement_intent",
            confidence=0.9,
            budget_amount={"value": 500000, "currency": "CNY", "raw": "50万"},
            evidence=[Evidence(field="title", text="采购意向")],
        )
        validated = validate_extraction(result)
        assert any("budget" in u.lower() for u in validated.uncertainties)


# ═══════════════════════════════════════════════════════════════════
# 5. No prohibited capabilities in codebase
# ═══════════════════════════════════════════════════════════════════


class TestNoProhibitedCapabilities:
    """Verify the codebase does NOT contain automated outbound,
    personal data scraping, or anti-bot bypass capabilities."""

    def test_no_auto_dial_module(self):
        """No module for automated phone dialing."""
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("leadradar.outbound.auto_dial")

    def test_no_auto_wechat_module(self):
        """No module for automated WeChat adding."""
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("leadradar.outbound.auto_wechat")

    def test_no_auto_sms_module(self):
        """No module for automated SMS sending."""
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("leadradar.outbound.auto_sms")

    def test_no_captcha_bypass_module(self):
        """No module for CAPTCHA or anti-bot bypass."""
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("leadradar.crawlers.captcha_bypass")

    def test_no_login_bypass_module(self):
        """No module for login wall bypass."""
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("leadradar.crawlers.login_bypass")

    def test_no_personal_scraper_module(self):
        """No module for personal phone number scraping."""
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("leadradar.crawlers.personal_scraper")


# ═══════════════════════════════════════════════════════════════════
# 6. Call script includes required ethical elements
# ═══════════════════════════════════════════════════════════════════


class TestCallScriptEthics:
    def test_opening_identifies_sender(self):
        from leadradar.services.call_script import generate_call_script

        script = generate_call_script(
            organization_name="某县农业农村局",
            signal_title="品牌建设采购",
            signal_type="procurement_intent",
        )
        assert "我" in script["opening"]

    def test_opening_mentions_source(self):
        """Opening should indicate information comes from public sources."""
        from leadradar.services.call_script import generate_call_script

        script = generate_call_script(
            organization_name="某县农业农村局",
            signal_title="品牌建设采购意向",
            signal_type="procurement_intent",
        )
        # Should reference seeing the announcement or public info
        assert any(k in script["opening"] for k in ("看到", "注意到", "公开"))

    def test_no_pressure_tactics(self):
        """Script should not contain high-pressure sales tactics."""
        from leadradar.services.call_script import generate_call_script

        script = generate_call_script(
            organization_name="某县农业农村局",
            signal_title="品牌建设采购",
            signal_type="procurement_intent",
        )
        full_text = script["opening"] + " ".join(script["questions"]) + script["wechat_follow_up"]
        pressure_words = ["必须", "赶紧", "立即", "错过就没", "限时", "马上签约"]
        for word in pressure_words:
            assert word not in full_text, f"Pressure tactic found: {word}"
