"""SPC (食品安全抽检公布结果查询系统) crawler — search + fetch providers.

Queries the food safety sampling inspection results system at
spcjsac.gsxt.gov.cn. This is a leading indicator: companies with failed
inspections likely need testing equipment upgrades or packaging improvements.

API: POST /pjgcx/cjPubInfo/getJgcxList
Request: JSON {"searchKey", "activeName", "pageType", "imageToken", "page", "limit"}
Response: {state: 200, data: {dataResult: [...], totalCount, hasNext}}

No captcha, no signing, no WAF — straightforward JSON POST.
"""

from __future__ import annotations

import asyncio
from urllib.parse import urljoin

import httpx

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult

_BASE_URL = "https://spcjsac.gsxt.gov.cn"
_SEARCH_API = f"{_BASE_URL}/pjgcx/cjPubInfo/getJgcxList"
_DEFAULT_HEADERS = {
    "User-Agent": "LeadRadarBot/0.1 (+https://github.com/leadradar)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Content-Type": "application/json",
    "Referer": f"{_BASE_URL}/",
}


class SPCSearchProvider(SearchProvider):
    """Search food safety inspection results by keyword."""

    def __init__(
        self,
        *,
        search_type: str = "食品名称",
        delay_seconds: float = 3.0,
        timeout: float = 20.0,
    ):
        self._search_type = search_type
        self._delay = delay_seconds
        self._timeout = timeout

    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        page_size = min(limit, 20)
        all_results: list[SearchResult] = []

        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=self._timeout,
        ) as client:
            page = 1
            while len(all_results) < limit:
                body = {
                    "searchKey": query,
                    "activeName": self._search_type,
                    "pageType": "listPage",
                    "imageToken": "",
                    "percentage": 0.65,
                    "page": page,
                    "limit": page_size,
                }
                resp = await client.post(_SEARCH_API, json=body)
                resp.raise_for_status()
                data = resp.json()

                if data.get("state") != 200:
                    break

                records = data.get("data", {}).get("dataResult", [])
                if not records:
                    break

                for rec in records:
                    all_results.append(_record_to_search_result(rec))

                has_next = data.get("data", {}).get("hasNext", False)
                if not has_next:
                    break

                page += 1
                await asyncio.sleep(self._delay)

        await asyncio.sleep(self._delay)
        return all_results[:limit]


class SPCFetchProvider(FetchProvider):
    """Fetch a single inspection result detail page."""

    def __init__(self, *, delay_seconds: float = 3.0, timeout: float = 20.0):
        self._delay = delay_seconds
        self._timeout = timeout

    async def fetch(self, url: str) -> RawPage:
        if url.startswith("/"):
            url = urljoin(_BASE_URL, url)

        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)

        await asyncio.sleep(self._delay)
        return RawPage(
            url=url,
            status_code=resp.status_code,
            content_type=resp.headers.get("content-type"),
            text=resp.text,
        )


def _record_to_search_result(rec: dict) -> SearchResult:
    """Parse a SPC inspection record into a SearchResult."""
    spmc = rec.get("spmc", "")
    rec_id = rec.get("id", "")
    url = f"{_BASE_URL}/#/detail?id={rec_id}" if rec_id else ""

    sfhg = rec.get("sfhg")
    parts = []
    if sfhg == "0":
        parts.append("不合格")
    elif sfhg == "1":
        parts.append("合格")
    parts.extend([
        rec.get("bcscqymc", ""),
        rec.get("bcydwmc", ""),
    ])
    bhgxm = rec.get("bhgxm")
    if bhgxm:
        parts.append(f"不合格项目: {bhgxm}")
    snippet = " | ".join(p for p in parts if p) or None

    published_at = rec.get("scrq")

    return SearchResult(
        title=spmc,
        url=url,
        snippet=snippet,
        published_at=published_at,
    )
