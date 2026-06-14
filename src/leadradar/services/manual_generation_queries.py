"""Expand configured keywords into concrete search queries."""

from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]


def _keywords_file() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / "keywords.yml"


def expand_queries(
    keyword_mode: str,
    *,
    keyword_groups: list[str] | None = None,
    keywords: list[str] | None = None,
) -> list[dict[str, str | None]]:
    """Return a list of query descriptors.

    Each descriptor has keys:
      - keyword_group: str
      - keyword: str | None
      - query: str

    If ``keyword_groups`` is provided, only those groups are considered.
    If ``keywords`` is provided, only those keywords are considered (only
    meaningful when ``keyword_mode`` is ``by_keyword``).
    """
    with open(_keywords_file(), encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    groups = raw.get("keyword_groups", {})
    if keyword_groups:
        groups = {k: v for k, v in groups.items() if k in keyword_groups}

    queries: list[dict[str, str | None]] = []

    for group_name, group_data in groups.items():
        group_keywords = group_data.get("keywords", [])
        if keywords:
            group_keywords = [kw for kw in group_keywords if kw in keywords]
        if not group_keywords:
            continue
        if keyword_mode == "by_group":
            queries.append({
                "keyword_group": group_name,
                "keyword": None,
                "query": " ".join(group_keywords),
            })
        else:
            for kw in group_keywords:
                queries.append({
                    "keyword_group": group_name,
                    "keyword": kw,
                    "query": kw,
                })

    return queries
