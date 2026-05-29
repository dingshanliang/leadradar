from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from leadradar.schemas import LeadScoringInput, LeadScoringResult
from leadradar.services.scoring_rule_set import ScoringRuleSet

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[2] / "data" / "scoring_rules.yml"


def load_scoring_rules(path: Path = DEFAULT_RULES_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _sum_flags(
    flag_names: list[str], dimension: str, rule_set: ScoringRuleSet
) -> tuple[int, list[str]]:
    total = 0
    reasons: list[str] = []
    for flag in flag_names:
        points = rule_set.flag_score(dimension, flag)
        if points:
            total += points
            reasons.append(f"{flag} +{points}")
    return min(total, rule_set.max_score(dimension)), reasons


def score_lead(
    input_data: LeadScoringInput, rules: dict[str, Any] | None = None
) -> LeadScoringResult:
    rule_set = ScoringRuleSet(data=rules)

    budget_strength = min(
        rule_set.flag_score("budget_strength", input_data.signal_type),
        rule_set.max_score("budget_strength"),
    )
    reasons = []
    if budget_strength:
        reasons.append(f"{input_data.signal_type} 预算强度 +{budget_strength}")

    scenario_fit, scenario_reasons = _sum_flags(
        input_data.scenario_flags, "scenario_fit", rule_set
    )
    timing, timing_reasons = _sum_flags(
        input_data.timing_flags, "timing", rule_set
    )
    reachability, reachability_reasons = _sum_flags(
        input_data.reachability_flags, "reachability", rule_set
    )
    leverage, leverage_reasons = _sum_flags(
        input_data.leverage_flags, "leverage", rule_set
    )

    reasons.extend(scenario_reasons + timing_reasons + reachability_reasons + leverage_reasons)
    total = budget_strength + scenario_fit + timing + reachability + leverage

    return LeadScoringResult(
        total_score=total,
        grade=rule_set.grade_for_total(total),
        breakdown={
            "budget_strength": budget_strength,
            "scenario_fit": scenario_fit,
            "timing": timing,
            "reachability": reachability,
            "leverage": leverage,
        },
        reasons=reasons,
    )
