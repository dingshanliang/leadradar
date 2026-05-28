import pytest

from leadradar.crawlers.base import RawPage, SearchResult
from leadradar.crawlers.parser import HtmlDocumentParser, content_hash
from leadradar.crawlers.search_provider import LocalFixtureFetchProvider, MockSearchProvider


@pytest.fixture
def mock_search():
    return MockSearchProvider()


@pytest.fixture
def mock_fetch():
    return LocalFixtureFetchProvider()


@pytest.fixture
def html_parser():
    return HtmlDocumentParser()


# ── MockSearchProvider ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_mock_search_returns_results(mock_search):
    results = await mock_search.search("区域品牌")
    assert len(results) >= 1
    assert all(isinstance(r, SearchResult) for r in results)


@pytest.mark.asyncio
async def test_mock_search_respects_limit(mock_search):
    results = await mock_search.search("区域品牌", limit=0)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_mock_search_result_has_required_fields(mock_search):
    results = await mock_search.search("区域品牌")
    r = results[0]
    assert r.title
    assert r.url
    assert r.url.startswith("https://")


# ── LocalFixtureFetchProvider ──────────────────────────────────

@pytest.mark.asyncio
async def test_mock_fetch_returns_html(mock_fetch):
    page = await mock_fetch.fetch("https://example.gov.cn/notice/1")
    assert isinstance(page, RawPage)
    assert page.status_code == 200
    assert page.content_type == "text/html"
    assert "采购单位" in page.text
    assert "预算金额" in page.text


@pytest.mark.asyncio
async def test_mock_fetch_preserves_url(mock_fetch):
    url = "https://example.gov.cn/notice/42"
    page = await mock_fetch.fetch(url)
    assert page.url == url


# ── HtmlDocumentParser ─────────────────────────────────────────

def test_html_parser_extracts_text(html_parser):
    page = RawPage(
        url="https://example.com",
        status_code=200,
        content_type="text/html",
        text="<html><body><h1>标题</h1><p>正文内容</p></body></html>",
    )
    text = html_parser.extract_text(page)
    assert "标题" in text
    assert "正文内容" in text


def test_html_parser_strips_scripts(html_parser):
    page = RawPage(
        url="https://example.com",
        status_code=200,
        content_type="text/html",
        text="<html><body><script>alert('x')</script><p>内容</p></body></html>",
    )
    text = html_parser.extract_text(page)
    assert "alert" not in text
    assert "内容" in text


def test_html_parser_strips_styles(html_parser):
    page = RawPage(
        url="https://example.com",
        status_code=200,
        content_type="text/html",
        text="<html><body><style>.x{color:red}</style><p>内容</p></body></html>",
    )
    text = html_parser.extract_text(page)
    assert "color" not in text
    assert "内容" in text


# ── content_hash ───────────────────────────────────────────────

def test_content_hash_deterministic():
    h1 = content_hash("hello world")
    h2 = content_hash("hello world")
    assert h1 == h2


def test_content_hash_different_for_different_input():
    h1 = content_hash("hello")
    h2 = content_hash("world")
    assert h1 != h2


def test_content_hash_is_sha256_hex():
    h = content_hash("test")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)
