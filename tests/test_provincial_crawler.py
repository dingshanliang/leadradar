"""Tests for provincial government procurement crawlers."""

from __future__ import annotations

import httpx
import pytest

from leadradar.crawlers.base import SearchResult
from leadradar.crawlers.provincial import (
    PROVINCES,
    ProvincialFetchProvider,
    ProvincialSearchProvider,
    _parse_custom_vue_record,
    _parse_gpcms_record,
)

# ── Shandong fixtures ────────────────────────────────────────────────

_SHANDONG_SEARCH_RESPONSE = {
    "code": 200,
    "data": {
        "records": [
            {
                "title": "食品安全抽检技术服务采购公告",
                "id": "abc123",
                "userName": "山东省市场监督管理局",
                "date": "2026-05-20",
                "areaName": "济南",
                "colCode": "zbgg",
                "buyKindCode": "公开招标",
                "projectType": "服务类",
            },
            {
                "title": "农产品包装检测设备采购意向",
                "id": "def456",
                "userName": "济南市农业农村局",
                "date": "2026-05-19",
                "areaName": "济南",
                "colCode": "zbgg",
                "buyKindCode": "竞争性磋商",
                "projectType": "货物类",
            },
        ],
        "total": 2,
        "current": 1,
    },
}

# ── gpcms (Guangdong/Sichuan) fixtures ───────────────────────────────

_GPCMS_SEARCH_RESPONSE = {
    "code": "0",
    "data": {
        "list": [
            {
                "title": "食品包装质量检测仪器采购公告",
                "id": "gd001",
                "url": "/article/gd001",
                "regionName": "广州",
                "noticeTypeName": "采购公告",
                "purchaser": "广州市市场监督管理局",
                "agency": "广东省政府采购中心",
                "budget": "1800000",
                "purchaseManner": "公开招标",
                "operationStartTime": "2026-05-18 10:00:00",
                "regionCode": "440100",
            },
            {
                "title": "区域品牌数字化管理平台中标公告",
                "id": "gd002",
                "url": "/article/gd002",
                "regionName": "深圳",
                "noticeTypeName": "中标公告",
                "purchaser": "深圳市市场监督管理局",
                "agency": "",
                "budget": "",
                "purchaseManner": "竞争性谈判",
                "operationStartTime": "2026-05-17 14:30:00",
                "regionCode": "440300",
            },
        ],
        "total": 2,
    },
}


# ── Test config ──────────────────────────────────────────────────────


class TestProvincialConfig:
    def test_all_provinces_have_configs(self):
        assert "shandong" in PROVINCES
        assert "guangdong" in PROVINCES
        assert "sichuan" in PROVINCES

    def test_shandong_platform(self):
        assert PROVINCES["shandong"].platform == "custom_vue"

    def test_guangdong_sichuan_share_platform(self):
        assert PROVINCES["guangdong"].platform == "gpcms"
        assert PROVINCES["sichuan"].platform == "gpcms"

    def test_gpcms_have_site_id(self):
        assert PROVINCES["guangdong"].site_id is not None
        assert PROVINCES["sichuan"].site_id is not None
        assert PROVINCES["guangdong"].site_id != PROVINCES["sichuan"].site_id

    def test_unknown_province_raises(self):
        with pytest.raises(ValueError, match="Unknown province"):
            ProvincialSearchProvider("hainan")


# ── Test custom_vue record parser (Shandong) ────────────────────────


class TestParseCustomVueRecord:
    def test_extracts_title(self):
        rec = _SHANDONG_SEARCH_RESPONSE["data"]["records"][0]
        result = _parse_custom_vue_record(rec, "http://www.ccgp-shandong.gov.cn")
        assert "食品安全抽检" in result.title

    def test_builds_url_from_id(self):
        rec = _SHANDONG_SEARCH_RESPONSE["data"]["records"][0]
        result = _parse_custom_vue_record(rec, "http://www.ccgp-shandong.gov.cn")
        assert "abc123" in result.url

    def test_builds_snippet(self):
        rec = _SHANDONG_SEARCH_RESPONSE["data"]["records"][0]
        result = _parse_custom_vue_record(rec, "http://www.ccgp-shandong.gov.cn")
        assert "济南" in result.snippet
        assert "山东省市场监督管理局" in result.snippet

    def test_extracts_date(self):
        rec = _SHANDONG_SEARCH_RESPONSE["data"]["records"][0]
        result = _parse_custom_vue_record(rec, "http://www.ccgp-shandong.gov.cn")
        assert result.published_at == "2026-05-20"

    def test_handles_empty_record(self):
        result = _parse_custom_vue_record({}, "http://example.com")
        assert result.title == ""
        assert result.url == ""


