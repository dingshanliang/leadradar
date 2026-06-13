from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from leadradar.api.schemas import ManualTaskCreate, ManualTaskOut, ManualSubtaskOut
from leadradar.db import get_session
from leadradar.models import ManualSubtask, ManualTask
from leadradar.services.manual_generation_service import (
    ManualGenerationService,
    schedule_manual_task,
)

router = APIRouter(prefix="/api/v1/manual-tasks")


@router.post("", status_code=201, response_model=ManualTaskOut)
async def create_manual_task(
    body: ManualTaskCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> ManualTaskOut:
    service = ManualGenerationService(session)
    try:
        task = service.create_task(
            source_keys=body.source_keys,
            keyword_mode=body.keyword_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    await schedule_manual_task(
        task_id=task.id,
        background_tasks=background_tasks,
    )

    return _task_to_out(task, subtasks=[])


@router.get("", response_model=list[ManualTaskOut])
def list_manual_tasks(
    limit: int = 20,
    session: Session = Depends(get_session),
) -> list[ManualTaskOut]:
    tasks = session.exec(
        select(ManualTask).order_by(ManualTask.created_at.desc()).limit(limit)
    ).all()
    return [_task_to_out(t, subtasks=_load_subtasks(t.id, session)) for t in tasks]


@router.get("/{task_id}", response_model=ManualTaskOut)
def get_manual_task(task_id: UUID, session: Session = Depends(get_session)) -> ManualTaskOut:
    task = session.get(ManualTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_out(task, subtasks=_load_subtasks(task_id, session))


def _load_subtasks(task_id: UUID, session: Session) -> list[ManualSubtask]:
    return session.exec(
        select(ManualSubtask).where(ManualSubtask.manual_task_id == task_id)
    ).all()


def _task_to_out(task: ManualTask, subtasks: list[ManualSubtask]) -> ManualTaskOut:
    return ManualTaskOut(
        id=task.id,
        keyword_mode=task.keyword_mode.value,
        status=task.status.value,
        total_subtasks=task.total_subtasks,
        completed_subtasks=task.completed_subtasks,
        created_leads_count=task.created_leads_count,
        skipped_duplicate_count=task.skipped_duplicate_count,
        error_message=task.error_message,
        created_at=task.created_at,
        started_at=task.started_at,
        finished_at=task.finished_at,
        subtasks=[
            ManualSubtaskOut(
                id=s.id,
                source_key=s.source_key,
                source_id=s.source_id,
                query=s.query,
                keyword_group=s.keyword_group,
                keyword=s.keyword,
                status=s.status.value,
                created_leads_count=s.created_leads_count,
                skipped_duplicate_count=s.skipped_duplicate_count,
                error_message=s.error_message,
                started_at=s.started_at,
                finished_at=s.finished_at,
            )
            for s in subtasks
        ],
    )
