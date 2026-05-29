from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from leadradar.schemas import LeadScoringInput, LeadScoringResult

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[2] / "data" / "scoring_rules.yml"


def load_scoring_rules(path: Path = DEFAULT_RULES_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def grade_for_score(score: int, rules: dict[str, Any]) -> str:
    thresholds = rules["grades"]
    if score >= thresholds["S"]:
        return "S"
    if score >= thresholds["A"]:
        return "A"
    if score >= thresholds["B"]:
        return "B"
    if score >= thresholds["C"]:
        return "C"
    return "D"


def _sum_flags(
    flag_names: list[str], rule_section: dict[str, int], max_score: int
) -> tuple[int, list[str]]:
    total = 0
    reasons: list[str] = []
    for flag in flag_names:
        points = int(rule_section.get(flag, 0))
        if points:
            total += points
            reasons.append(f"{flag} +{points}")
    return min(total, max_score), reasons


def score_lead(
    input_data: LeadScoringInput, rules: dict[str, Any] | None = None
) -> LeadScoringResult:
    rules = rules or load_scoring_rules()
    max_scores = rules["max_scores"]

    budget_strength = min(
        int(rules["budget_strength"].get(input_data.signal_type, 0)),
        int(max_scores["budget_strength"]),
    )
    reasons = []
    if budget_strength:
        reasons.append(f"{input_data.signal_type} 预算强度 +{budget_strength}")

    scenario_fit, scenario_reasons = _sum_flags(
        input_data.scenario_flags,
        rules["scenario_fit"],
        int(max_scores["scenario_fit"]),
    )
    timing, timing_reasons = _sum_flags(
        input_data.timing_flags,
        rules["timing"],
        int(max_scores["timing"]),
    )
    reachability, reachability_reasons = _sum_flags(
        input_data.reachability_flags,
        rules["reachability"],
        int(max_scores["reachability"]),
    )
    leverage, leverage_reasons = _sum_flags(
        input_data.leverage_flags,
        rules["leverage"],
        int(max_scores["leverage"]),
    )

    reasons.extend(scenario_reasons + timing_reasons + reachability_reasons + leverage_reasons)
    total = budget_strength + scenario_fit + timing + reachability + leverage

    return LeadScoringResult(
        total_score=total,
        grade=grade_for_score(total, rules),
        breakdown={
            "budget_strength": budget_strength,
            "scenario_fit": scenario_fit,
            "timing": timing,
            "reachability": reachability,
            "leverage": leverage,
        },
        reasons=reasons,
    )
