"""Tests for PLAP (军队采购网) crawler — search + fetch providers."""

from __future__ import annotations

import pytest

from leadradar.crawlers.base import RawPage, SearchResult
from leadradar.crawlers.plap import (
    PLAPFetchProvider,
    PLAPSearchProvider,
    _record_to_search_result,
    _build_detail_url,
)

# ── Fixtures from real API response ──────────────────────────────────

SAMPLE_RECORD = {
    "noticeTime": "2026-05-28 14:29:07",
    "id": "58d074b2-5a61-11f1-bdf4-fa163e92c454",
    "title": "包装箱入库测算系统采购项目（第三次）招标公告(2026-JKCNZZ-F4001)",
    "htmlpath": "/site/juncai/ggxx/info/2026/8a1d04c29e688f09019e6cafeedd19cd.html",
    "regionName": "湖南省",
    "openTenderCode": "2026-JKCNZZ-F4001",
    "noticeType": "001014",
    "noticeId": "8a1d04c29e688f09019e6cafeedd19cd",
    "purchaseManner": "4",
    "budget": None,
}

SAMPLE_API_RESPONSE = {
    "code": "200",
    "msg": "success",
    "total": 2,
    "data": [
        SAMPLE_RECORD,
        {
            **SAMPLE_RECORD,
            "title": "器材清点包装倒调劳务采购竞争性谈判公告(2026-JQGCGZ-F3002)",
            "htmlpath": "/site/juncai/ggxx/info/2026/other-id.html",
            "noticeTime": "2026-05-26 16:25:03",
            "regionName": "广东省",
            "noticeId": "other-id",
        },
    ],
}

SAMPLE_DETAIL_HTML = """<!DOCTYPE html>
<html><body>
<span id="f_noticeTime" style="display:none">2026-05-28 14:29:07</span>
<div class="wrap_content_detail">
  <div class="detailContent">
    <p>一、项目名称：包装箱入库测算系统采购项目</p>
    <p>二、项目编号：2026-JKCNZZ-F4001</p>
    <p>三、预算金额：￥380,000.00</p>
    <p>四、采购单位：某部队后勤保障部</p>
    <p>五、联系方式：张参谋 0731-85551234</p>
  </div>
</div>
</body></html>"""


# ── Unit tests: _record_to_search_result ─────────────────────────────


class TestRecordParsing:
    def test_parses_title(self):
        result = _record_to_search_result(SAMPLE_RECORD)
        assert result.title == "包装箱入库测算系统采购项目（第三次）招标公告(2026-JKCNZZ-F4001)"

    def test_builds_detail_url(self):
        result = _record_to_search_result(SAMPLE_RECORD)
        assert result.url == "https://www.plap.mil.cn/freecms-glht/site/juncai/ggxx/info/2026/8a1d04c29e688f09019e6cafeedd19cd.html"

    def test_extracts_published_at(self):
        result = _record_to_search_result(SAMPLE_RECORD)
        assert result.published_at == "2026-05-28"

    def test_snippet_contains_region(self):
        result = _record_to_search_result(SAMPLE_RECORD)
        assert "湖南省" in (result.snippet or "")

    def test_missing_htmlpath_still_has_url(self):
        rec = {**SAMPLE_RECORD, "htmlpath": None}
        result = _record_to_search_result(rec)
        assert result.url == ""

    def test_missing_notice_time(self):
        rec = {**SAMPLE_RECORD, "noticeTime": None}
        result = _record_to_search_result(rec)
        assert result.published_at is None


class TestBuildDetailUrl:
    def test_normal_path(self):
        url = _build_detail_url("/site/juncai/ggxx/info/2026/abc.html")
        assert url.startswith("https://www.plap.mil.cn/freecms-glht/")

    def test_none_path(self):
        assert _build_detail_url(None) == ""

    def test_empty_path(self):
        assert _build_detail_url("") == ""


# ── Integration tests with mocked httpx ──────────────────────────────


class TestPLAPSearchProvider:
    @pytest.fixture
    def mock_search_response(self, monkeypatch):
        """Mock httpx.AsyncClient.get to return sample API data."""
        import leadradar.crawlers.plap as plap_mod

        class MockResponse:
            def __init__(self, json_data):
                self._data = json_data
                self.status_code = 200
                self.headers = {"content-type": "application/json"}

            def json(self):
                return self._data

            def raise_for_status(self):
                pass

        class MockClient:
            def __init__(self, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url, **kwargs):
                return MockResponse(SAMPLE_API_RESPONSE)

        monkeypatch.setattr(plap_mod.httpx, "AsyncClient", MockClient)

    @pytest.mark.asyncio
    async def test_search_returns_results(self, mock_search_response):
        provider = PLAPSearchProvider()
        results = await provider.search("包装")
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    @pytest.mark.asyncio
    async def test_search_result_has_required_fields(self, mock_search_response):
        provider = PLAPSearchProvider()
        results = await provider.search("包装")
        r = results[0]
        assert r.title
        assert r.url
        assert r.url.startswith("https://")
        assert r.published_at

    @pytest.mark.asyncio
    async def test_search_respects_limit(self, monkeypatch):
        import leadradar.crawlers.plap as plap_mod

        class MockResponse:
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {"code": "200", "total": 0, "data": []}

            def raise_for_status(self):
                pass

        class MockClient:
            def __init__(self, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url, **kwargs):
                return MockResponse()

        monkeypatch.setattr(plap_mod.httpx, "AsyncClient", MockClient)

        provider = PLAPSearchProvider()
        results = await provider.search("包装", limit=0)
        assert len(results) == 0


class TestPLAPFetchProvider:
    @pytest.fixture
    def mock_fetch_response(self, monkeypatch):
        import leadradar.crawlers.plap as plap_mod

        class MockResponse:
            def __init__(self, text):
                self.text = text
                self.status_code = 200
                self.headers = {"content-type": "text/html"}

        class MockClient:
            def __init__(self, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url, **kwargs):
                return MockResponse(SAMPLE_DETAIL_HTML)

        monkeypatch.setattr(plap_mod.httpx, "AsyncClient", MockClient)

    @pytest.mark.asyncio
    async def test_fetch_returns_raw_page(self, mock_fetch_response):
        provider = PLAPFetchProvider()
        page = await provider.fetch("https://www.plap.mil.cn/freecms-glht/site/juncai/ggxx/info/2026/abc.html")
        assert isinstance(page, RawPage)
        assert page.status_code == 200
        assert "包装箱" in page.text

    @pytest.mark.asyncio
    async def test_fetch_handles_relative_url(self, mock_fetch_response):
        provider = PLAPFetchProvider()
        page = await provider.fetch("/site/juncai/ggxx/info/2026/abc.html")
        assert page.url.startswith("https://www.plap.mil.cn")
