"""CCGP (中国政府采购网) crawler — search + fetch providers.

Only crawls publicly accessible pages. Respects rate limits via configurable
delay between requests. No login/captcha bypass.
"""

from __future__ import annotations

import asyncio
import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult

_BASE_SEARCH_URL = "https://search.ccgp.gov.cn/bxsearch"
_DEFAULT_HEADERS = {
    "User-Agent": "LeadRadarBot/0.1 (+https://github.com/leadradar)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class CCGPSearchProvider(SearchProvider):
    """Search CCGP by keyword, parse server-rendered result list."""

    def __init__(self, *, delay_seconds: float = 2.0, timeout: float = 20.0):
        self._delay = delay_seconds
        self._timeout = timeout

    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        params = {
            "searchtype": "1",
            "page_index": "1",
            "bidSort": "0",
            "pinMu": "0",
            "bidType": "1",
            "dbselect": "bidx",
            "kw": query,
            "timeType": "6",
            "displayZone": "",
            "zoneId": "",
            "pppStatus": "0",
            "agentName": "",
        }

        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            resp = await client.get(_BASE_SEARCH_URL, params=params)
            resp.raise_for_status()

        await asyncio.sleep(self._delay)
        return _parse_search_results(resp.text)[:limit]


class CCGPFetchProvider(FetchProvider):
    """Fetch a single CCGP announcement page."""

    def __init__(self, *, delay_seconds: float = 2.0, timeout: float = 20.0):
        self._delay = delay_seconds
        self._timeout = timeout

    async def fetch(self, url: str) -> RawPage:
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


def _parse_search_results(html: str) -> list[SearchResult]:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("ul.vT-srch-result-list-bid > li")
    results: list[SearchResult] = []

    for li in items:
        link = li.select_one("a[href]")
        if not link:
            continue

        title = link.get_text(strip=True)
        url = link.get("href", "")
        snippet_tag = li.select_one("p")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else None

        span_tag = li.select_one("span")
        published_at = None
        if span_tag:
            date_match = re.search(r"(\d{4}\.\d{2}\.\d{2})", span_tag.get_text())
            if date_match:
                published_at = date_match.group(1).replace(".", "-")

        results.append(
            SearchResult(
                title=title,
                url=url,
                snippet=snippet,
                published_at=published_at,
            )
        )

    return results
