"""Provincial government procurement crawlers.

Supports multiple provincial CCGP sites through a platform-aware config system.
Each province has its own API format and search behavior, grouped by backend platform:

- custom_vue: Shandong (POST JSON API, no captcha)
- gpcms: Guangdong + Sichuan (GET API with JS signing)

Provinces not yet supported:
- jiangsu: Requires captcha (raises CaptchaRequiredError)
- zhejiang: Alibaba Cloud WAF (requires headless browser)
- jiangxi: Site unavailable (SSL certificate error)
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult

_DEFAULT_HEADERS = {
    "User-Agent": "LeadRadarBot/0.1 (+https://github.com/leadradar)",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class CaptchaRequiredError(Exception):
    """Provincial site requires CAPTCHA verification (e.g. jiangsu)."""


# ── Provincial Config ────────────────────────────────────────────────


@dataclass(frozen=True)
class ProvincialConfig:
    name: str
    base_url: str
    search_url: str
    platform: str  # "custom_vue" | "gpcms"
    site_id: str | None = None
    channel_ids: str | None = None


PROVINCES: dict[str, ProvincialConfig] = {
    "shandong": ProvincialConfig(
        name="山东省政府采购网",
        base_url="http://www.ccgp-shandong.gov.cn",
        search_url="http://www.ccgp-shandong.gov.cn:8087/api/website/site/searchAllByCode",
        platform="custom_vue",
    ),
    "guangdong": ProvincialConfig(
        name="广东省政府采购网",
        base_url="https://gdgpo.czt.gd.gov.cn",
        search_url="https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex",
        platform="gpcms",
        site_id="cd64e06a-21a7-4620-aebc-0576bab7e07a",
        channel_ids="fca71be5-fc0c-45db-96af-f513e9abda9d,95ff31f3-a1af-4bc4-b1a2-54c894476193",
    ),
    "sichuan": ProvincialConfig(
        name="四川省政府采购网",
        base_url="https://www.ccgp-sichuan.gov.cn",
        search_url="https://www.ccgp-sichuan.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex",
        platform="gpcms",
        site_id="94c965cc-c55d-4f92-8469-d5875c68bd04",
        channel_ids="fca71be5-fc0c-45db-96af-f513e9abda9d,95ff31f3-a1af-4bc4-b1a2-54c894476193",
    ),
}


# ── Search Provider ──────────────────────────────────────────────────


class ProvincialSearchProvider(SearchProvider):
    """Search a provincial government procurement site by keyword."""

    def __init__(
        self,
        province: str,
        *,
        delay_seconds: float = 3.0,
        timeout: float = 20.0,
    ):
        if province not in PROVINCES:
            raise ValueError(
                f"Unknown province '{province}'. "
                f"Available: {list(PROVINCES.keys())}"
            )
        self._config = PROVINCES[province]
        self._delay = delay_seconds
        self._timeout = timeout

    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        if self._config.platform == "custom_vue":
            results = await self._search_custom_vue(query, limit)
        elif self._config.platform == "gpcms":
            results = await self._search_gpcms(query, limit)
        else:
            raise ValueError(f"Unsupported platform: {self._config.platform}")

        await asyncio.sleep(self._delay)
        return results[:limit]

    async def _search_custom_vue(self, query: str, limit: int) -> list[SearchResult]:
        """Shandong-style: POST JSON API."""
        from datetime import datetime, timedelta

        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        page_size = min(limit, 20)

        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=self._timeout,
        ) as client:
            all_results: list[SearchResult] = []
            page = 1

            while len(all_results) < limit:
                body = {
                    "type": "01",
                    "title": query,
                    "area": "",
                    "currentPage": page,
                    "pageSize": page_size,
                    "startTime": thirty_days_ago.strftime("%Y-%m-%d 00:00:00"),
                    "endTime": now.strftime("%Y-%m-%d 23:59:59"),
                }
                resp = await client.post(
                    self._config.search_url,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()

                records = data.get("data", {}).get("records", []) or data.get("data", [])
                if not records:
                    break

                for rec in records:
                    all_results.append(_parse_custom_vue_record(rec, self._config.base_url))

                total = data.get("data", {}).get("total", 0) or 0
                if page * page_size >= total:
                    break

                page += 1
                await asyncio.sleep(self._delay)

        return all_results

    async def _search_gpcms(self, query: str, limit: int) -> list[SearchResult]:
        """Guangdong/Sichuan gpcms platform: GET API with signing."""
        from datetime import datetime, timedelta

        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        page_size = min(limit, 20)

        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=self._timeout,
        ) as client:
            all_results: list[SearchResult] = []
            page = 1

            while len(all_results) < limit:
                params = {
                    "currPage": str(page),
                    "pageSize": str(page_size),
                    "siteId": self._config.site_id,
                    "channel": self._config.channel_ids,
                    "noticeType": "",
                    "purchaser": "",
                    "agency": "",
                    "operationStartTime": thirty_days_ago.strftime("%Y-%m-%d 00:00:00"),
                    "operationEndTime": now.strftime("%Y-%m-%d 23:59:59"),
                    "searchKey": query,
                    "regionCode": "",
                }

                headers = _build_gpcms_headers(params)

                resp = await client.get(
                    self._config.search_url,
                    params=params,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

                records = data.get("data", {}).get("list", [])
                if not records:
                    break

                for rec in records:
                    all_results.append(_parse_gpcms_record(rec, self._config.base_url))

                total = data.get("data", {}).get("total", 0) or 0
                if page * page_size >= total:
                    break

                page += 1
                await asyncio.sleep(self._delay)

        return all_results


# ── Fetch Provider ───────────────────────────────────────────────────


class ProvincialFetchProvider(FetchProvider):
    """Fetch a single provincial procurement announcement page."""

    def __init__(
        self,
        province: str,
        *,
        delay_seconds: float = 3.0,
        timeout: float = 20.0,
    ):
        if province not in PROVINCES:
            raise ValueError(f"Unknown province '{province}'")
        self._config = PROVINCES[province]
        self._delay = delay_seconds
        self._timeout = timeout

    async def fetch(self, url: str) -> RawPage:
        if url.startswith("/"):
            url = urljoin(self._config.base_url, url)

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


# ── Record parsers ───────────────────────────────────────────────────


def _parse_custom_vue_record(rec: dict, base_url: str) -> SearchResult:
    """Parse a Shandong-style JSON record."""
    title = rec.get("title", "")
    url = rec.get("url", "")
    if not url and rec.get("id"):
        url = f"{base_url}/detail.html?id={rec['id']}"
    elif url.startswith("/"):
        url = urljoin(base_url, url)

    parts = [rec.get("areaName", ""), rec.get("userName", "")]
    snippet = " | ".join(p for p in parts if p) or None
    published_at = rec.get("date")

    return SearchResult(
        title=title,
        url=url,
        snippet=snippet,
        published_at=published_at,
    )


def _parse_gpcms_record(rec: dict, base_url: str) -> SearchResult:
    """Parse a gpcms (Guangdong/Sichuan) JSON record."""
    title = rec.get("title", "")
    url = rec.get("url", "")
    if not url and rec.get("id"):
        url = f"{base_url}/article/{rec['id']}"
    elif url.startswith("/"):
        url = urljoin(base_url, url)

    parts = [
        rec.get("regionName", ""),
        rec.get("noticeTypeName", ""),
        rec.get("purchaser", ""),
    ]
    budget = rec.get("budget")
    if budget:
        parts.append(f"预算: {budget}")
    snippet = " | ".join(p for p in parts if p) or None

    published_at = rec.get("operationStartTime", "").split(" ")[0] or None

    return SearchResult(
        title=title,
        url=url,
        snippet=snippet,
        published_at=published_at,
    )


# ── gpcms signing helper ─────────────────────────────────────────────


def _build_gpcms_headers(params: dict) -> dict:
    """Build request headers with signing for gpcms platform.

    The gpcms platform requires nsssjss and sign headers computed from
    query parameters. This implements a basic signing scheme that may
    need adjustment based on the actual JS logic.
    """
    timestamp = str(int(time.time() * 1000))
    param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v)
    sign = hashlib.md5(f"{param_str}{timestamp}".encode()).hexdigest()

    return {
        **_DEFAULT_HEADERS,
        "nsssjss": timestamp,
        "sign": sign,
        "requestSource": "qwjs",
    }
