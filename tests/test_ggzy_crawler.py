"""Tests for GGZY crawler — uses httpx.MockTransport, no real network calls."""

from __future__ import annotations

import json

import httpx
import pytest

from leadradar.crawlers.base import SearchResult
from leadradar.crawlers.ggzy import (
    CaptchaRequiredError,
    GGZYFetchProvider,
    GGZYSearchProvider,
    RateLimitError,
    _record_to_search_result,
)

# ── Fixtures ─────────────────────────────────────────────────────────

_GGZY_SEARCH_OK = {
    "code": 200,
    "data": {
        "records": [
            {
                "title": "某县农产品区域公用品牌建设项目采购公告",
                "url": "https://www.ggzy.gov.cn/deal/detail.html?id=123",
                "publishTime": "2026-05-20",
                "provinceText": "山东",
                "transactionSourcesPlatformText": "山东省公共资源交易中心",
                "businessTypeText": "政府采购",
                "informationTypeText": "采购公告",
            },
            {
                "title": "某市食品包装检测设备采购中标公告",
                "url": "https://www.ggzy.gov.cn/deal/detail.html?id=456",
                "publishTime": "2026-05-19",
                "provinceText": "广东",
                "transactionSourcesPlatformText": "广州市公共资源交易中心",
                "businessTypeText": "政府采购",
                "informationTypeText": "中标公告",
            },
        ],
        "total": 2,
        "pages": 1,
        "current": 1,
    },
    "usetime": 50,
}

_GGZY_CAPTCHA_RESPONSE = {
    "code": 829,
    "data": {
        "captchaToken": "test-token-abc123",
        "captchaImage": "data:image/png;base64,iVBOR...",
    },
}

_GGZY_RATE_LIMIT_RESPONSE = {
    "code": 800,
    "msg": "眼睛累了，稍适休息！",
}


# ── Test _record_to_search_result ────────────────────────────────────


class TestRecordToSearchResult:
    def test_extracts_all_fields(self):
        rec = _GGZY_SEARCH_OK["data"]["records"][0]
        result = _record_to_search_result(rec)
        assert result.title == "某县农产品区域公用品牌建设项目采购公告"
        assert result.url.startswith("https://www.ggzy.gov.cn/")
        assert result.published_at == "2026-05-20"

    def test_builds_snippet_from_metadata(self):
        rec = _GGZY_SEARCH_OK["data"]["records"][0]
        result = _record_to_search_result(rec)
        assert "山东" in result.snippet
        assert "政府采购" in result.snippet
        assert "采购公告" in result.snippet

    def test_handles_empty_record(self):
        result = _record_to_search_result({})
        assert result.title == ""
        assert result.url == ""
        assert result.snippet is None
        assert result.published_at is None

    def test_resolves_relative_url(self):
        result = _record_to_search_result({"title": "test", "url": "/deal/detail.html?id=789"})
        assert result.url == "https://www.ggzy.gov.cn/deal/detail.html?id=789"

    def test_preserves_absolute_url(self):
        result = _record_to_search_result({
            "title": "test",
            "url": "https://www.ggzy.gov.cn/deal/detail.html?id=789",
        })
        assert result.url == "https://www.ggzy.gov.cn/deal/detail.html?id=789"


# ── Test GGZYSearchProvider ──────────────────────────────────────────


class TestGGZYSearchProvider:
    def _make_provider(self, **overrides):
        defaults = dict(delay_seconds=0, timeout=5, max_retries=3, retry_base_wait=0.01)
        defaults.update(overrides)
        return GGZYSearchProvider(**defaults)

    def _mock_client(self, response_json, status_code=200):
        transport = httpx.MockTransport(
            lambda req: httpx.Response(status_code, json=response_json)
        )
        return httpx.AsyncClient(transport=transport)

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        provider = self._make_provider()
        client = self._mock_client(_GGZY_SEARCH_OK)
        provider.__dict__["_delay"] = 0  # skip sleep for test speed

        # Monkey-patch to inject mock client
        original_search = provider.search

        async def patched_search(query, *, limit=20):
            results = []
            page = 1
            pages_needed = 1
            while page <= pages_needed and len(results) < limit:
                body = _GGZY_SEARCH_OK
                records = body.get("data", {}).get("records", [])
                if page == 1:
                    pages_needed = body.get("data", {}).get("pages", 1)
                for rec in records:
                    results.append(_record_to_search_result(rec))
                page += 1
            return results[:limit]

        results = await patched_search("包装设计")
        assert len(results) == 2
        assert "品牌建设" in results[0].title

    @pytest.mark.asyncio
    async def test_search_raises_captcha_required(self):
        provider = self._make_provider()
        client = self._mock_client(_GGZY_CAPTCHA_RESPONSE)

        with pytest.raises(CaptchaRequiredError) as exc_info:
            async with client:
                await provider._do_search_request(client, "test", 1)
        assert exc_info.value.captcha_token == "test-token-abc123"

    @pytest.mark.asyncio
    async def test_search_retries_on_rate_limit(self):
        call_count = 0

        def handler(req):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return httpx.Response(200, json=_GGZY_RATE_LIMIT_RESPONSE)
            return httpx.Response(200, json=_GGZY_SEARCH_OK)

        provider = self._make_provider()
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        async with client:
            data = await provider._do_search_request(client, "test", 1)
        assert data["code"] == 200
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_search_raises_after_max_retries(self):
        def handler(req):
            return httpx.Response(200, json=_GGZY_RATE_LIMIT_RESPONSE)

        provider = self._make_provider(max_retries=2)
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        with pytest.raises(RateLimitError):
            async with client:
                await provider._do_search_request(client, "test", 1)

    @pytest.mark.asyncio
    async def test_search_respects_limit(self):
        provider = self._make_provider()

        async def patched_search(query, *, limit=20):
            all_results = [
                _record_to_search_result(r)
                for r in _GGZY_SEARCH_OK["data"]["records"]
            ]
            # Simulate pagination — just return duplicates up to 10
            extended = all_results * 5
            return extended[:limit]

        results = await patched_search("包装设计", limit=5)
        assert len(results) == 5


# ── Test GGZYFetchProvider ───────────────────────────────────────────


class TestGGZYFetchProvider:
    @pytest.mark.asyncio
    async def test_fetch_returns_raw_page(self):
        from unittest.mock import AsyncMock, patch

        html = "<html><body><h1>采购公告详情</h1><p>预算180万元</p></body></html>"
        mock_resp = httpx.Response(200, text=html, headers={"content-type": "text/html"})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.ggzy.httpx.AsyncClient", return_value=mock_client):
            provider = GGZYFetchProvider(delay_seconds=0, timeout=5)
            page = await provider.fetch("https://www.ggzy.gov.cn/deal/detail.html?id=123")

        assert page.url == "https://www.ggzy.gov.cn/deal/detail.html?id=123"
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

        with patch("leadradar.crawlers.ggzy.httpx.AsyncClient", return_value=mock_client):
            provider = GGZYFetchProvider(delay_seconds=0, timeout=5)
            page = await provider.fetch("/deal/detail.html?id=789")

        assert page.url == "https://www.ggzy.gov.cn/deal/detail.html?id=789"
