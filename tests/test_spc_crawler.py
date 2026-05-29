"""Tests for SPC (食品安全抽检公布结果查询系统) crawler."""

from __future__ import annotations

import httpx
import pytest

from leadradar.crawlers.base import SearchResult
from leadradar.crawlers.spc import (
    SPCFetchProvider,
    SPCSearchProvider,
    _record_to_search_result,
)

# ── Fixtures ──────────────────────────────────────────────────────────

_SPC_SEARCH_RESPONSE = {
    "state": 200,
    "request": None,
    "message": "",
    "cause": "",
    "variables": {},
    "data": {
        "dataResult": [
            {
                "id": "30686862",
                "bcscqymc": "授权商：山东三福健康产业有限公司；生产商：泰安泰山三福健康产业有限公司",
                "bcscqydz": "授权商地址：/；生产商地址：山东省泰安市泰山风景名胜区下港镇下里村1号",
                "bcydwmc": "山东三福健康产业有限公司",
                "spmc": "包装饮用水",
                "ggxh": "350ml/袋",
                "scrq": "2023-06-22",
                "bhgxm": None,
                "sfhg": "1",
            },
            {
                "id": "40123456",
                "bcscqymc": "某某食品有限公司",
                "bcscqydz": "浙江省杭州市西湖区某某路123号",
                "bcydwmc": "杭州某某超市有限公司",
                "spmc": "红烧牛肉面",
                "ggxh": "120g/袋",
                "scrq": "2024-01-15",
                "bhgxm": "苯甲酸及其钠盐",
                "sfhg": "0",
            },
        ],
        "limit": 10,
        "page": 1,
        "totalCount": 2,
        "hasNext": False,
    },
}

_SPC_SEARCH_PAGE2_RESPONSE = {
    "state": 200,
    "data": {
        "dataResult": [
            {
                "id": "50789012",
                "bcscqymc": "另一家公司",
                "bcydwmc": "某检测机构",
                "spmc": "花生酱",
                "ggxh": "200g/瓶",
                "scrq": "2024-03-10",
                "bhgxm": "黄曲霉毒素B1",
                "sfhg": "0",
            },
        ],
        "limit": 10,
        "page": 2,
        "totalCount": 15,
        "hasNext": False,
    },
}

_SPC_EMPTY_RESPONSE = {
    "state": 200,
    "data": {
        "dataResult": [],
        "limit": 10,
        "page": 1,
        "totalCount": 0,
        "hasNext": False,
    },
}

_SPC_ERROR_RESPONSE = {
    "state": 500,
    "message": "Internal server error",
}


# ── Test record parser ────────────────────────────────────────────────


class TestRecordToSearchResult:
    def test_qualified_record(self):
        rec = _SPC_SEARCH_RESPONSE["data"]["dataResult"][0]
        result = _record_to_search_result(rec)
        assert result.title == "包装饮用水"
        assert "30686862" in result.url
        assert "合格" in (result.snippet or "")
        assert "山东三福" in (result.snippet or "")
        assert result.published_at == "2023-06-22"

    def test_unqualified_record_with_bhgxm(self):
        rec = _SPC_SEARCH_RESPONSE["data"]["dataResult"][1]
        result = _record_to_search_result(rec)
        assert result.title == "红烧牛肉面"
        assert "不合格" in (result.snippet or "")
        assert "苯甲酸及其钠盐" in (result.snippet or "")
        assert "某某食品" in (result.snippet or "")

    def test_empty_record(self):
        result = _record_to_search_result({})
        assert result.title == ""
        assert result.url == ""
        assert result.snippet is None

    def test_record_without_id(self):
        result = _record_to_search_result({"spmc": "测试食品", "sfhg": "1"})
        assert result.url == ""

    def test_record_builds_url_with_id(self):
        result = _record_to_search_result({"id": "99999"})
        assert "99999" in result.url
        assert "spcjsac.gsxt.gov.cn" in result.url


# ── Test SPCSearchProvider ────────────────────────────────────────────


