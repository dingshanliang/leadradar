"""Full pipeline: keyword → crawl → extract → signal → scored lead."""

from __future__ import annotations

import logging

from sqlmodel import Session, select

from leadradar.crawlers.base import FetchProvider, SearchProvider
from leadradar.crawlers.parser import HtmlDocumentParser
from leadradar.llm.extraction import LLMProvider
from leadradar.models import CrawlTask, CrawlTaskStatus, Lead, LeadScore, RawDocument
from leadradar.services.crawler_service import CrawlerService
from leadradar.services.lead_service import document_to_signal, signal_to_scored_lead

logger = logging.getLogger(__name__)


class PipelineResult:
    def __init__(self):
        self.documents: list[RawDocument] = []
        self.leads: list[Lead] = []
        self.scores: list[LeadScore] = []
        self.skipped_irrelevant = 0
        self.errors: list[str] = []


async def run_pipeline(
    *,
    query: str,
    session: Session,
    search: SearchProvider,
    fetch: FetchProvider,
    llm: LLMProvider,
    parser: HtmlDocumentParser | None = None,
) -> PipelineResult:
    """Run full pipeline: crawl → extract → score for a keyword query."""
    result = PipelineResult()

    # Step 1: Crawl
    crawler = CrawlerService(session=session, search=search, fetch=fetch, parser=parser)
    crawl_task = await crawler.crawl(query)

    if crawl_task.status == CrawlTaskStatus.FAILED:
        result.errors.append(crawl_task.error_message or "crawl failed")
        return result

    # Step 2: Get all documents from this crawl
    docs = session.exec(
        select(RawDocument)
        .where(RawDocument.source_id == crawl_task.source_id)
        .order_by(RawDocument.fetched_at.desc())
    ).all()

    # If no source_id (direct query), get the latest documents
    if not docs:
        docs = session.exec(
            select(RawDocument).order_by(RawDocument.fetched_at.desc()).limit(20)
        ).all()

    # Step 3: Extract → Signal → Lead for each document
    for doc in docs:
        try:
            extraction_run, signal = await document_to_signal(
                document=doc, llm=llm, session=session,
            )

            if signal is None:
                result.skipped_irrelevant += 1
                result.documents.append(doc)
                continue

            org, lead, lead_score = signal_to_scored_lead(
                signal=signal, session=session,
            )
            result.documents.append(doc)
            result.leads.append(lead)
            result.scores.append(lead_score)

        except Exception as e:
            logger.exception("Pipeline failed for document %s", doc.id)
            result.errors.append(f"doc {doc.url}: {e}")
            result.documents.append(doc)

    return result
