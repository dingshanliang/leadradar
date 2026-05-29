"""Tests for configuration management API and validation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from leadradar.main import app
from leadradar.services.config_service import (
    GradeThresholds,
    ScoringRulesUpdate,
    load_scoring_rules,
    save_scoring_rules,
    update_scoring_rules,
)

VALID_RULES = {
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
    },
    "timing": {
        "procurement_expected_within_3_months": 20,
    },
    "reachability": {
        "procurement_contact": 10,
    },
    "leverage": {
        "multi_org_region_brand_project": 10,
    },
}


class TestGradeThresholds:
    def test_valid_descending_grades(self):
        g = GradeThresholds(S=90, A=75, B=60, C=45, D=0)
        assert g.S == 90

    def test_equal_grades_rejected(self):
        with pytest.raises(ValueError, match="必须严格递减"):
            GradeThresholds(S=85, A=85, B=55, C=40, D=0)

    def test_out_of_order_grades_rejected(self):
        with pytest.raises(ValueError, match="必须严格递减"):
            GradeThresholds(S=70, A=85, B=55, C=40, D=0)


class TestScoringRulesUpdate:
    def test_valid_rules_accepted(self):
        rules = ScoringRulesUpdate(**VALID_RULES)
        assert rules.max_scores["budget_strength"] == 35

    def test_max_scores_not_100_rejected(self):
        data = dict(VALID_RULES)
        data["max_scores"] = {"budget_strength": 30, "scenario_fit": 25, "timing": 20, "reachability": 10, "leverage": 10}
        with pytest.raises(ValueError, match="总和必须等于 100"):
            ScoringRulesUpdate(**data)

    def test_sub_score_exceeds_max_rejected(self):
        data = dict(VALID_RULES)
        data["budget_strength"] = {"procurement_intent": 40}  # exceeds 35
        with pytest.raises(ValueError, match="超过了该维度满分"):
            ScoringRulesUpdate(**data)

    def test_missing_max_score_dimension_rejected(self):
        data = dict(VALID_RULES)
        data["max_scores"] = {"scenario_fit": 25, "timing": 20, "reachability": 10, "leverage": 10}
        # sum = 75, also fails sum check
        with pytest.raises(ValueError):
            ScoringRulesUpdate(**data)


class TestSaveAndLoad:
    def test_round_trip(self, tmp_path: Path):
        path = tmp_path / "scoring_rules.yml"
        save_scoring_rules(VALID_RULES, path)
        loaded = load_scoring_rules(path)
        assert loaded["grades"]["S"] == 85
        assert loaded["max_scores"]["budget_strength"] == 35

    def test_backup_created(self, tmp_path: Path):
        path = tmp_path / "scoring_rules.yml"
        save_scoring_rules({"version": "0.0"}, path)
        save_scoring_rules(VALID_RULES, path)
        bak = path.with_suffix(".yml.bak")
        assert bak.exists()
        assert load_scoring_rules(bak)["version"] == "0.0"


class TestConfigAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_put_scoring_config_valid(self, client: TestClient, tmp_path: Path, monkeypatch):
        from leadradar.services import config_service as cs
        monkeypatch.setattr(cs, "DEFAULT_SCORING_PATH", tmp_path / "scoring_rules.yml")
        res = client.put("/api/v1/config/scoring", json=VALID_RULES)
        assert res.status_code == 200
        assert res.json()["ok"] is True

    def test_put_scoring_config_invalid(self, client: TestClient):
        data = dict(VALID_RULES)
        data["grades"] = {"S": 85, "A": 85, "B": 55, "C": 40, "D": 0}
        res = client.put("/api/v1/config/scoring", json=data)
        assert res.status_code == 422
