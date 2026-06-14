"""Manual lead generation orchestration."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from fastapi import BackgroundTasks
from sqlmodel import Session, select

from leadradar.crawlers.registry import get_providers
from leadradar.llm.extraction import get_llm_provider
from leadradar.models import (
    ManualSubtask,
    ManualSubtaskStatus,
    ManualTask,
    ManualTaskStatus,
    Source,
)
from leadradar.db import get_engine
from leadradar.services.manual_generation_queries import expand_queries
from leadradar.services.manual_generation_runner import run_subtask

logger = logging.getLogger(__name__)

CONCURRENCY_LIMIT = 3


class ManualGenerationService:
    def __init__(self, session: Session):
        self._session = session

    def create_task(
        self,
        *,
        source_keys: list[str],
        keyword_mode: str,
        keyword_groups: list[str] | None = None,
        keywords: list[str] | None = None,
    ) -> ManualTask:
        """Create a ManualTask and its subtasks, but do not run them."""
        from leadradar.crawlers.registry import list_sources

        if not source_keys:
            raise ValueError("source_keys must not be empty")

        available = set(list_sources())
        invalid = set(source_keys) - available
        if invalid:
            raise ValueError(f"Unknown source keys: {sorted(invalid)}")

        sources = self._session.exec(
            select(Source).where(
                Source.source_key.isnot(None),  # type: ignore[union-attr]
                Source.source_key.in_(source_keys),  # type: ignore[union-attr]
                Source.enabled.is_(True),  # type: ignore[attr-defined]
            )
        ).all()
        source_by_key = {s.source_key: s for s in sources if s.source_key}
        missing = set(source_keys) - set(source_by_key.keys())
        if missing:
            raise ValueError(f"Source keys missing or disabled: {sorted(missing)}")

        queries = expand_queries(
            keyword_mode,
            keyword_groups=keyword_groups,
            keywords=keywords,
        )
        if not queries:
            raise ValueError("No keywords configured")

        task = ManualTask(
            keyword_mode=keyword_mode,
            status=ManualTaskStatus.PENDING,
            total_subtasks=len(sources) * len(queries),
        )
        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)

        for source in sources:
            for q in queries:
                subtask = ManualSubtask(
                    manual_task_id=task.id,
                    source_key=source.source_key,
                    source_id=source.id,
                    query=q["query"],
                    keyword_group=q["keyword_group"],
                    keyword=q["keyword"],
                )
                self._session.add(subtask)

        self._session.commit()
        return task

    async def run_task(self, task_id: UUID) -> None:
        """Run all subtasks for a manual task in the background."""
        task = self._session.get(ManualTask, task_id)
        if task is None:
            raise ValueError(f"ManualTask {task_id} not found")

        task.status = ManualTaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        self._session.add(task)
        self._session.commit()

        subtasks = self._session.exec(
            select(ManualSubtask).where(ManualSubtask.manual_task_id == task_id)
        ).all()

        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
        llm = get_llm_provider()

        async def _run_one(subtask: ManualSubtask) -> None:
            async with semaphore:
                with Session(get_engine()) as session:
                    st = session.get(ManualSubtask, subtask.id)
                    if st is None:
                        return
                    search, fetch = get_providers(st.source_key)
                    await run_subtask(
                        subtask=st,
                        session=session,
                        search=search,
                        fetch=fetch,
                        llm=llm,
                    )

        try:
            await asyncio.gather(*[_run_one(st) for st in subtasks])

            task = self._session.get(ManualTask, task_id)
            if task is None:
                raise ValueError(f"ManualTask {task_id} not found")
            self._session.expire_all()
            subtasks_after = self._session.exec(
                select(ManualSubtask).where(ManualSubtask.manual_task_id == task_id)
            ).all()

            task.completed_subtasks = sum(
                1 for s in subtasks_after if s.status != ManualSubtaskStatus.PENDING
            )
            task.created_leads_count = sum(s.created_leads_count for s in subtasks_after)
            task.skipped_duplicate_count = sum(
                s.skipped_duplicate_count for s in subtasks_after
            )

            failed_count = sum(1 for s in subtasks_after if s.status == ManualSubtaskStatus.FAILED)
            if failed_count == len(subtasks_after):
                task.status = ManualTaskStatus.FAILED
            elif failed_count:
                task.status = ManualTaskStatus.PARTIAL_FAILED
            else:
                task.status = ManualTaskStatus.COMPLETED

        except Exception as e:
            if task is None:
                raise ValueError(f"ManualTask {task_id} not found") from e
            logger.exception("Manual task %s failed", task_id)
            task.status = ManualTaskStatus.FAILED
            task.error_message = str(e)

        if task is None:
            raise ValueError(f"ManualTask {task_id} not found")
        task.finished_at = datetime.utcnow()
        self._session.add(task)
        self._session.commit()


async def schedule_manual_task(
    *,
    task_id: UUID,
    background_tasks: BackgroundTasks,
) -> None:
    """Schedule a manual task to run in the background with a fresh DB session."""
    async def _run_in_fresh_session() -> None:
        with Session(get_engine()) as session:
            service = ManualGenerationService(session)
            await service.run_task(task_id)

    background_tasks.add_task(_run_in_fresh_session)
