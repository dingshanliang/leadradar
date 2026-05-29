"""Crawl scheduler: keyword → search → deduplicate → store RawDocument."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlmodel import Session, select

from leadradar.crawlers.base import FetchProvider, SearchProvider
from leadradar.crawlers.parser import HtmlDocumentParser, content_hash
from leadradar.models import CrawlTask, CrawlTaskStatus, RawDocument
from leadradar.services.dedup import deduplicate_search_results

logger = logging.getLogger(__name__)


class CrawlerService:
    def __init__(
        self,
        session: Session,
        search: SearchProvider,
        fetch: FetchProvider,
        parser: HtmlDocumentParser | None = None,
    ):
        self._session = session
        self._search = search
        self._fetch = fetch
        self._parser = parser or HtmlDocumentParser()

    async def crawl(self, query: str, source_id: str | None = None) -> CrawlTask:
        task = CrawlTask(
            query=query,
            source_id=source_id,
            status=CrawlTaskStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)

        try:
            results = await self._search.search(query)
            results = deduplicate_search_results(results)
            new_count = 0
            dup_count = 0
            seen_hashes: set[str] = set()

            for result in results:
                if self._is_duplicate(result.url):
                    dup_count += 1
                    continue

                page = await self._fetch.fetch(result.url)
                text = self._parser.extract_text(page)
                hash_val = content_hash(text)

                if hash_val in seen_hashes or self._is_content_duplicate(hash_val):
                    dup_count += 1
                    continue

                seen_hashes.add(hash_val)
                doc = RawDocument(
                    source_id=source_id,
                    url=result.url,
                    title=result.title,
                    published_at=(
                        datetime.fromisoformat(result.published_at) if result.published_at else None
                    ),
                    raw_html=page.text,
                    extracted_text=text,
                    content_hash=hash_val,
                    document_type="html",
                )
                self._session.add(doc)
                new_count += 1

            self._session.commit()
            task.status = CrawlTaskStatus.COMPLETED
            task.error_message = f"new={new_count}, dup={dup_count}"

        except Exception as e:
            logger.exception("Crawl failed for query=%s", query)
            task.status = CrawlTaskStatus.FAILED
            task.error_message = str(e)

        task.finished_at = datetime.utcnow()
        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)
        return task

    def _is_duplicate(self, url: str) -> bool:
        existing = self._session.exec(select(RawDocument).where(RawDocument.url == url)).first()
        return existing is not None

    def _is_content_duplicate(self, hash_val: str) -> bool:
        existing = self._session.exec(
            select(RawDocument).where(RawDocument.content_hash == hash_val)
        ).first()
        return existing is not None
