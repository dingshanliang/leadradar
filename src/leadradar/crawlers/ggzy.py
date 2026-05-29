"""GGZY (全国公共资源交易平台) crawler — search + fetch providers.

Searches via JSON API at /information/pubTradingInfo/getTradList.
Respects rate limits with exponential backoff. Raises CaptchaRequiredError
instead of attempting to bypass CAPTCHA challenges.
"""

from __future__ import annotations

import asyncio
from urllib.parse import urljoin

import httpx

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult
from leadradar.crawlers.registry import register as _register

_BASE_URL = "https://www.ggzy.gov.cn"
_SEARCH_API = f"{_BASE_URL}/information/pubTradingInfo/getTradList"
_DEFAULT_HEADERS = {
    "User-Agent": "LeadRadarBot/0.1 (+https://github.com/leadradar)",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": f"{_BASE_URL}/deal/dealList.html",
}


class CaptchaRequiredError(Exception):
    """GGZY API returned code 829 — CAPTCHA verification required."""

    def __init__(self, captcha_token: str = "", captcha_image: str = ""):
        self.captcha_token = captcha_token
        self.captcha_image = captcha_image
        super().__init__("GGZY requires CAPTCHA verification")


class RateLimitError(Exception):
    """GGZY API returned code 800 — too many requests."""


class GGZYSearchProvider(SearchProvider):
    """Search GGZY via JSON API with keyword query."""

    def __init__(
        self,
        *,
        deal_classify: str = "02",
        deal_stage: str = "0200",
        source_type: str = "1",
        deal_province: str = "0",
        delay_seconds: float = 3.0,
        timeout: float = 20.0,
        max_retries: int = 3,
        retry_base_wait: float = 10.0,
    ):
        self._deal_classify = deal_classify
        self._deal_stage = deal_stage
        self._source_type = source_type
        self._deal_province = deal_province
        self._delay = delay_seconds
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_base_wait = retry_base_wait

    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        results: list[SearchResult] = []
        page = 1
        pages_needed = 1

        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            while page <= pages_needed and len(results) < limit:
                data = await self._do_search_request(client, query, page)
                records = data.get("data", {}).get("records", [])

                if page == 1:
                    pages_needed = data.get("data", {}).get("pages", 1)

                for rec in records:
                    results.append(_record_to_search_result(rec))

                if page < pages_needed:
                    await asyncio.sleep(self._delay)

                page += 1

        await asyncio.sleep(self._delay)
        return results[:limit]

    async def _do_search_request(
        self,
        client: httpx.AsyncClient,
        query: str,
        page: int,
    ) -> dict:
        form: dict[str, str] = {"PAGENUMBER": str(page)}
        if query:
            form["FINDTXT"] = query
        if self._source_type:
            form["SOURCE_TYPE"] = self._source_type
        if self._deal_classify != "00":
            form["DEAL_CLASSIFY"] = self._deal_classify
        if self._deal_stage and self._deal_stage[2:] != "00":
            form["DEAL_STAGE"] = self._deal_stage
        if self._deal_province != "0":
            form["DEAL_PROVINCE"] = self._deal_province

        for attempt in range(self._max_retries):
            resp = await client.post(
                _SEARCH_API,
                data=form,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            body = resp.json()

            code = body.get("code")
            if code == 200:
                return body
            elif code == 829:
                captcha_data = body.get("data", {})
                raise CaptchaRequiredError(
                    captcha_token=captcha_data.get("captchaToken", ""),
                    captcha_image=captcha_data.get("captchaImage", ""),
                )
            elif code == 800:
                wait = self._retry_base_wait * (2**attempt)
                await asyncio.sleep(wait)
                continue
            else:
                raise httpx.HTTPStatusError(
                    f"GGZY API error: code={code}, msg={body.get('message', '')}",
                    request=resp.request,
                    response=resp,
                )

        raise RateLimitError(f"GGZY rate limit persisted after {self._max_retries} retries")


class GGZYFetchProvider(FetchProvider):
    """Fetch a single GGZY announcement page."""

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
    title = rec.get("title", "")
    url = rec.get("url", "")
    if url.startswith("/"):
        url = urljoin(_BASE_URL, url)

    parts = [
        rec.get("provinceText", ""),
        rec.get("businessTypeText", ""),
        rec.get("informationTypeText", ""),
    ]
    snippet = " | ".join(p for p in parts if p) or None

    return SearchResult(
        title=title,
        url=url,
        snippet=snippet,
        published_at=rec.get("publishTime"),
    )


# ── registry ─────────────────────────────────────────────────────

_register("ggzy", GGZYSearchProvider, GGZYFetchProvider)
