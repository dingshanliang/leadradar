"""Tests for GreenFood (中国绿色食品发展中心) crawler."""

from __future__ import annotations

import httpx
import pytest

from leadradar.crawlers.greenfood import (
    GreenFoodFetchProvider,
    GreenFoodSearchProvider,
    _has_next_page,
    _parse_announcement_list,
)

# ── Fixtures ──────────────────────────────────────────────────────────

_GREENFOOD_LIST_HTML = """\
<html><body>
<div class="con">
<ul>
<li>
    <a href="./202603/t20260325_8822564.htm">绿色食品产品公告(2026年第5180号)</a>
    <span>2026-03-25</span>
</li>
<li>
    <a href="./202603/t20260325_8822561.htm">绿色食品产品公告(2026年第5178号)</a>
    <span>2026-03-25</span>
</li>
<li>
    <a href="./202603/t20260325_8822560.htm">绿色食品产品公告(2026年第5176号)</a>
    <span>2026-03-25</span>
</li>
</ul>
<div class="pages">
<a>首页</a>
<a>上一页</a>
<a>1</a>
<a href="index_1.htm">2</a>
<a href="index_2.htm">3</a>
<a href="index_1.htm">下一页</a>
<a href="index_141.htm">尾页</a>
</div>
</div>
</body></html>
"""

_GREENFOOD_LIST_LAST_PAGE_HTML = """\
<html><body>
<div class="con">
<ul>
<li>
    <a href="./202501/t20250115_8822564.htm">绿色食品产品公告(2025年第1000号)</a>
    <span>2025-01-15</span>
</li>
</ul>
<div class="pages">
<a>首页</a>
<a href="index_140.htm">上一页</a>
<a>尾页</a>
</div>
</div>
</body></html>
"""

_GREENFOOD_EMPTY_HTML = """\
<html><body><p>暂无数据</p></body></html>
"""


# ── Test _parse_announcement_list ─────────────────────────────────────


class TestParseAnnouncementList:
    def test_extracts_announcements(self):
        results = _parse_announcement_list(_GREENFOOD_LIST_HTML)
        assert len(results) == 3
        assert "5180号" in results[0].title
        assert "5178号" in results[1].title

    def test_builds_full_urls(self):
        results = _parse_announcement_list(_GREENFOOD_LIST_HTML)
        assert results[0].url.startswith("http://www.greenfood.agri.cn/cpgg/lsspgg/")
        assert "8822564" in results[0].url

    def test_extracts_dates(self):
        results = _parse_announcement_list(_GREENFOOD_LIST_HTML)
        assert results[0].published_at == "2026-03-25"
        assert results[1].published_at == "2026-03-25"

    def test_filters_by_query(self):
        results = _parse_announcement_list(_GREENFOOD_LIST_HTML, query="5178")
        assert len(results) == 1
        assert "5178号" in results[0].title

    def test_no_match_filter(self):
        results = _parse_announcement_list(_GREENFOOD_LIST_HTML, query="2024")
        assert len(results) == 0

    def test_empty_html(self):
        results = _parse_announcement_list(_GREENFOOD_EMPTY_HTML)
        assert len(results) == 0

    def test_skips_non_announcement_links(self):
        html = '<ul><li><a href="/about.html">关于我们</a></li></ul>'
        results = _parse_announcement_list(html)
        assert len(results) == 0


# ── Test _has_next_page ──────────────────────────────────────────────


class TestHasNextPage:
    def test_has_next_link(self):
        assert _has_next_page(_GREENFOOD_LIST_HTML) is True

    def test_last_page(self):
        assert _has_next_page(_GREENFOOD_LIST_LAST_PAGE_HTML) is False

    def test_no_pagination(self):
        assert _has_next_page(_GREENFOOD_EMPTY_HTML) is False


# ── Test GreenFoodSearchProvider ──────────────────────────────────────


class TestGreenFoodSearchProvider:
    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, text=_GREENFOOD_LIST_LAST_PAGE_HTML)
        mock_resp._request = httpx.Request("GET", "http://test")

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.greenfood.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.greenfood.asyncio.sleep", new_callable=AsyncMock):
                provider = GreenFoodSearchProvider(delay_seconds=0)
                results = await provider.search("2025")

        assert len(results) == 1
        assert "1000号" in results[0].title

    @pytest.mark.asyncio
    async def test_search_empty(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, text=_GREENFOOD_EMPTY_HTML)
        mock_resp._request = httpx.Request("GET", "http://test")

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.greenfood.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.greenfood.asyncio.sleep", new_callable=AsyncMock):
                provider = GreenFoodSearchProvider(delay_seconds=0)
                results = await provider.search("测试")

        assert len(results) == 0


# ── Test GreenFoodFetchProvider ───────────────────────────────────────


class TestGreenFoodFetchProvider:
    @pytest.mark.asyncio
    async def test_fetch_returns_raw_page(self):
        from unittest.mock import AsyncMock, patch

        html = "<html><body><h1>绿色食品公告详情</h1></body></html>"
        mock_resp = httpx.Response(200, text=html)
        mock_resp._request = httpx.Request("GET", "http://test")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.greenfood.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.greenfood.asyncio.sleep", new_callable=AsyncMock):
                provider = GreenFoodFetchProvider(delay_seconds=0)
                page = await provider.fetch(
                    "http://www.greenfood.agri.cn/cpgg/lsspgg/202603/t20260325_8822564.htm"
                )

        assert page.status_code == 200
        assert "绿色食品公告" in page.text

    @pytest.mark.asyncio
    async def test_fetch_resolves_relative_url(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, text="<html></html>")
        mock_resp._request = httpx.Request("GET", "http://test")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.greenfood.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.greenfood.asyncio.sleep", new_callable=AsyncMock):
                provider = GreenFoodFetchProvider(delay_seconds=0)
                page = await provider.fetch("/cpgg/lsspgg/index_1.htm")

        assert page.url.startswith("http://www.greenfood.agri.cn/")
