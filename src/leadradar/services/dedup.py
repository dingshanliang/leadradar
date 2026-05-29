"""Deduplication utilities for search results and documents.

Multi-level dedup:
  1. Exact URL match (fastest)
  2. Content hash match (same content, different URL)
  3. Title similarity (fuzzy match for cross-source duplicates)
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

from leadradar.crawlers.base import SearchResult

_SIMILARITY_THRESHOLD = 0.7


def deduplicate_search_results(
    results: list[SearchResult],
    *,
    similarity_threshold: float = _SIMILARITY_THRESHOLD,
) -> list[SearchResult]:
    """Deduplicate a list of SearchResults by URL and title similarity.

    Processing order: first occurrence wins, duplicates are dropped.
    """
    if not results:
        return results

    seen_urls: set[str] = set()
    seen_titles: list[str] = []
    deduped: list[SearchResult] = []

    for result in results:
        normalized_url = _normalize_url(result.url)

        if normalized_url and normalized_url in seen_urls:
            continue

        cleaned = _clean_title(result.title)
        if _is_similar_to_any(cleaned, seen_titles, similarity_threshold):
            continue

        if normalized_url:
            seen_urls.add(normalized_url)
        seen_titles.append(cleaned)
        deduped.append(result)

    return deduped


def _normalize_url(url: str) -> str:
    """Normalize URL for comparison: strip fragment, trailing slash, scheme."""
    if not url:
        return ""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    query = f"?{parsed.query}" if parsed.query else ""
    netloc = parsed.netloc.lower()
    if not netloc:
        return url.strip().lower()
    return f"{netloc}{path}{query}"


def _clean_title(title: str) -> str:
    """Clean title for comparison: strip HTML tags, dates, normalize whitespace."""
    cleaned = re.sub(r"</?em>", "", title)
    cleaned = re.sub(r"\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.lower().strip()


def _is_similar_to_any(
    title: str,
    candidates: list[str],
    threshold: float,
) -> bool:
    """Check if title is similar to any candidate above threshold."""
    for candidate in candidates:
        if not candidate:
            continue
        if title == candidate:
            return True
        shorter, longer = sorted([title, candidate], key=len)
        if len(shorter) < 4:
            continue
        ratio = SequenceMatcher(None, title, candidate).ratio()
        if ratio >= threshold:
            return True
    return False
