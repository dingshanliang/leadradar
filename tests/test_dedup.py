"""Tests for deduplication utilities."""

from __future__ import annotations


from leadradar.crawlers.base import SearchResult
from leadradar.services.dedup import (
    _clean_title,
    _is_similar_to_any,
    _normalize_url,
    deduplicate_search_results,
)


# ── Test _normalize_url ──────────────────────────────────────────────


class TestNormalizeUrl:
    def test_strips_trailing_slash(self):
        assert _normalize_url("http://example.com/path/") == "example.com/path"

    def test_lowercases_domain(self):
        assert _normalize_url("http://EXAMPLE.COM/Path") == "example.com/Path"

    def test_strips_fragment(self):
        norm = _normalize_url("http://example.com/path#section")
        assert "#section" not in norm
        assert "example.com/path" in norm

    def test_preserves_query(self):
        norm = _normalize_url("http://example.com/search?q=test")
        assert "q=test" in norm

    def test_empty_string(self):
        assert _normalize_url("") == ""


# ── Test _clean_title ────────────────────────────────────────────────


class TestCleanTitle:
    def test_removes_em_tags(self):
        assert _clean_title("食品<em>包装</em>检测") == "食品包装检测"

    def test_removes_dates(self):
        result = _clean_title("2026-05-18 采购公告")
        assert "2026" not in result
        assert "采购公告" in result

    def test_removes_chinese_dates(self):
        result = _clean_title("2026年5月18日采购公告")
        assert "采购公告" in result
        assert "2026" not in result

    def test_collapses_whitespace(self):
        assert _clean_title("采购  公告") == "采购 公告"
        assert _clean_title("采购公告  ") == "采购公告"


# ── Test _is_similar_to_any ──────────────────────────────────────────


class TestIsSimilarToAny:
    def test_exact_match(self):
        assert _is_similar_to_any("采购公告", ["采购公告"], 0.7) is True

    def test_similar_titles(self):
        assert _is_similar_to_any("食品包装采购公告", ["食品包装采购公示"], 0.7) is True

    def test_different_titles(self):
        assert _is_similar_to_any("食品包装采购公告", ["办公设备招标公告"], 0.7) is False

    def test_empty_candidates(self):
        assert _is_similar_to_any("采购公告", [], 0.7) is False

    def test_short_title_skipped(self):
        assert _is_similar_to_any("ab", ["cd"], 0.7) is False


# ── Test deduplicate_search_results ──────────────────────────────────


class TestDeduplicateSearchResults:
    def test_dedup_by_url(self):
        results = [
            SearchResult(title="公告A", url="http://example.com/a"),
            SearchResult(title="公告B", url="http://example.com/a"),
        ]
        deduped = deduplicate_search_results(results)
        assert len(deduped) == 1
        assert deduped[0].title == "公告A"

    def test_dedup_by_normalized_url(self):
        results = [
            SearchResult(title="公告A", url="http://example.com/path/"),
            SearchResult(title="公告B", url="http://example.com/path"),
        ]
        deduped = deduplicate_search_results(results)
        assert len(deduped) == 1

    def test_dedup_by_similar_title(self):
        results = [
            SearchResult(title="食品包装采购公告", url="http://a.com/1"),
            SearchResult(title="食品包装采购公示", url="http://b.com/2"),
        ]
        deduped = deduplicate_search_results(results)
        assert len(deduped) == 1

    def test_keeps_different_results(self):
        results = [
            SearchResult(title="食品包装采购公告", url="http://a.com/1"),
            SearchResult(title="办公设备招标公告", url="http://b.com/2"),
        ]
        deduped = deduplicate_search_results(results)
        assert len(deduped) == 2

    def test_empty_list(self):
        assert deduplicate_search_results([]) == []

    def test_first_occurrence_wins(self):
        results = [
            SearchResult(title="公告A", url="http://a.com/1"),
            SearchResult(title="公告B", url="http://a.com/1"),
            SearchResult(title="公告C", url="http://b.com/2"),
        ]
        deduped = deduplicate_search_results(results)
        assert len(deduped) == 2
        assert deduped[0].title == "公告A"
        assert deduped[1].title == "公告C"

    def test_handles_empty_urls(self):
        results = [
            SearchResult(title="公告A", url=""),
            SearchResult(title="公告B", url=""),
        ]
        deduped = deduplicate_search_results(results)
        assert len(deduped) == 2

    def test_dedup_by_fragment_only_difference(self):
        results = [
            SearchResult(title="公告", url="http://example.com/page#top"),
            SearchResult(title="公告2", url="http://example.com/page#bottom"),
        ]
        deduped = deduplicate_search_results(results)
        assert len(deduped) == 1
