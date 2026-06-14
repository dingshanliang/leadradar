"""Execute a single manual generation subtask."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlmodel import Session, select

from leadradar.crawlers.base import FetchProvider, SearchProvider
from leadradar.crawlers.parser import HtmlDocumentParser
from leadradar.llm.extraction import LLMProvider
from leadradar.models import ManualSubtask, ManualSubtaskStatus, RawDocument
from leadradar.services.crawler_service import CrawlerService
from leadradar.services.lead_service import document_to_signal, signal_to_scored_lead

logger = logging.getLogger(__name__)


async def run_subtask(
    *,
    subtask: ManualSubtask,
    session: Session,
    search: SearchProvider,
    fetch: FetchProvider,
    llm: LLMProvider,
    parser: HtmlDocumentParser | None = None,
) -> None:
    """Run one source × query combination and create leads."""
    subtask.status = ManualSubtaskStatus.RUNNING
    subtask.started_at = datetime.utcnow()
    session.add(subtask)
    session.commit()

    try:
        crawler = CrawlerService(session=session, search=search, fetch=fetch, parser=parser)
        await crawler.crawl(subtask.query, source_id=subtask.source_id)

        docs = session.exec(
            select(RawDocument).where(RawDocument.source_id == subtask.source_id)
        ).all()

        created = 0
        skipped = 0
        for doc in docs:
            try:
                extraction_run, signal = await document_to_signal(
                    document=doc,
                    llm=llm,
                    session=session,
                )
                if signal is None:
                    skipped += 1
                    continue

                signal_to_scored_lead(signal=signal, session=session)
                created += 1
            except Exception:
                logger.exception("Subtask %s failed for doc %s", subtask.id, doc.id)
                skipped += 1

        subtask.created_leads_count = created
        subtask.skipped_duplicate_count = skipped
        subtask.status = ManualSubtaskStatus.COMPLETED

    except Exception as e:
        logger.exception("Subtask %s failed", subtask.id)
        subtask.status = ManualSubtaskStatus.FAILED
        subtask.error_message = str(e)

    subtask.finished_at = datetime.utcnow()
    session.add(subtask)
    session.commit()
