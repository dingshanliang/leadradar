"""Expand configured keywords into concrete search queries."""

from __future__ import annotations

from pathlib import Path

import yaml


def _keywords_file() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / "keywords.yml"


def expand_queries(keyword_mode: str) -> list[dict[str, str | None]]:
    """Return a list of query descriptors.

    Each descriptor has keys:
      - keyword_group: str
      - keyword: str | None
      - query: str
    """
    with open(_keywords_file(), encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    groups = raw.get("keyword_groups", {})
    queries: list[dict[str, str | None]] = []

    for group_name, group_data in groups.items():
        keywords = group_data.get("keywords", [])
        if keyword_mode == "by_group":
            queries.append({
                "keyword_group": group_name,
                "keyword": None,
                "query": " ".join(keywords),
            })
        else:
            for kw in keywords:
                queries.append({
                    "keyword_group": group_name,
                    "keyword": kw,
                    "query": kw,
                })

    return queries
