"""AQSC (全国名特优新农产品名录) crawler — search + fetch providers.

Crawls the "名特优新" product registry at mtyx.aqsc.org.
Newly certified agricultural product producers = potential packaging/labeling leads.

ThinkPHP form-based search:
  POST /Home/Minglu/index.html with form fields
  Response is HTML table with pagination links

No captcha, no signing, no WAF. Standard HTML form submission.
"""

from __future__ import annotations

import asyncio
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult

_BASE_URL = "http://mtyx.aqsc.org"
_SEARCH_URL = f"{_BASE_URL}/Home/Minglu/index.html"
_DEFAULT_HEADERS = {
    "User-Agent": "LeadRadarBot/0.1 (+https://github.com/leadradar)",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": f"{_BASE_URL}/",
}


class AQSCSearchProvider(SearchProvider):
    """Search the 名特优新 product registry by product name keyword."""

    def __init__(self, *, delay_seconds: float = 3.0, timeout: float = 20.0):
        self._delay = delay_seconds
        self._timeout = timeout

    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        page_size = min(limit, 100)
        all_results: list[SearchResult] = []

        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            data = {
                "search_rows_limit": str(page_size),
                "search_post_action": "search",
                "order_rule": "default",
                "order_rule_index": "-1",
                "eq_dq_province": "-999",
                "eq_bu_hz_id": "-999",
                "li_productname1": query,
                "bt_yx_dt[]": "",
            }
            resp = await client.post(_SEARCH_URL, data=data)
            resp.raise_for_status()

            all_results, total = _parse_search_page(resp.text)

            fetched = len(all_results)
            page = 2
            while fetched < min(limit, total) and total > page_size:
                await asyncio.sleep(self._delay)
                page_url = f"{_BASE_URL}/Home/Minglu/index/p/{page}.html"
                resp = await client.get(page_url)
                resp.raise_for_status()

                page_results, _ = _parse_search_page(resp.text)
                if not page_results:
                    break

                all_results.extend(page_results)
                fetched += len(page_results)
                page += 1

        await asyncio.sleep(self._delay)
        return all_results[:limit]


class AQSCFetchProvider(FetchProvider):
    """Fetch a single AQSC product detail or listing page."""

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


def _parse_search_page(html: str) -> tuple[list[SearchResult], int]:
    """Parse one page of AQSC search results HTML.

    Returns (results, total_count).
    """
    soup = BeautifulSoup(html, "html.parser")
    total = _extract_total(soup)

    table = soup.select_one("table")
    if not table:
        return [], total

    results: list[SearchResult] = []
    rows = table.select("tbody tr")
    if not rows:
        rows = table.select("tr")

    for row in rows:
        if not isinstance(row, Tag):
            continue
        cells = row.select("td")
        if len(cells) < 7:
            continue

        product_name = cells[1].get_text(strip=True)
        province = cells[2].get_text(strip=True)
        county = cells[3].get_text(strip=True)
        cert_unit = cells[4].get_text(strip=True)
        expiry = cells[5].get_text(strip=True)
        producers = cells[6].get_text(strip=True)
        cert_no = cells[7].get_text(strip=True) if len(cells) > 7 else ""

        snippet_parts = [p for p in [province, county, cert_unit] if p]
        snippet = f"{' '.join(snippet_parts)} | 生产单位: {producers}" if snippet_parts else None

        results.append(
            SearchResult(
                title=product_name,
                url="",
                snippet=snippet,
                published_at=expiry if expiry else None,
            )
        )

    return results, total


def _extract_total(soup: BeautifulSoup) -> int:
    """Extract total record count from pagination info."""
    pager = soup.select_one(".pagination, .page-info, .dataTables_info")
    if pager:
        match = re.search(r"共(\d+)条", pager.get_text())
        if match:
            return int(match.group(1))

    for text_el in soup.find_all(string=re.compile(r"共\d+条")):
        match = re.search(r"共(\d+)条", text_el)
        if match:
            return int(match.group(1))

    return 0
