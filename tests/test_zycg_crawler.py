"""Tests for ZYCG (中央政府采购网) crawler."""

from __future__ import annotations

import httpx
import pytest

from leadradar.crawlers.zycg import (
    ZYCGFetchProvider,
    ZYCGSearchProvider,
    _clean_title_highlight,
    _record_to_search_result,
)

# ── Fixtures ──────────────────────────────────────────────────────────

_ZYCG_SEARCH_RESPONSE = {
    "msg": "操作成功",
    "total": 496,
    "code": "200",
    "data": [
        {
            "addtimeStr": "2026-05-18 07:01:25",
            "pageUrl": "/freecms/site/zygjjgzfcgzx/ggxx/info/2026/5e1aa31b-abc.html",
            "id": "54c01917-5244-11f1-9615-fa163ee0ead6",
            "title": "民族团结杂志社2025-2028年《中国民族》杂志<em>印刷</em>服务采购项目招标公告",
        },
        {
            "addtimeStr": "2026-05-15 09:30:00",
            "pageUrl": "/freecms/site/zygjjgzfcgzx/ggxx/info/2026/def456.html",
            "id": "67890123-abcd-11f1-9615-fa163ee0ead6",
            "title": "国家市场监督管理总局食品检<em>测</em>设备采购中标公告",
        },
    ],
}

_ZYCG_EMPTY_RESPONSE = {
    "msg": "操作成功",
    "total": 0,
    "code": "200",
    "data": [],
}

_ZYCG_ERROR_RESPONSE = {
    "msg": "系统异常",
    "total": 0,
    "code": "500",
    "data": None,
}


# ── Test helpers ──────────────────────────────────────────────────────


class TestCleanTitleHighlight:
    def test_removes_em_tags(self):
        assert _clean_title_highlight("食品<em>包装</em>检测") == "食品包装检测"

    def test_no_tags(self):
        assert _clean_title_highlight("正常标题") == "正常标题"

    def test_empty_string(self):
        assert _clean_title_highlight("") == ""


# ── Test record parser ────────────────────────────────────────────────


class TestRecordToSearchResult:
    def test_extracts_title_without_highlight(self):
        rec = _ZYCG_SEARCH_RESPONSE["data"][0]
        result = _record_to_search_result(rec)
        assert "印刷" in result.title
        assert "<em>" not in result.title

    def test_builds_full_url(self):
        rec = _ZYCG_SEARCH_RESPONSE["data"][0]
        result = _record_to_search_result(rec)
        assert result.url.startswith("https://www.zycg.gov.cn/")
        assert "5e1aa31b" in result.url

    def test_extracts_date(self):
        rec = _ZYCG_SEARCH_RESPONSE["data"][0]
        result = _record_to_search_result(rec)
        assert result.published_at == "2026-05-18"

    def test_handles_empty_record(self):
        result = _record_to_search_result({})
        assert result.title == ""
        assert result.url == ""
        assert result.published_at is None

    def test_handles_pageurl_key_variant(self):
        result = _record_to_search_result({"title": "测试", "pageurl": "/path/to/page"})
        assert "/path/to/page" in result.url


# ── Test ZYCGSearchProvider ───────────────────────────────────────────


class TestZYCGSearchProvider:
    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        from unittest.mock import AsyncMock, patch

        session_resp = httpx.Response(200, text="<html></html>")
        session_resp._request = httpx.Request("GET", "http://test")

        search_data = {
            "msg": "操作成功",
            "total": 2,
            "code": "200",
            "data": _ZYCG_SEARCH_RESPONSE["data"],
        }
        search_resp = httpx.Response(200, json=search_data)
        search_resp._request = httpx.Request("GET", "http://test")

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return session_resp
            return search_resp

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.zycg.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.zycg.asyncio.sleep", new_callable=AsyncMock):
                provider = ZYCGSearchProvider(delay_seconds=0)
                results = await provider.search("印刷")

        assert len(results) == 2
        assert "印刷" in results[0].title
        assert "<em>" not in results[0].title

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        from unittest.mock import AsyncMock, patch

        session_resp = httpx.Response(200, text="<html></html>")
        session_resp._request = httpx.Request("GET", "http://test")

        search_resp = httpx.Response(200, json=_ZYCG_EMPTY_RESPONSE)
        search_resp._request = httpx.Request("GET", "http://test")

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return session_resp
            return search_resp

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.zycg.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.zycg.asyncio.sleep", new_callable=AsyncMock):
                provider = ZYCGSearchProvider(delay_seconds=0)
                results = await provider.search("不存在的内容")

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_stops_on_error(self):
        from unittest.mock import AsyncMock, patch

        session_resp = httpx.Response(200, text="<html></html>")
        session_resp._request = httpx.Request("GET", "http://test")

        search_resp = httpx.Response(200, json=_ZYCG_ERROR_RESPONSE)
        search_resp._request = httpx.Request("GET", "http://test")

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return session_resp
            return search_resp

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.zycg.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.zycg.asyncio.sleep", new_callable=AsyncMock):
                provider = ZYCGSearchProvider(delay_seconds=0)
                results = await provider.search("测试")

        assert len(results) == 0


# ── Test ZYCGFetchProvider ────────────────────────────────────────────


class TestZYCGFetchProvider:
    @pytest.mark.asyncio
    async def test_fetch_returns_raw_page(self):
        from unittest.mock import AsyncMock, patch

        html = "<html><body><h1>采购公告详情</h1></body></html>"
        mock_resp = httpx.Response(200, text=html)
        mock_resp._request = httpx.Request("GET", "http://test")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.zycg.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.zycg.asyncio.sleep", new_callable=AsyncMock):
                provider = ZYCGFetchProvider(delay_seconds=0)
                page = await provider.fetch(
                    "https://www.zycg.gov.cn/freecms/site/zygjjgzfcgzx/ggxx/info/2026/abc.html"
                )

        assert page.status_code == 200
        assert "采购公告详情" in page.text

    @pytest.mark.asyncio
    async def test_fetch_resolves_relative_url(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, text="<html></html>")
        mock_resp._request = httpx.Request("GET", "http://test")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.zycg.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.zycg.asyncio.sleep", new_callable=AsyncMock):
                provider = ZYCGFetchProvider(delay_seconds=0)
                page = await provider.fetch("/freecms/site/test.html")

        assert page.url.startswith("https://www.zycg.gov.cn/")
