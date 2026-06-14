"""Load follow-up validation rules and next-action suggestions from YAML."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DEFAULT_CALL_RESULTS_PATH = DATA_DIR / "call_results.yml"
DEFAULT_SUGGESTIONS_PATH = DATA_DIR / "follow_up_suggestions.yml"


class FollowUpConfigError(Exception):
    pass


def load_call_results(path: Path | None = None) -> dict[str, Any]:
    path = path or DEFAULT_CALL_RESULTS_PATH
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("categories", {})


def load_follow_up_suggestions(path: Path | None = None) -> dict[str, str]:
    path = path or DEFAULT_SUGGESTIONS_PATH
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("rules", {})


def validate_reason(category: str, reason: str, path: Path | None = None) -> None:
    categories = load_call_results(path)
    all_reasons = {
        r for cat in categories.values() for r in cat.get("reasons", [])
    }
    if reason not in all_reasons:
        raise ValueError("Invalid follow-up reason")

    allowed_reasons = categories.get(category, {}).get("reasons", [])
    if reason not in allowed_reasons:
        raise ValueError("结果类别与原因不匹配")


def _parse_duration(value: str) -> timedelta:
    value = value.strip()
    match = re.match(r"^(\d+)\s*([hdw])$", value, re.IGNORECASE)
    if not match:
        raise FollowUpConfigError(f"无法解析建议时间间隔: {value}")
    amount = int(match.group(1))
    unit = match.group(2).lower()
    multipliers = {"h": "hours", "d": "days", "w": "weeks"}
    return timedelta(**{multipliers[unit]: amount})


def get_follow_up_suggestion(
    result: str,
    now: datetime | None = None,
    path: Path | None = None,
) -> datetime | None:
    now = now or datetime.now(timezone.utc)
    rules = load_follow_up_suggestions(path)

    # Match an exact result string first, then fall back to the category part.
    duration_str = rules.get(result)
    if duration_str is None:
        category = result.split(":", 1)[0] if ":" in result else result
        duration_str = rules.get(category)

    if duration_str is None:
        return None

    delta = _parse_duration(duration_str)
    return now + delta
