"""Tests for LeadConversionEngine — pure data transformation, no DB."""

from __future__ import annotations

import json

import pytest

from leadradar.models import LeadStatus, Signal
from leadradar.schemas import ExtractionResult, Region
from leadradar.services.lead_conversion import (
    LeadConversionEngine,
    LeadConversionResult,
    _budget_bucket,
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
        "budget_strength": {"procurement_intent": 35, "tender_notice": 35},
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
def base_signal():
    return Signal(
        raw_document_id=1,
        signal_type="procurement_intent",
        title="测试",
        evidence_text="预算180万元",
        source_url="https://example.gov.cn/1",
        budget_amount=1_800_000,
    )


@pytest.fixture
def base_result():
    return ExtractionResult(
        is_relevant=True,
        signal_type="procurement_intent",
        customer_type="region_brand_government",
        organization_name="某县农业农村局",
        region=Region(province="江西", city="南昌", county="某县"),
        need_summary="预包装食品项目",
        matched_keywords=["农产品", "地理标志"],
        product_fit=["区域品牌数字化管理包"],
        evidence=[{"field": "budget", "text": "预算180万元"}],
        confidence=0.92,
    )


# ════════════════════════════════════════════════════════════════
# OrganizationData derivation
# ════════════════════════════════════════════════════════════════


class TestOrganizationData:
    def test_name_from_extraction(self, base_signal, base_result):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        assert result.organization_data.name == "某县农业农村局"
        assert result.organization_data.normalized_name == "某县农业农村局"

    def test_unknown_when_no_name(self, base_signal):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, None)
        assert result.organization_data.name == "未知机构"
        assert result.organization_data.normalized_name == "未知机构"

    def test_region_fields(self, base_signal, base_result):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        assert result.organization_data.province == "江西"
        assert result.organization_data.city == "南昌"
        assert result.organization_data.county == "某县"

    def test_customer_type(self, base_signal, base_result):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        assert result.organization_data.organization_type == "region_brand_government"

    def test_no_region_when_none(self, base_signal):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, None)
        assert result.organization_data.province is None
        assert result.organization_data.city is None
        assert result.organization_data.county is None


# ════════════════════════════════════════════════════════════════
# LeadData derivation
# ════════════════════════════════════════════════════════════════


class TestLeadData:
    def test_customer_type(self, base_signal, base_result):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        assert result.lead_data.customer_type == "region_brand_government"

    def test_recommended_package(self, base_signal, base_result):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        assert result.lead_data.recommended_package == "区域品牌数字化管理包"

    def test_no_package_when_empty_fit(self, base_signal):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, None)
        assert result.lead_data.recommended_package is None

    def test_lead_status_is_new(self, base_signal, base_result):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        assert result.lead_data.lead_status == LeadStatus.NEW

    def test_budget_bucket(self, base_signal, base_result):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        assert result.lead_data.budget_bucket == "100-500万"

    def test_no_budget_bucket_when_none(self, base_signal):
        r = base_signal.model_copy(update={"budget_amount": None})
        engine = LeadConversionEngine()
        result = engine.convert(r, None)
        assert result.lead_data.budget_bucket is None


# ════════════════════════════════════════════════════════════════
# LeadScoreData derivation
# ════════════════════════════════════════════════════════════════


class TestLeadScoreData:
    def test_scores_present(self, base_signal, base_result, sample_rules):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        assert result.lead_score_data.total_score > 0
        assert result.lead_score_data.grade in {"S", "A", "B", "C", "D"}
        assert result.lead_score_data.budget_strength_score >= 0
        assert result.lead_score_data.scenario_fit_score >= 0
        assert result.lead_score_data.timing_score >= 0
        assert result.lead_score_data.reachability_score >= 0
        assert result.lead_score_data.leverage_score >= 0

    def test_reason_json_is_valid(self, base_signal, base_result):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        reasons = json.loads(result.lead_score_data.score_reason_json)
        assert isinstance(reasons, list)
        assert len(reasons) > 0

    def test_s_grade_for_procurement_intent(self, base_signal, base_result):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        assert result.lead_score_data.grade == "S"
        assert result.lead_score_data.total_score >= 85


# ════════════════════════════════════════════════════════════════
# End-to-end conversion
# ════════════════════════════════════════════════════════════════


class TestConvert:
    def test_returns_all_three_parts(self, base_signal, base_result):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, base_result)
        assert isinstance(result, LeadConversionResult)
        assert result.organization_data is not None
        assert result.lead_data is not None
        assert result.lead_score_data is not None

    def test_with_none_extraction_result(self, base_signal):
        engine = LeadConversionEngine()
        result = engine.convert(base_signal, None)
        assert result.organization_data.name == "未知机构"
        assert result.lead_data.recommended_package is None
        assert result.lead_data.customer_type is None
        # Should still get a score (based on signal_type budget + default reachability)
        assert result.lead_score_data.total_score >= 0

    def test_with_custom_flag_engine(self, base_signal, base_result, sample_rules):
        from leadradar.services.flag_derivation import FlagDerivationEngine

        rule_set = ScoringRuleSet(data=sample_rules)
        flag_engine = FlagDerivationEngine(rule_set=rule_set)
        engine = LeadConversionEngine(flag_engine=flag_engine)
        result = engine.convert(base_signal, base_result)
        assert result.lead_score_data.total_score >= 0


# ════════════════════════════════════════════════════════════════
# _budget_bucket helper
# ════════════════════════════════════════════════════════════════


class TestBudgetBucket:
    def test_none(self):
        assert _budget_bucket(None) is None

    def test_under_10w(self):
        assert _budget_bucket(50_000) == "<10万"

    def test_10_to_50w(self):
        assert _budget_bucket(100_000) == "10-50万"
        assert _budget_bucket(499_999) == "10-50万"

    def test_50_to_100w(self):
        assert _budget_bucket(500_000) == "50-100万"
        assert _budget_bucket(999_999) == "50-100万"

    def test_100_to_500w(self):
        assert _budget_bucket(1_000_000) == "100-500万"
        assert _budget_bucket(4_999_999) == "100-500万"

    def test_over_500w(self):
        assert _budget_bucket(5_000_000) == ">500万"
        assert _budget_bucket(10_000_000) == ">500万"
