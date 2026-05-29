"""ScoringRuleSet — type-safe, validated wrapper around scoring_rules.yml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from leadradar.services.config_service import load_scoring_rules


DEFAULT_RULES_PATH = Path(__file__).resolve().parents[3] / "data" / "scoring_rules.yml"


class ScoringRuleSet:
    """Validated in-memory representation of scoring_rules.yml.

    Provides type-safe access to dimensions, flags, scores, and grades.
    Eliminates raw dict lookups scattered across scoring.py and tests.
    """

    _DIMENSIONS = (
        "budget_strength",
        "scenario_fit",
        "timing",
        "reachability",
        "leverage",
    )

    def __init__(self, data: dict[str, Any] | None = None):
        self._data = data or load_scoring_rules()

    # ── dimensions ──────────────────────────────────────────────────

    def dimensions(self) -> tuple[str, ...]:
        return self._DIMENSIONS

    def max_score(self, dimension: str) -> int:
        return int(self._data["max_scores"][dimension])

    # ── flags ───────────────────────────────────────────────────────

    def valid_flags(self) -> set[str]:
        """Return all flag names across all dimensions."""
        flags: set[str] = set()
        for dim in self._DIMENSIONS:
            flags.update(self._data[dim].keys())
        return flags

    def valid_flags_for(self, dimension: str) -> set[str]:
        return set(self._data[dimension].keys())

    def flag_score(self, dimension: str, flag: str) -> int:
        """Return score for a flag in a dimension."""
        return int(self._data[dimension].get(flag, 0))

    def has_flag(self, dimension: str, flag: str) -> bool:
        return flag in self._data.get(dimension, {})

    # ── grades ──────────────────────────────────────────────────────

    def grade_threshold(self, grade: str) -> int:
        return int(self._data["grades"][grade])

    def grade_for_total(self, total: int) -> Literal["S", "A", "B", "C", "D"]:
        thresholds = self._data["grades"]
        if total >= thresholds["S"]:
            return "S"
        if total >= thresholds["A"]:
            return "A"
        if total >= thresholds["B"]:
            return "B"
        if total >= thresholds["C"]:
            return "C"
        return "D"

    # ── raw access (for config_service compat) ──────────────────────

    def raw(self) -> dict[str, Any]:
        return self._data
