"""Tests for FlagDerivationEngine and individual flag rules."""

from __future__ import annotations

import pytest

from leadradar.models import Signal
from leadradar.schemas import ExtractionResult
from leadradar.services.flag_derivation import (
    FlagDerivationEngine,
    _agency_phone,
    _agri_product_brand,
    _certification_or_gi,
    _gift_box_or_packaged_product,
    _multi_org_region_brand_project,
    _newly_published_tender,
    _newly_won_project,
    _official_phone,
    _packaging_or_printing_partner,
    _poor_existing_qr,
    _prepackaged_food,
    _procurement_contact,
    _procurement_expected_within_3_months,
    _region_brand_or_association,
    default_engine,
)
from leadradar.services.scoring_rule_set import ScoringRuleSet


@pytest.fixture
def sample_rules():
    return {
        "version": "0.1",
        "max_scores": {
            "budget_strength": 35,
            "scenario_fit": 25,
            "timing": 20,
            "reachability": 10,
            "leverage": 10,
        },
        "grades": {"S": 85, "A": 70, "B": 55, "C": 40, "D": 0},
        "budget_strength": {"procurement_intent": 35},
        "scenario_fit": {
            "region_brand_or_association": 10,
            "prepackaged_food": 8,
            "agri_product_brand": 8,
            "gift_box_or_packaged_product": 6,
            "certification_or_gi": 5,
            "poor_existing_qr": 8,
        },
        "timing": {
            "procurement_expected_within_3_months": 20,
            "newly_published_tender": 18,
            "newly_won_project": 12,
        },
        "reachability": {
            "procurement_contact": 10,
            "agency_phone": 8,
            "official_phone": 6,
        },
        "leverage": {
            "multi_org_region_brand_project": 10,
            "packaging_or_printing_partner": 8,
        },
    }


@pytest.fixture
def rule_set(sample_rules):
    return ScoringRuleSet(data=sample_rules)


@pytest.fixture
def engine(rule_set):
    return default_engine(rule_set=rule_set)


@pytest.fixture
def base_signal():
    return Signal(
        raw_document_id=1,
        signal_type="procurement_intent",
        title="测试",
        evidence_text="预算180万元",
        source_url="https://example.gov.cn/1",
    )


@pytest.fixture
def base_result():
    return ExtractionResult(
        is_relevant=True,
        signal_type="procurement_intent",
        customer_type="region_brand_government",
        need_summary="预包装食品项目",
        matched_keywords=["农产品", "地理标志"],
        product_fit=["区域品牌数字化管理包"],
        evidence=[{"field": "budget", "text": "预算180万元"}],
        confidence=0.92,
    )


# ════════════════════════════════════════════════════════════════
# Engine registration validation
# ════════════════════════════════════════════════════════════════


class TestEngineRegistration:
    def test_register_unknown_dimension_raises(self, rule_set):
        engine = FlagDerivationEngine(rule_set=rule_set)
        with pytest.raises(ValueError, match="Unknown dimension"):
            engine.register("unknown_dim", "some_flag", lambda s, r: True)

    def test_register_unknown_flag_raises(self, rule_set):
        engine = FlagDerivationEngine(rule_set=rule_set)
        with pytest.raises(ValueError, match="Unknown flag"):
            engine.register("scenario_fit", "nonexistent_flag", lambda s, r: True)

    def test_register_valid_rule_succeeds(self, rule_set):
        engine = FlagDerivationEngine(rule_set=rule_set)
        engine.register("scenario_fit", "prepackaged_food", lambda s, r: True)
        assert len(engine._rules) == 1


# ════════════════════════════════════════════════════════════════
# Scenario-fit rules
# ════════════════════════════════════════════════════════════════


class TestScenarioFitRules:
    def test_region_brand_or_association_match(self, base_result):
        assert _region_brand_or_association(None, base_result) is True

    def test_region_brand_or_association_no_match(self, base_result):
        r = base_result.model_copy(update={"customer_type": "enterprise"})
        assert _region_brand_or_association(None, r) is False

    def test_prepackaged_food_match(self, base_result):
        assert _prepackaged_food(None, base_result) is True

    def test_prepackaged_food_no_match(self, base_result):
        r = base_result.model_copy(update={"need_summary": "硬件采购"})
        assert _prepackaged_food(None, r) is False

    def test_agri_product_brand_match(self, base_result):
        assert _agri_product_brand(None, base_result) is True

    def test_agri_product_brand_no_match(self, base_result):
        r = base_result.model_copy(update={"need_summary": "IT系统", "matched_keywords": []})
        assert _agri_product_brand(None, r) is False

    def test_gift_box_or_packaged_product_match(self, base_result):
        r = base_result.model_copy(update={"need_summary": "礼盒包装设计"})
        assert _gift_box_or_packaged_product(None, r) is True

    def test_certification_or_gi_match(self, base_result):
        assert _certification_or_gi(None, base_result) is True

    def test_poor_existing_qr_match(self, base_result):
        r = base_result.model_copy(update={"need_summary": "二维码体验差"})
        assert _poor_existing_qr(None, r) is True


