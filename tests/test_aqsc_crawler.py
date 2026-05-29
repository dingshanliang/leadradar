"""Tests for AQSC (全国名特优新农产品名录) crawler."""

from __future__ import annotations

import httpx
import pytest

from leadradar.crawlers.aqsc import (
    AQSCFetchProvider,
    AQSCSearchProvider,
    _extract_total,
    _parse_search_page,
)

# ── Fixtures ──────────────────────────────────────────────────────────

_AQSC_SEARCH_HTML = """\
<html><body>
<table id="dynamic-table" class="table table-striped table-bordered">
<thead>
<tr>
    <th>序号</th>
    <th>产品名称</th>
    <th>省份</th>
    <th>县域</th>
    <th>获证单位</th>
    <th>有效期</th>
    <th>主要生产经营单位</th>
    <th>证书编号</th>
</tr>
</thead>
<tbody>
<tr>
    <td>1</td>
    <td>灵宝苹果</td>
    <td>河南省</td>
    <td>灵宝市</td>
    <td>灵宝市园艺局</td>
    <td>2027-05-09</td>
    <td>灵宝市高山天然果品有限责任公司<br>灵宝市永辉果业有限责任公司</td>
    <td>CAQS-MTYX-20190001</td>
</tr>
<tr>
    <td>2</td>
    <td>洛宁上戈苹果</td>
    <td>河南省</td>
    <td>洛宁县</td>
    <td>洛宁县园艺技术服务中心</td>
    <td>2027-05-09</td>
    <td>洛阳众森农业有限公司<br>洛阳上果农业有限公司</td>
    <td>CAQS-MTYX-20190018</td>
</tr>
</tbody>
</table>
<span class="rows">共2条记录, 当前页1 / 1</span>
</body></html>
"""

_AQSC_EMPTY_HTML = """\
<html><body>
<table id="dynamic-table" class="table">
<thead><tr><th>序号</th><th>产品名称</th><th>省份</th></tr></thead>
<tbody></tbody>
</table>
<span class="rows">共0条记录</span>
</body></html>
"""

_AQSC_NO_TABLE_HTML = """\
<html><body><p>系统维护中</p></body></html>
"""


# ── Test _parse_search_page ──────────────────────────────────────────


class TestParseSearchPage:
    def test_extracts_results(self):
        results, total = _parse_search_page(_AQSC_SEARCH_HTML)
        assert total == 2
        assert len(results) == 2
        assert results[0].title == "灵宝苹果"
        assert results[1].title == "洛宁上戈苹果"

    def test_snippet_contains_province_and_county(self):
        results, _ = _parse_search_page(_AQSC_SEARCH_HTML)
        assert "河南省" in results[0].snippet
        assert "灵宝市" in results[0].snippet
        assert "灵宝市园艺局" in results[0].snippet

    def test_published_at_is_expiry_date(self):
        results, _ = _parse_search_page(_AQSC_SEARCH_HTML)
        assert results[0].published_at == "2027-05-09"

    def test_url_is_empty_for_registry_items(self):
        results, _ = _parse_search_page(_AQSC_SEARCH_HTML)
        assert results[0].url == ""

    def test_empty_table_returns_empty(self):
        results, total = _parse_search_page(_AQSC_EMPTY_HTML)
        assert total == 0
        assert len(results) == 0

    def test_no_table_returns_empty(self):
        results, total = _parse_search_page(_AQSC_NO_TABLE_HTML)
        assert total == 0
        assert len(results) == 0


# ── Test _extract_total ──────────────────────────────────────────────


class TestExtractTotal:
    def test_extracts_from_span_rows(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<span class="rows">共8036条记录, 当前页1 / 402</span>',
            "html.parser",
        )
        assert _extract_total(soup) == 8036

    def test_extracts_from_plain_text(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<p>共50条记录</p>", "html.parser")
        assert _extract_total(soup) == 50

    def test_no_match_returns_zero(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<p>无数据</p>", "html.parser")
        assert _extract_total(soup) == 0


# ── Test AQSCSearchProvider ──────────────────────────────────────────


class TestAQSCSearchProvider:
    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, text=_AQSC_SEARCH_HTML)
        mock_resp._request = httpx.Request("POST", "http://test")

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.aqsc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.aqsc.asyncio.sleep", new_callable=AsyncMock):
                provider = AQSCSearchProvider(delay_seconds=0)
                results = await provider.search("苹果")

        assert len(results) == 2
        assert results[0].title == "灵宝苹果"

    @pytest.mark.asyncio
    async def test_search_empty(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, text=_AQSC_EMPTY_HTML)
        mock_resp._request = httpx.Request("POST", "http://test")

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.aqsc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.aqsc.asyncio.sleep", new_callable=AsyncMock):
                provider = AQSCSearchProvider(delay_seconds=0)
                results = await provider.search("不存在的产品")

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_posts_with_correct_form_data(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, text=_AQSC_EMPTY_HTML)
        mock_resp._request = httpx.Request("POST", "http://test")

        captured_data = {}

        async def mock_post(url, **kwargs):
            captured_data.update(kwargs.get("data", {}))
            return mock_resp

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.aqsc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.aqsc.asyncio.sleep", new_callable=AsyncMock):
                provider = AQSCSearchProvider(delay_seconds=0)
                await provider.search("大米")

        assert captured_data["li_productname1"] == "大米"
        assert captured_data["search_post_action"] == "search"
        assert captured_data["eq_dq_province"] == "-999"


# ── Test AQSCFetchProvider ───────────────────────────────────────────


class TestAQSCFetchProvider:
    @pytest.mark.asyncio
    async def test_fetch_returns_raw_page(self):
        from unittest.mock import AsyncMock, patch

        html = "<html><body><h1>灵宝苹果详情</h1></body></html>"
        mock_resp = httpx.Response(200, text=html)
        mock_resp._request = httpx.Request("GET", "http://test")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.aqsc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.aqsc.asyncio.sleep", new_callable=AsyncMock):
                provider = AQSCFetchProvider(delay_seconds=0)
                page = await provider.fetch("http://mtyx.aqsc.org/detail/123.html")

        assert page.status_code == 200
        assert "灵宝苹果" in page.text

    @pytest.mark.asyncio
    async def test_fetch_resolves_relative_url(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, text="<html></html>")
        mock_resp._request = httpx.Request("GET", "http://test")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.aqsc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.aqsc.asyncio.sleep", new_callable=AsyncMock):
                provider = AQSCFetchProvider(delay_seconds=0)
                page = await provider.fetch("/Home/Minglu/index.html")

        assert page.url.startswith("http://mtyx.aqsc.org/")
