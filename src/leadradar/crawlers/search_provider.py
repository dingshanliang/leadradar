from __future__ import annotations

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult


class MockSearchProvider(SearchProvider):
    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        return [
            SearchResult(
                title="某县农产品区域公用品牌建设项目采购意向",
                url="https://example.gov.cn/notice/1",
                snippet="预算金额180万元，预计采购时间2026年7月",
                published_at="2026-05-20",
            )
        ][:limit]


class LocalFixtureFetchProvider(FetchProvider):
    async def fetch(self, url: str) -> RawPage:
        html = """
        <html><body>
        <h1>某县农产品区域公用品牌建设项目采购意向</h1>
        <p>采购单位：某县农业农村局</p>
        <p>预算金额：180万元</p>
        <p>预计采购时间：2026年7月</p>
        <p>采购需求：区域公用品牌建设、农产品品牌推广、包装设计、数字化展示。</p>
        </body></html>
        """
        return RawPage(url=url, status_code=200, content_type="text/html", text=html)