# ════════════════════════════════════════════════════════════════
# Timing rules
# ════════════════════════════════════════════════════════════════


class TestTimingRules:
    def test_procurement_expected_within_3_months(self, base_result):
        assert _procurement_expected_within_3_months(None, base_result) is True

    def test_newly_published_tender(self, base_result):
        r = base_result.model_copy(update={"signal_type": "tender_notice"})
        assert _newly_published_tender(None, r) is True

    def test_newly_won_project(self, base_result):
        r = base_result.model_copy(update={"signal_type": "winning_notice"})
        assert _newly_won_project(None, r) is True


# ════════════════════════════════════════════════════════════════
# Leverage rules
# ════════════════════════════════════════════════════════════════


class TestLeverageRules:
    def test_multi_org_region_brand_project(self, base_result):
        assert _multi_org_region_brand_project(None, base_result) is True

    def test_packaging_or_printing_partner(self, base_result):
        r = base_result.model_copy(update={"product_fit": ["渠道白标工具包"]})
        assert _packaging_or_printing_partner(None, r) is True


# ════════════════════════════════════════════════════════════════
# Reachability rules (mutually exclusive)
# ════════════════════════════════════════════════════════════════


class TestReachabilityRules:
    def test_agency_phone_priority(self, base_signal):
        s = base_signal.model_copy(update={"evidence_text": "采购代理：张三"})
        assert _agency_phone(s, None) is True
        assert _procurement_contact(s, None) is False
        assert _official_phone(s, None) is False

    def test_procurement_contact_when_no_agency(self, base_signal):
        s = base_signal.model_copy(update={"evidence_text": "联系人：李四"})
        assert _agency_phone(s, None) is False
        assert _procurement_contact(s, None) is True
        assert _official_phone(s, None) is False

    def test_official_phone_fallback(self, base_signal):
        s = base_signal.model_copy(update={"evidence_text": "公开招标公告"})
        assert _agency_phone(s, None) is False
        assert _procurement_contact(s, None) is False
        assert _official_phone(s, None) is True

    def test_mutual_exclusivity(self, base_signal):
        """For any evidence_text, exactly one reachability rule fires."""
        texts = [
            "采购代理：张三",
            "联系人：李四",
            "公开招标公告",
            "",
        ]
        for text in texts:
            s = base_signal.model_copy(update={"evidence_text": text})
            hits = sum([
                _agency_phone(s, None),
                _procurement_contact(s, None),
                _official_phone(s, None),
            ])
            assert hits == 1, f"Expected exactly 1 hit for '{text}', got {hits}"


# ════════════════════════════════════════════════════════════════
# End-to-end derive
# ════════════════════════════════════════════════════════════════


class TestDerive:
    def test_derive_with_full_result(self, engine, base_signal, base_result):
        scoring_input = engine.derive(base_signal, base_result)

        assert scoring_input.signal_type == "procurement_intent"
        assert "region_brand_or_association" in scoring_input.scenario_flags
        assert "prepackaged_food" in scoring_input.scenario_flags
        assert "agri_product_brand" in scoring_input.scenario_flags
        assert "certification_or_gi" in scoring_input.scenario_flags
        assert "procurement_expected_within_3_months" in scoring_input.timing_flags
        assert "multi_org_region_brand_project" in scoring_input.leverage_flags
        assert scoring_input.reachability_flags == ["official_phone"]

    def test_derive_with_none_result(self, engine, base_signal):
        scoring_input = engine.derive(base_signal, None)

        assert scoring_input.signal_type == "procurement_intent"
        assert scoring_input.scenario_flags == []
        assert scoring_input.timing_flags == []
        assert scoring_input.leverage_flags == []
        assert scoring_input.reachability_flags == ["official_phone"]

    def test_rule_failure_isolated(self, rule_set, base_signal):
        """A crashing rule should not break the whole derivation."""
        engine = FlagDerivationEngine(rule_set=rule_set)
        engine.register("scenario_fit", "prepackaged_food", lambda s, r: (_ for _ in ()).throw(RuntimeError("boom")))
        engine.register("scenario_fit", "region_brand_or_association", lambda s, r: True)

        result = engine.derive(base_signal, None)
        assert "region_brand_or_association" in result.scenario_flags
        assert "prepackaged_food" not in result.scenario_flags
