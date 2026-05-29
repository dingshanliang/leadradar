"""PLAP (军队采购网 / People's Liberation Army Procurement) crawler.

Queries the People's Liberation Army procurement portal at www.plap.mil.cn.
Covers military procurement announcements — packaging, logistics, equipment, etc.

API endpoint (freecms REST):
  GET /freecms/rest/v1/notice/selectInfoMoreChannel.do
  Params: siteId, title, noticeType, currPage, pageSize, selectTimeName

No captcha, no login, no RSA header enforcement for public search.
Rate-limited to ~5 seconds between requests as a courtesy.
"""

from __future__ import annotations

import asyncio
from urllib.parse import urljoin

import httpx

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult
from leadradar.crawlers.registry import register as _register

_BASE_URL = "https://www.plap.mil.cn"
_PAGE_BASE = f"{_BASE_URL}/freecms-glht"
_SEARCH_API = f"{_BASE_URL}/freecms/rest/v1/notice/selectInfoMoreChannel.do"
_SITE_ID = "404bb030-5be9-4070-85bd-c94b1473e8de"

# 采购公告 types: 公开招标, 竞争性谈判, 询价, etc.
_DEFAULT_NOTICE_TYPES = "00101,001052,00105B,001031"

_DEFAULT_HEADERS = {
    "User-Agent": "LeadRadarBot/0.1 (+https://github.com/leadradar)",
    "Accept": "application/json, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": f"{_BASE_URL}/",
}


class PLAPSearchProvider(SearchProvider):
    """Search PLAP announcements by keyword."""

    def __init__(
        self,
        *,
        delay_seconds: float = 5.0,
        timeout: float = 20.0,
        notice_types: str = _DEFAULT_NOTICE_TYPES,
    ):
        self._delay = delay_seconds
        self._timeout = timeout
        self._notice_types = notice_types

    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        page_size = min(limit, 20)
        all_results: list[SearchResult] = []

        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            page = 1
            while len(all_results) < limit:
                params = {
                    "siteId": _SITE_ID,
                    "channel": "",
                    "searchKey": "",
                    "title": query,
                    "content": "",
                    "regionCode": "",
                    "noticeType": self._notice_types,
                    "operationStartTime": "",
                    "operationEndTime": "",
                    "selectTimeName": "noticeTime",
                    "currPage": str(page),
                    "pageSize": str(page_size),
                }
                resp = await client.get(_SEARCH_API, params=params)
                resp.raise_for_status()
                data = resp.json()

                records = data.get("data") or []
                if not records:
                    break

                for rec in records:
                    all_results.append(_record_to_search_result(rec))

                total = data.get("total", 0) or 0
                if page * page_size >= total:
                    break

                page += 1
                await asyncio.sleep(self._delay)

        await asyncio.sleep(self._delay)
        return all_results[:limit]


class PLAPFetchProvider(FetchProvider):
    """Fetch a single PLAP announcement detail page."""

    def __init__(self, *, delay_seconds: float = 5.0, timeout: float = 20.0):
        self._delay = delay_seconds
        self._timeout = timeout

    async def fetch(self, url: str) -> RawPage:
        if url.startswith("/"):
            url = urljoin(_PAGE_BASE + "/", url)

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
    title = rec.get("title", "")
    htmlpath = rec.get("htmlpath") or ""
    url = _build_detail_url(htmlpath) if htmlpath else ""

    published_at = None
    notice_time = rec.get("noticeTime", "")
    if notice_time:
        published_at = notice_time.split(" ")[0]

    region = rec.get("regionName", "")
    snippet = f"[{region}] {title}" if region else title

    return SearchResult(
        title=title,
        url=url,
        snippet=snippet,
        published_at=published_at,
    )


def _build_detail_url(htmlpath: str | None) -> str:
    if not htmlpath:
        return ""
    if htmlpath.startswith("http"):
        return htmlpath
    return f"{_PAGE_BASE}{htmlpath}"


# ── registry ─────────────────────────────────────────────────────

_register("plap", PLAPSearchProvider, PLAPFetchProvider)