# ── Test gpcms record parser (Guangdong/Sichuan) ────────────────────


class TestParseGpcmsRecord:
    def test_extracts_title(self):
        rec = _GPCMS_SEARCH_RESPONSE["data"]["list"][0]
        result = _parse_gpcms_record(rec, "https://gdgpo.czt.gd.gov.cn")
        assert "食品包装" in result.title

    def test_uses_url_from_record(self):
        rec = _GPCMS_SEARCH_RESPONSE["data"]["list"][0]
        result = _parse_gpcms_record(rec, "https://gdgpo.czt.gd.gov.cn")
        assert result.url == "https://gdgpo.czt.gd.gov.cn/article/gd001"

    def test_builds_snippet_with_budget(self):
        rec = _GPCMS_SEARCH_RESPONSE["data"]["list"][0]
        result = _parse_gpcms_record(rec, "https://gdgpo.czt.gd.gov.cn")
        assert "广州" in result.snippet
        assert "采购公告" in result.snippet
        assert "1800000" in result.snippet

    def test_snippet_without_budget(self):
        rec = _GPCMS_SEARCH_RESPONSE["data"]["list"][1]
        result = _parse_gpcms_record(rec, "https://gdgpo.czt.gd.gov.cn")
        assert "预算" not in (result.snippet or "")

    def test_extracts_date(self):
        rec = _GPCMS_SEARCH_RESPONSE["data"]["list"][0]
        result = _parse_gpcms_record(rec, "https://gdgpo.czt.gd.gov.cn")
        assert result.published_at == "2026-05-18"

    def test_handles_empty_record(self):
        result = _parse_gpcms_record({}, "http://example.com")
        assert result.title == ""


# ── Test ProvincialSearchProvider with mocked HTTP ───────────────────


class TestProvincialSearchProvider:
    @pytest.mark.asyncio
    async def test_shandong_search(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, json=_SHANDONG_SEARCH_RESPONSE)
        mock_resp._request = httpx.Request("POST", "http://test")
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.provincial.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.provincial.asyncio.sleep", new_callable=AsyncMock):
                provider = ProvincialSearchProvider("shandong", delay_seconds=0)
                results = await provider.search("包装")

        assert len(results) == 2
        assert "食品安全抽检" in results[0].title

    @pytest.mark.asyncio
    async def test_gpcms_search_guangdong(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, json=_GPCMS_SEARCH_RESPONSE)
        mock_resp._request = httpx.Request("GET", "http://test")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.provincial.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.provincial.asyncio.sleep", new_callable=AsyncMock):
                provider = ProvincialSearchProvider("guangdong", delay_seconds=0)
                results = await provider.search("包装")

        assert len(results) == 2
        assert "食品包装" in results[0].title
        assert "1800000" in (results[0].snippet or "")


# ── Test ProvincialFetchProvider ─────────────────────────────────────


class TestProvincialFetchProvider:
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

        with patch("leadradar.crawlers.provincial.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.provincial.asyncio.sleep", new_callable=AsyncMock):
                provider = ProvincialFetchProvider("shandong", delay_seconds=0)
                page = await provider.fetch("http://www.ccgp-shandong.gov.cn/detail.html?id=123")

        assert page.status_code == 200
        assert "采购公告详情" in page.text

    @pytest.mark.asyncio
    async def test_fetch_resolves_relative_url(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, text="<html></html>")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.provincial.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.provincial.asyncio.sleep", new_callable=AsyncMock):
                provider = ProvincialFetchProvider("guangdong", delay_seconds=0)
                page = await provider.fetch("/article/gd001")

        assert page.url == "https://gdgpo.czt.gd.gov.cn/article/gd001"
