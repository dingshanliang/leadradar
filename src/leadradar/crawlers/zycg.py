"""ZYCG (中央政府采购网) crawler — search + fetch providers.

Queries the Central Government Procurement Network at www.zycg.gov.cn.
Covers central-level procurement (ministry canteens, agency supplies, etc.)
— high unit value, structured announcements.

Two-step process:
1. Visit any page to obtain JSESSIONID cookie.
2. GET /freecms/rest/v1/notice/searchAll.do?title=...&currPage=...&pageSize=...

No captcha, no signing, no WAF. Just needs a valid session cookie.
"""

from __future__ import annotations

import asyncio
import re
from urllib.parse import urljoin

import httpx

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult
from leadradar.crawlers.registry import register as _register

_BASE_URL = "https://www.zycg.gov.cn"
_SEARCH_API = f"{_BASE_URL}/freecms/rest/v1/notice/searchAll.do"
_SESSION_PAGE = f"{_BASE_URL}/freecms/site/zygjjgzfcgzx/cggg/index.html"
_DEFAULT_HEADERS = {
    "User-Agent": "LeadRadarBot/0.1 (+https://github.com/leadradar)",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": f"{_BASE_URL}/",
}


class ZYCGSearchProvider(SearchProvider):
    """Search ZYCG announcements by keyword."""

    def __init__(
        self,
        *,
        delay_seconds: float = 3.0,
        timeout: float = 20.0,
    ):
        self._delay = delay_seconds
        self._timeout = timeout

    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        page_size = min(limit, 20)
        all_results: list[SearchResult] = []

        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            await client.get(_SESSION_PAGE)

            page = 1
            while len(all_results) < limit:
                params = {
                    "title": query,
                    "currPage": str(page),
                    "pageSize": str(page_size),
                }
                resp = await client.get(_SEARCH_API, params=params)
                resp.raise_for_status()
                data = resp.json()

                if data.get("code") != "200":
                    break

                records = data.get("data", [])
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


class ZYCGFetchProvider(FetchProvider):
    """Fetch a single ZYCG announcement detail page."""

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
    """Parse a ZYCG announcement record into a SearchResult."""
    title = rec.get("title", "")
    page_url = rec.get("pageUrl") or rec.get("pageurl") or ""
    if page_url and not page_url.startswith("http"):
        page_url = urljoin(_BASE_URL, page_url)

    published_at = None
    addtime = rec.get("addtimeStr", "")
    if addtime:
        published_at = addtime.split(" ")[0]

    snippet = _clean_title_highlight(title) if title else None

    return SearchResult(
        title=_clean_title_highlight(title),
        url=page_url,
        snippet=snippet,
        published_at=published_at,
    )


def _clean_title_highlight(title: str) -> str:
    """Remove <em> highlight tags from search result titles."""
    return re.sub(r"</?em>", "", title)


# ── registry ─────────────────────────────────────────────────────

_register("zycg", ZYCGSearchProvider, ZYCGFetchProvider)
