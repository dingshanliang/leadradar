"""GreenFood (中国绿色食品发展中心) crawler — search + fetch providers.

Crawls the green food product announcement pages at greenfood.agri.cn.
Newly certified producers signal packaging/labeling upgrade needs.

The query system requires CAPTCHA (not allowed by project constraints),
so we crawl the publicly accessible announcement listing instead:
  - List: /cpgg/lsspgg/ (paginated, 142 pages)
  - Detail: each announcement has an HTML table with certified products

Announcement table columns: 生产单位, 核准用标产品, 商标, 绿色食品编号, 企业信息码
"""

from __future__ import annotations

import asyncio
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult

_BASE_URL = "http://www.greenfood.agri.cn"
_LIST_URL = f"{_BASE_URL}/cpgg/lsspgg/"
_DEFAULT_HEADERS = {
    "User-Agent": "LeadRadarBot/0.1 (+https://github.com/leadradar)",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": f"{_BASE_URL}/",
}


class GreenFoodSearchProvider(SearchProvider):
    """Crawl green food product announcement listing pages.

    Unlike typical search providers, this crawls a paginated directory
    rather than accepting a keyword query. The query parameter is used
    as a filter on the announcement title (e.g. "2026").
    """

    def __init__(self, *, delay_seconds: float = 3.0, timeout: float = 20.0):
        self._delay = delay_seconds
        self._timeout = timeout

    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        all_results: list[SearchResult] = []

        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            page = 0
            while len(all_results) < limit:
                url = f"{_LIST_URL}index_{page}.htm" if page > 0 else _LIST_URL
                resp = await client.get(url)
                resp.raise_for_status()

                page_results = _parse_announcement_list(resp.text, query)

                if not page_results and page == 0:
                    break
                if not page_results:
                    break

                all_results.extend(page_results)

                if not _has_next_page(resp.text):
                    break

                page += 1
                await asyncio.sleep(self._delay)

        await asyncio.sleep(self._delay)
        return all_results[:limit]


class GreenFoodFetchProvider(FetchProvider):
    """Fetch a single green food announcement detail page."""

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


def _parse_announcement_list(html: str, query: str = "") -> list[SearchResult]:
    """Parse announcement listing page, optionally filtering by query."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[SearchResult] = []

    content = soup.select_one(".con, .list, .cpgg_nr, ul")
    if not content:
        content = soup

    for link in content.select("a[href]"):
        href = link.get("href", "")
        title = link.get_text(strip=True)

        if not title or not href:
            continue
        if "公告" not in title:
            continue

        if query and query.lower() not in title.lower():
            continue

        if href.startswith("./"):
            href = urljoin(_LIST_URL, href)
        elif href.startswith("/"):
            href = urljoin(_BASE_URL, href)

        date_tag = link.find_next("span") or link.find_next_sibling()
        published_at = None
        if date_tag:
            date_text = date_tag.get_text(strip=True) if hasattr(date_tag, "get_text") else ""
            match = re.search(r"(\d{4}-\d{2}-\d{2})", date_text)
            if match:
                published_at = match.group(1)

        parent_li = link.find_parent("li")
        if parent_li and not published_at:
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", parent_li.get_text())
            if date_match:
                published_at = date_match.group(1)

        results.append(
            SearchResult(
                title=title,
                url=href,
                snippet=None,
                published_at=published_at,
            )
        )

    return results


def _has_next_page(html: str) -> bool:
    """Check if there's a '下一页' link in pagination."""
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.find("a", string=re.compile(r"下一页"))
    if next_link:
        return True
    links = soup.select("a[href]")
    for link in links:
        text = link.get_text(strip=True)
        if text == "下一页":
            return True
    return False
