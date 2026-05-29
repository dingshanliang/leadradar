"""Tests for ScoringRuleSet — type-safe wrapper around scoring_rules.yml."""

from __future__ import annotations

import pytest

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
        "budget_strength": {
            "procurement_intent": 35,
            "tender_notice": 35,
        },
        "scenario_fit": {
            "region_brand_or_association": 10,
            "prepackaged_food": 8,
        },
        "timing": {
            "procurement_expected_within_3_months": 20,
        },
        "reachability": {
            "procurement_contact": 10,
            "agency_phone": 8,
        },
        "leverage": {
            "multi_org_region_brand_project": 10,
        },
    }


@pytest.fixture
def rule_set(sample_rules):
    return ScoringRuleSet(data=sample_rules)


class TestDimensions:
    def test_dimensions_returns_five(self, rule_set):
        assert rule_set.dimensions() == (
            "budget_strength",
            "scenario_fit",
            "timing",
            "reachability",
            "leverage",
        )

    def test_max_score(self, rule_set):
        assert rule_set.max_score("budget_strength") == 35
        assert rule_set.max_score("scenario_fit") == 25


class TestFlags:
    def test_valid_flags_returns_all(self, rule_set):
        flags = rule_set.valid_flags()
        assert "region_brand_or_association" in flags
        assert "procurement_intent" in flags
        assert "procurement_contact" in flags

    def test_valid_flags_for_dimension(self, rule_set):
        scenario = rule_set.valid_flags_for("scenario_fit")
        assert scenario == {"region_brand_or_association", "prepackaged_food"}

    def test_flag_score_known(self, rule_set):
        assert rule_set.flag_score("scenario_fit", "prepackaged_food") == 8

    def test_flag_score_unknown_returns_zero(self, rule_set):
        assert rule_set.flag_score("scenario_fit", "nonexistent") == 0

    def test_has_flag(self, rule_set):
        assert rule_set.has_flag("scenario_fit", "prepackaged_food") is True
        assert rule_set.has_flag("scenario_fit", "nonexistent") is False


class TestGrades:
    def test_grade_threshold(self, rule_set):
        assert rule_set.grade_threshold("S") == 85
        assert rule_set.grade_threshold("D") == 0

    def test_grade_for_total(self, rule_set):
        assert rule_set.grade_for_total(90) == "S"
        assert rule_set.grade_for_total(85) == "S"
        assert rule_set.grade_for_total(84) == "A"
        assert rule_set.grade_for_total(70) == "A"
        assert rule_set.grade_for_total(69) == "B"
        assert rule_set.grade_for_total(55) == "B"
        assert rule_set.grade_for_total(54) == "C"
        assert rule_set.grade_for_total(40) == "C"
        assert rule_set.grade_for_total(39) == "D"
        assert rule_set.grade_for_total(0) == "D"


class TestRawAccess:
    def test_raw_returns_underlying_data(self, sample_rules, rule_set):
        assert rule_set.raw() == sample_rules