class TestSPCSearchProvider:
    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, json=_SPC_SEARCH_RESPONSE)
        mock_resp._request = httpx.Request("POST", "http://test")
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.spc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.spc.asyncio.sleep", new_callable=AsyncMock):
                provider = SPCSearchProvider(delay_seconds=0)
                results = await provider.search("包装")

        assert len(results) == 2
        assert results[0].title == "包装饮用水"
        assert "合格" in (results[0].snippet or "")

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, json=_SPC_EMPTY_RESPONSE)
        mock_resp._request = httpx.Request("POST", "http://test")
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.spc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.spc.asyncio.sleep", new_callable=AsyncMock):
                provider = SPCSearchProvider(delay_seconds=0)
                results = await provider.search("不存在的食品")

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_stops_on_error_state(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, json=_SPC_ERROR_RESPONSE)
        mock_resp._request = httpx.Request("POST", "http://test")
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.spc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.spc.asyncio.sleep", new_callable=AsyncMock):
                provider = SPCSearchProvider(delay_seconds=0)
                results = await provider.search("测试")

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_sends_correct_request_body(self):
        from unittest.mock import AsyncMock, patch

        captured_body = {}

        async def capture_post(url, json=None, **kwargs):
            captured_body.update(json or {})
            mock_resp = httpx.Response(200, json=_SPC_SEARCH_RESPONSE)
            mock_resp._request = httpx.Request("POST", "http://test")
            return mock_resp

        mock_client = AsyncMock()
        mock_client.post = capture_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.spc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.spc.asyncio.sleep", new_callable=AsyncMock):
                provider = SPCSearchProvider(search_type="企业名称", delay_seconds=0)
                await provider.search("某某公司")

        assert captured_body["searchKey"] == "某某公司"
        assert captured_body["activeName"] == "企业名称"
        assert captured_body["page"] == 1

    @pytest.mark.asyncio
    async def test_search_pagination(self):
        from unittest.mock import AsyncMock, patch

        page1_resp_data = {
            "state": 200,
            "data": {
                "dataResult": _SPC_SEARCH_RESPONSE["data"]["dataResult"],
                "limit": 10,
                "page": 1,
                "totalCount": 15,
                "hasNext": True,
            },
        }
        call_count = 0

        async def multi_post(url, json=None, **kwargs):
            nonlocal call_count
            call_count += 1
            if json and json.get("page") == 1:
                resp_data = page1_resp_data
            else:
                resp_data = _SPC_SEARCH_PAGE2_RESPONSE
            mock_resp = httpx.Response(200, json=resp_data)
            mock_resp._request = httpx.Request("POST", "http://test")
            return mock_resp

        mock_client = AsyncMock()
        mock_client.post = multi_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.spc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.spc.asyncio.sleep", new_callable=AsyncMock):
                provider = SPCSearchProvider(delay_seconds=0)
                results = await provider.search("测试", limit=20)

        assert call_count == 2
        assert len(results) == 3


# ── Test SPCFetchProvider ─────────────────────────────────────────────


class TestSPCFetchProvider:
    @pytest.mark.asyncio
    async def test_fetch_returns_raw_page(self):
        from unittest.mock import AsyncMock, patch

        html = "<html><body><h1>抽检详情</h1></body></html>"
        mock_resp = httpx.Response(200, text=html)
        mock_resp._request = httpx.Request("GET", "http://test")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.spc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.spc.asyncio.sleep", new_callable=AsyncMock):
                provider = SPCFetchProvider(delay_seconds=0)
                page = await provider.fetch("https://spcjsac.gsxt.gov.cn/#/detail?id=123")

        assert page.status_code == 200
        assert "抽检详情" in page.text

    @pytest.mark.asyncio
    async def test_fetch_resolves_relative_url(self):
        from unittest.mock import AsyncMock, patch

        mock_resp = httpx.Response(200, text="<html></html>")
        mock_resp._request = httpx.Request("GET", "http://test")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("leadradar.crawlers.spc.httpx.AsyncClient", return_value=mock_client):
            with patch("leadradar.crawlers.spc.asyncio.sleep", new_callable=AsyncMock):
                provider = SPCFetchProvider(delay_seconds=0)
                page = await provider.fetch("/some/path")

        assert page.url.startswith("https://spcjsac.gsxt.gov.cn/")
