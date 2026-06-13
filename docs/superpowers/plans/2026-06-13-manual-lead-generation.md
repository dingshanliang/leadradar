# 手动生成线索功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 LeadRadar 中新增「手动生成线索」功能：用户选择公开信息渠道和关键词模式后点击生成，系统异步采集、抽取、评分并生成线索，同时展示任务进度与结果摘要。

**Architecture:** 后端新增 `ManualTask`/`ManualSubtask` 模型与独立服务层，通过 FastAPI `BackgroundTasks` 异步执行「渠道 × 查询」子任务；前端新增 `/manual-tasks` 页面，使用 SWR 轮询实时刷新任务进度。

**Tech Stack:** Python 3.11+ / FastAPI / SQLModel / Pydantic v2 / pytest；Next.js 16 / React 19 / TypeScript / Tailwind CSS / SWR / Vitest。

---

## 文件结构

### 后端新增/修改

| 文件 | 变更 | 职责 |
|---|---|---|
| `src/leadradar/models.py` | 修改 | 追加 `source_key` 到 `Source`；追加 `ManualTask`、`ManualSubtask` 模型与枚举 |
| `src/leadradar/services/crawler_service.py` | 修改 | `source_id` 类型接受 `UUID \| str \| None` |
| `src/leadradar/services/manual_generation_service.py` | 新增 | 创建任务、展开子任务、启动后台执行 |
| `src/leadradar/services/manual_generation_runner.py` | 新增 | 单个子任务执行器（crawl → extract → score） |
| `src/leadradar/api/schemas.py` | 修改 | 追加手动任务相关请求/响应模型；`SourceOut` 暴露 `source_key` |
| `src/leadradar/api/manual_generation_routes.py` | 新增 | `/api/v1/manual-tasks` 路由 |
| `src/leadradar/main.py` | 修改 | 注册新路由 |
| `src/leadradar/llm/extraction.py` | 修改 | 新增 `get_llm_provider()` 工厂函数 |
| `tests/test_manual_generation.py` | 新增 | 后端 API 与业务逻辑测试 |

### 前端新增/修改

| 文件 | 变更 | 职责 |
|---|---|---|
| `web/src/lib/api-client.ts` | 修改 | 追加手动任务 API 调用函数 |
| `web/src/lib/types.ts` | 修改 | 追加手动任务类型别名（待生成） |
| `web/src/hooks/use-manual-tasks.ts` | 新增 | 手动任务列表与详情 SWR hooks |
| `web/src/app/(with-sidebar)/manual-tasks/page.tsx` | 新增 | 手动生成线索主页面 |
| `web/src/components/manual-tasks/task-form.tsx` | 新增 | 渠道选择 + 关键词模式 + 生成按钮 |
| `web/src/components/manual-tasks/task-list.tsx` | 新增 | 任务列表 |
| `web/src/components/manual-tasks/task-detail.tsx` | 新增 | 任务详情与进度面板 |
| `web/src/components/layout/sidebar.tsx` | 修改 | 增加「手动生成」菜单入口 |
| `web/src/app/(with-sidebar)/page.tsx` | 修改 | 空状态增加快捷入口 |
| `web/src/app/(with-sidebar)/manual-tasks/__tests__/page.test.tsx` | 新增 | 页面基础测试 |

---

## Task 1: 扩展 `Source` 并添加 `ManualTask` / `ManualSubtask` 数据模型

**Files:**
- Modify: `src/leadradar/models.py`

- [ ] **Step 1: 给 `Source` 增加 `source_key`**

在 `Source` 类中追加字段：

```python
source_key: Optional[str] = None
```

- [ ] **Step 2: 在 `LeadStatus` 之后追加枚举**

```python
class ManualTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_FAILED = "partial_failed"


class ManualSubtaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class KeywordMode(str, Enum):
    BY_GROUP = "by_group"
    BY_KEYWORD = "by_keyword"
```

- [ ] **Step 3: 在文件末尾追加模型类**

```python
class ManualTask(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    keyword_mode: KeywordMode = KeywordMode.BY_GROUP
    status: ManualTaskStatus = ManualTaskStatus.PENDING
    total_subtasks: int = 0
    completed_subtasks: int = 0
    created_leads_count: int = 0
    skipped_duplicate_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class ManualSubtask(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    manual_task_id: UUID = Field(foreign_key="manualtask.id")
    source_key: str
    source_id: UUID = Field(foreign_key="source.id")
    query: str
    keyword_group: str
    keyword: Optional[str] = None
    status: ManualSubtaskStatus = ManualSubtaskStatus.PENDING
    created_leads_count: int = 0
    skipped_duplicate_count: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
```

- [ ] **Step 4: 运行模型导入检查**

Run:
```bash
python -c "from leadradar.models import Source, ManualTask, ManualSubtask; print('ok')"
```

Expected: `ok`

- [ ] **Step 5: 提交**

```bash
git add src/leadradar/models.py
git commit -m "feat(models): add source_key to Source and ManualTask tables"
```

---

## Task 2: 添加 LLM Provider 工厂函数

**Files:**
- Modify: `src/leadradar/llm/extraction.py`
- Modify: `src/leadradar/config.py`（如需要显式导入）

- [ ] **Step 1: 在 `OpenAICompatibleLLMProvider` 之后追加工厂函数**

```python
def get_llm_provider() -> LLMProvider:
    """Return an LLM provider based on application settings."""
    from leadradar.config import get_settings

    settings = get_settings()
    if settings.llm_provider == "openai_compatible" and settings.llm_api_key:
        return OpenAICompatibleLLMProvider(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
        )
    return MockLLMProvider()
```

- [ ] **Step 2: 写基础测试**

Create: `tests/test_llm_provider.py`

```python
from leadradar.config import Settings, get_settings
from leadradar.llm.extraction import MockLLMProvider, OpenAICompatibleLLMProvider, get_llm_provider


def test_get_llm_provider_defaults_to_mock(monkeypatch):
    monkeypatch.setattr(
        "leadradar.config.get_settings",
        lambda: Settings(llm_provider="mock"),
    )
    provider = get_llm_provider()
    assert isinstance(provider, MockLLMProvider)


def test_get_llm_provider_uses_openai_when_configured(monkeypatch):
    monkeypatch.setattr(
        "leadradar.config.get_settings",
        lambda: Settings(
            llm_provider="openai_compatible",
            llm_api_key="sk-test",
            llm_base_url="https://api.example.com/v1",
            llm_model="gpt-4o-mini",
        ),
    )
    provider = get_llm_provider()
    assert isinstance(provider, OpenAICompatibleLLMProvider)
```

- [ ] **Step 3: 运行测试**

Run:
```bash
pytest tests/test_llm_provider.py -v
```

Expected: 2 passed

- [ ] **Step 4: 提交**

```bash
git add src/leadradar/llm/extraction.py tests/test_llm_provider.py
git commit -m "feat(llm): add get_llm_provider factory"
```

---

## Task 3: 实现关键词展开工具

**Files:**
- Create: `src/leadradar/services/manual_generation_queries.py`

- [ ] **Step 1: 创建查询展开模块**

```python
"""Expand configured keywords into concrete search queries."""

from __future__ import annotations

from pathlib import Path

import yaml


def _keywords_file() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / "keywords.yml"


def expand_queries(keyword_mode: str) -> list[dict[str, str | None]]:
    """Return a list of query descriptors.

    Each descriptor has keys:
      - keyword_group: str
      - keyword: str | None
      - query: str
    """
    with open(_keywords_file(), encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    groups = raw.get("keyword_groups", {})
    queries: list[dict[str, str | None]] = []

    for group_name, group_data in groups.items():
        keywords = group_data.get("keywords", [])
        if keyword_mode == "by_group":
            queries.append({
                "keyword_group": group_name,
                "keyword": None,
                "query": " ".join(keywords),
            })
        else:
            for kw in keywords:
                queries.append({
                    "keyword_group": group_name,
                    "keyword": kw,
                    "query": kw,
                })

    return queries
```

- [ ] **Step 2: 写测试**

Create: `tests/test_manual_generation_queries.py`

```python
from leadradar.services.manual_generation_queries import expand_queries


def test_expand_queries_by_group():
    queries = expand_queries("by_group")
    assert len(queries) >= 1
    assert queries[0]["keyword_group"] == "region_brand"
    assert queries[0]["keyword"] is None
    assert "区域公用品牌" in queries[0]["query"]


def test_expand_queries_by_keyword_has_more_items():
    group_queries = expand_queries("by_group")
    keyword_queries = expand_queries("by_keyword")
    assert len(keyword_queries) > len(group_queries)
    assert keyword_queries[0]["keyword"] is not None
```

- [ ] **Step 3: 运行测试**

Run:
```bash
pytest tests/test_manual_generation_queries.py -v
```

Expected: 2 passed

- [ ] **Step 4: 提交**

```bash
git add src/leadradar/services/manual_generation_queries.py tests/test_manual_generation_queries.py
git commit -m "feat(manual-gen): expand configured keywords into queries"
```

---

## Task 4: 更新 `CrawlerService` 类型并实现子任务执行器

**Files:**
- Modify: `src/leadradar/services/crawler_service.py`
- Create: `src/leadradar/services/manual_generation_runner.py`

- [ ] **Step 1: 修改 `CrawlerService.crawl` 的 `source_id` 类型**

在 `src/leadradar/services/crawler_service.py` 顶部导入 `UUID`：

```python
from uuid import UUID
```

将 `crawl` 方法签名从：

```python
async def crawl(self, query: str, source_id: str | None = None) -> CrawlTask:
```

改为：

```python
async def crawl(self, query: str, source_id: UUID | str | None = None) -> CrawlTask:
```

- [ ] **Step 2: 创建执行器**

```python
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
            select(RawDocument)
            .where(RawDocument.source_id == subtask.source_id)
            .order_by(RawDocument.fetched_at.desc())
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
            except Exception as e:
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
```

- [ ] **Step 3: 写失败测试确保导入正确**

Run:
```bash
python -c "from leadradar.services.manual_generation_runner import run_subtask; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: 提交**

```bash
git add src/leadradar/services/crawler_service.py src/leadradar/services/manual_generation_runner.py
git commit -m "feat(manual-gen): add subtask runner and allow UUID source_id in crawler"
```

---

## Task 5: 实现手动生成服务

**Files:**
- Create: `src/leadradar/services/manual_generation_service.py`

- [ ] **Step 1: 创建服务**

```python
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
from leadradar.services.manual_generation_queries import expand_queries
from leadradar.services.manual_generation_runner import run_subtask

logger = logging.getLogger(__name__)

CONCURRENCY_LIMIT = 3


class ManualGenerationService:
    def __init__(self, session: Session):
        self._session = session

    def create_task(self, *, source_keys: list[str], keyword_mode: str) -> ManualTask:
        """Create a ManualTask and its subtasks, but do not run them."""
        from leadradar.crawlers.registry import list_sources

        available = set(list_sources())
        invalid = set(source_keys) - available
        if invalid:
            raise ValueError(f"Unknown source keys: {sorted(invalid)}")

        sources = self._session.exec(
            select(Source).where(Source.source_key.in_(source_keys), Source.enabled == True)
        ).all()
        source_by_key = {s.source_key: s for s in sources if s.source_key}
        missing = set(source_keys) - set(source_by_key.keys())
        if missing:
            raise ValueError(f"Source keys missing or disabled: {sorted(missing)}")

        queries = expand_queries(keyword_mode)
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
                search, fetch = get_providers(subtask.source_key)
                await run_subtask(
                    subtask=subtask,
                    session=self._session,
                    search=search,
                    fetch=fetch,
                    llm=llm,
                )
                task.completed_subtasks += 1
                self._session.add(task)
                self._session.commit()

        try:
            await asyncio.gather(*[_run_one(st) for st in subtasks])

            failed = self._session.exec(
                select(ManualSubtask).where(
                    ManualSubtask.manual_task_id == task_id,
                    ManualSubtask.status == ManualSubtaskStatus.FAILED,
                )
            ).all()

            if len(failed) == len(subtasks):
                task.status = ManualTaskStatus.FAILED
            elif failed:
                task.status = ManualTaskStatus.PARTIAL_FAILED
            else:
                task.status = ManualTaskStatus.COMPLETED

        except Exception as e:
            logger.exception("Manual task %s failed", task_id)
            task.status = ManualTaskStatus.FAILED
            task.error_message = str(e)

        task.finished_at = datetime.utcnow()
        self._session.add(task)
        self._session.commit()


async def schedule_manual_task(
    *,
    task_id: UUID,
    background_tasks: BackgroundTasks,
) -> None:
    """Schedule a manual task to run in the background with a fresh DB session."""
    from leadradar.db import get_engine

    async def _run_in_fresh_session() -> None:
        with Session(get_engine()) as session:
            service = ManualGenerationService(session)
            await service.run_task(task_id)

    background_tasks.add_task(_run_in_fresh_session)
```

- [ ] **Step 2: 运行导入检查**

Run:
```bash
python -c "from leadradar.services.manual_generation_service import ManualGenerationService; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: 提交**

```bash
git add src/leadradar/services/manual_generation_service.py
git commit -m "feat(manual-gen): add task orchestration service"
```

---

## Task 6: 添加 API Schema

**Files:**
- Modify: `src/leadradar/api/schemas.py`

- [ ] **Step 1: 在 `SourceOut` 中暴露 `source_key`**

```python
class SourceOut(BaseModel):
    id: UUID
    name: str
    source_type: str
    source_key: str | None = None
    base_url: str | None = None
    priority: str | None = None
    enabled: bool = True
    rate_limit_per_minute: int = 20
    created_at: datetime
```

- [ ] **Step 2: 在文件末尾追加手动任务 schema**

```python
# ── Manual Generation ─────────────────────────────────────────────


class ManualTaskCreate(BaseModel):
    source_keys: list[str]
    keyword_mode: str = "by_group"


class ManualSubtaskOut(BaseModel):
    id: UUID
    source_key: str
    source_id: UUID
    query: str
    keyword_group: str
    keyword: str | None = None
    status: str
    created_leads_count: int
    skipped_duplicate_count: int
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ManualTaskOut(BaseModel):
    id: UUID
    keyword_mode: str
    status: str
    total_subtasks: int
    completed_subtasks: int
    created_leads_count: int
    skipped_duplicate_count: int
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    subtasks: list[ManualSubtaskOut] = []
```

- [ ] **Step 3: 运行导入检查**

Run:
```bash
python -c "from leadradar.api.schemas import SourceOut, ManualTaskCreate, ManualTaskOut, ManualSubtaskOut; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: 提交**

```bash
git add src/leadradar/api/schemas.py
git commit -m "feat(api): expose source_key and add manual task schemas"
```

---

## Task 7: 实现 API 路由

**Files:**
- Create: `src/leadradar/api/manual_generation_routes.py`
- Modify: `src/leadradar/main.py`

- [ ] **Step 1: 创建路由文件**

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from leadradar.api.schemas import ManualTaskCreate, ManualTaskOut, ManualSubtaskOut
from leadradar.db import get_session
from leadradar.models import ManualSubtask, ManualTask, Source
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
):
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
):
    tasks = session.exec(
        select(ManualTask).order_by(ManualTask.created_at.desc()).limit(limit)
    ).all()
    return [_task_to_out(t, subtasks=_load_subtasks(t.id, session)) for t in tasks]


@router.get("/{task_id}", response_model=ManualTaskOut)
def get_manual_task(task_id: UUID, session: Session = Depends(get_session)):
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
```

- [ ] **Step 2: 在 `main.py` 注册路由**

Add import:
```python
from leadradar.api.manual_generation_routes import router as manual_generation_router
```

Add after auth router:
```python
app.include_router(manual_generation_router)
```

- [ ] **Step 3: 运行后端启动检查**

Run:
```bash
python -c "from leadradar.main import app; print('routes:', [r.path for r in app.routes if 'manual' in r.path])"
```

Expected output includes `/api/v1/manual-tasks` and `/api/v1/manual-tasks/{task_id}`.

- [ ] **Step 4: 提交**

```bash
git add src/leadradar/api/manual_generation_routes.py src/leadradar/main.py
git commit -m "feat(api): add manual generation routes"
```

---

## Task 8: 后端集成测试

**Files:**
- Create: `tests/test_manual_generation.py`

- [ ] **Step 1: 创建测试文件**

```python
"""Tests for manual lead generation API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from leadradar.crawlers.base import FetchProvider, RawPage, SearchProvider, SearchResult
from leadradar.crawlers.registry import register
from leadradar.main import app
from leadradar.models import ManualTask, Source


class FakeSearch(SearchProvider):
    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        return []


class FakeFetch(FetchProvider):
    async def fetch(self, url: str) -> RawPage:
        return RawPage(url=url, status_code=200, content_type="text/html", text="<html></html>")


def _register_test_source():
    register("test_source", lambda: FakeSearch(), lambda: FakeFetch())


@pytest.fixture
def engine():
    _register_test_source()
    e = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(e)
    return e


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def sample_source(session):
    source = Source(
        name="测试采购网",
        source_type="government_procurement",
        source_key="test_source",
        enabled=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@pytest.fixture
def client(engine, monkeypatch):
    from leadradar.db import get_session
    from leadradar import api

    def _get_session():
        with Session(engine) as s:
            yield s

    # Prevent background tasks from running real crawls in API tests.
    monkeypatch.setattr(
        api.manual_generation_routes,
        "schedule_manual_task",
        lambda *, task_id, background_tasks: None,
    )

    app.dependency_overrides[get_session] = _get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_manual_task(client, sample_source):
    response = client.post(
        "/api/v1/manual-tasks",
        json={
            "source_keys": ["test_source"],
            "keyword_mode": "by_group",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["total_subtasks"] > 0


def test_create_manual_task_requires_source_keys(client):
    response = client.post(
        "/api/v1/manual-tasks",
        json={"source_keys": [], "keyword_mode": "by_group"},
    )
    assert response.status_code == 422


def test_create_manual_task_rejects_unknown_source_key(client):
    response = client.post(
        "/api/v1/manual-tasks",
        json={"source_keys": ["not_real"], "keyword_mode": "by_group"},
    )
    assert response.status_code == 422


def test_list_manual_tasks(client, sample_source):
    client.post(
        "/api/v1/manual-tasks",
        json={
            "source_keys": ["test_source"],
            "keyword_mode": "by_group",
        },
    )
    response = client.get("/api/v1/manual-tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_manual_task_detail(client, sample_source):
    create_resp = client.post(
        "/api/v1/manual-tasks",
        json={
            "source_keys": ["test_source"],
            "keyword_mode": "by_group",
        },
    )
    task_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/manual-tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert len(data["subtasks"]) > 0
```

- [ ] **Step 2: 运行测试**

Run:
```bash
pytest tests/test_manual_generation.py -v
```

Expected: 5 passed

- [ ] **Step 3: 提交**

```bash
git add tests/test_manual_generation.py
git commit -m "test(manual-gen): add API tests"
```

---

## Task 9: 生成前端类型

**Files:**
- Modify: `web/src/lib/types.ts`

- [ ] **Step 1: 确保后端可访问并生成类型**

Run:
```bash
make dev
```

In another terminal:
```bash
cd web && npm run generate-types:live
```

Expected: `web/src/lib/api-types.ts` 更新，包含 `ManualTaskCreate`, `ManualTaskOut`, `ManualSubtaskOut`。

- [ ] **Step 2: 在 `types.ts` 追加别名**

```typescript
export type ManualTaskCreate = components["schemas"]["ManualTaskCreate"];
export type ManualTaskOut = components["schemas"]["ManualTaskOut"];
export type ManualSubtaskOut = components["schemas"]["ManualSubtaskOut"];
```

- [ ] **Step 3: 提交**

```bash
git add web/src/lib/api-types.ts web/src/lib/types.ts
git commit -m "chore(web): regenerate API types for manual tasks"
```

---

## Task 10: 前端 API 客户端

**Files:**
- Modify: `web/src/lib/api-client.ts`

- [ ] **Step 1: 追加 API 函数**

```typescript
import type {
  // ... existing imports ...
  ManualTaskCreate,
  ManualTaskOut,
} from "./types";

// ── Manual Tasks ────────────────────────────────────────────────

export async function createManualTask(
  payload: ManualTaskCreate
): Promise<ManualTaskOut> {
  return apiFetch("/api/v1/manual-tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listManualTasks(): Promise<ManualTaskOut[]> {
  return apiFetch("/api/v1/manual-tasks");
}

export async function getManualTask(taskId: string): Promise<ManualTaskOut> {
  return apiFetch(`/api/v1/manual-tasks/${taskId}`);
}
```

- [ ] **Step 2: 运行类型检查**

Run:
```bash
cd web && npm run typecheck
```

Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add web/src/lib/api-client.ts
git commit -m "feat(web): add manual task API client"
```

---

## Task 11: 前端 SWR Hooks

**Files:**
- Create: `web/src/hooks/use-manual-tasks.ts`

- [ ] **Step 1: 创建 hooks**

```typescript
"use client";

import useSWR from "swr";
import { getManualTask, listManualTasks } from "@/lib/api-client";
import type { ManualTaskOut } from "@/lib/types";

export function useManualTasks() {
  const { data, error, isLoading, mutate } = useSWR<ManualTaskOut[]>(
    "manual-tasks",
    listManualTasks,
    { refreshInterval: 3000, revalidateOnFocus: true }
  );
  return { tasks: data ?? [], error, isLoading, mutate };
}

export function useManualTask(taskId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<ManualTaskOut>(
    taskId ? `manual-task:${taskId}` : null,
    () => getManualTask(taskId!),
    { refreshInterval: 3000, revalidateOnFocus: true }
  );
  return { task: data, error, isLoading, mutate };
}
```

- [ ] **Step 2: 运行类型检查**

Run:
```bash
cd web && npm run typecheck
```

Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add web/src/hooks/use-manual-tasks.ts
git commit -m "feat(web): add manual tasks SWR hooks"
```

---

## Task 12: 创建任务表单组件

**Files:**
- Create: `web/src/components/manual-tasks/task-form.tsx`

- [ ] **Step 1: 创建组件**

```tsx
"use client";

import { useState } from "react";
import { createManualTask } from "@/lib/api-client";
import type { Source } from "@/lib/types";

interface TaskFormProps {
  sources: Source[];
  onCreated: (taskId: string) => void;
}

export function TaskForm({ sources, onCreated }: TaskFormProps) {
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [keywordMode, setKeywordMode] = useState<"by_group" | "by_keyword">("by_group");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toggleSource = (id: string) => {
    setSelectedSources((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const handleSubmit = async () => {
    if (selectedSources.length === 0) return;
    setIsSubmitting(true);
    try {
      const task = await createManualTask({
        source_keys: selectedSources,
        keyword_mode: keywordMode,
      });
      onCreated(task.id);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4 p-4 bg-bg-elevated rounded-xl border border-border">
      <div>
        <h3 className="text-sm font-medium mb-2">选择信息渠道</h3>
        <div className="flex flex-wrap gap-2">
          {sources.map((source) => (
            <label
              key={source.source_key ?? source.id}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer text-sm transition-colors ${
                selectedSources.includes(source.source_key ?? "")
                  ? "border-primary bg-primary/[0.06] text-primary"
                  : "border-border hover:bg-bg-muted"
              }`}
            >
              <input
                type="checkbox"
                className="sr-only"
                checked={selectedSources.includes(source.source_key ?? "")}
                onChange={() => toggleSource(source.source_key ?? "")}
              />
              {source.name}
            </label>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium mb-2">关键词模式</h3>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              value="by_group"
              checked={keywordMode === "by_group"}
              onChange={() => setKeywordMode("by_group")}
            />
            按关键词组生成
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              value="by_keyword"
              checked={keywordMode === "by_keyword"}
              onChange={() => setKeywordMode("by_keyword")}
            />
            按关键词生成
          </label>
        </div>
      </div>

      <button
        onClick={handleSubmit}
        disabled={selectedSources.length === 0 || isSubmitting}
        className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
      >
        {isSubmitting ? "提交中..." : "生成线索"}
      </button>
    </div>
  );
}
```

- [ ] **Step 2: 运行类型检查**

Run:
```bash
cd web && npm run typecheck
```

Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add web/src/components/manual-tasks/task-form.tsx
git commit -m "feat(web): add manual task form component"
```

---

## Task 13: 创建任务列表组件

**Files:**
- Create: `web/src/components/manual-tasks/task-list.tsx`

- [ ] **Step 1: 创建组件**

```tsx
"use client";

import type { ManualTaskOut } from "@/lib/types";

interface TaskListProps {
  tasks: ManualTaskOut[];
  selectedTaskId: string | null;
  onSelect: (taskId: string) => void;
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: "待执行",
    running: "执行中",
    completed: "已完成",
    failed: "失败",
    partial_failed: "部分失败",
  };
  return map[status] ?? status;
}

export function TaskList({ tasks, selectedTaskId, onSelect }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <p className="text-sm text-muted py-4">暂无手动生成任务</p>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <button
          key={task.id}
          onClick={() => onSelect(task.id)}
          className={`w-full text-left p-3 rounded-lg border transition-colors ${
            selectedTaskId === task.id
              ? "border-primary bg-primary/[0.06]"
              : "border-border hover:bg-bg-muted"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">
              {new Date(task.created_at).toLocaleString("zh-CN")}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-bg-muted">
              {statusLabel(task.status)}
            </span>
          </div>
          <div className="mt-1 text-xs text-muted">
            渠道 {task.total_subtasks} 个查询 · 生成 {task.created_leads_count} 条 · 跳过 {task.skipped_duplicate_count} 条
          </div>
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: 运行类型检查**

Run:
```bash
cd web && npm run typecheck
```

Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add web/src/components/manual-tasks/task-list.tsx
git commit -m "feat(web): add manual task list component"
```

---

## Task 14: 创建任务详情/进度组件

**Files:**
- Create: `web/src/components/manual-tasks/task-detail.tsx`

- [ ] **Step 1: 创建组件**

```tsx
"use client";

import Link from "next/link";
import type { ManualTaskOut } from "@/lib/types";

interface TaskDetailProps {
  task: ManualTaskOut;
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: "待执行",
    running: "执行中",
    completed: "已完成",
    failed: "失败",
    partial_failed: "部分失败",
  };
  return map[status] ?? status;
}

function subStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: "待执行",
    running: "执行中",
    completed: "完成",
    failed: "失败",
  };
  return map[status] ?? status;
}

export function TaskDetail({ task }: TaskDetailProps) {
  const progress =
    task.total_subtasks > 0
      ? Math.round((task.completed_subtasks / task.total_subtasks) * 100)
      : 0;

  return (
    <div className="space-y-4 p-4 bg-bg-elevated rounded-xl border border-border">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">任务详情</h3>
        <span className="text-xs px-2 py-0.5 rounded-full bg-bg-muted">
          {statusLabel(task.status)}
        </span>
      </div>

      <div>
        <div className="flex justify-between text-xs text-muted mb-1">
          <span>进度</span>
          <span>{task.completed_subtasks} / {task.total_subtasks}</span>
        </div>
        <div className="h-2 bg-bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="p-2 bg-bg-muted rounded-lg">
          <div className="text-lg font-semibold">{task.created_leads_count}</div>
          <div className="text-xs text-muted">新线索</div>
        </div>
        <div className="p-2 bg-bg-muted rounded-lg">
          <div className="text-lg font-semibold">{task.skipped_duplicate_count}</div>
          <div className="text-xs text-muted">跳过重复</div>
        </div>
        <div className="p-2 bg-bg-muted rounded-lg">
          <div className="text-lg font-semibold">
            {task.subtasks.filter((s) => s.status === "failed").length}
          </div>
          <div className="text-xs text-muted">失败</div>
        </div>
      </div>

      {task.error_message && (
        <p className="text-sm text-destructive">{task.error_message}</p>
      )}

      <div className="border-t border-border pt-3">
        <h4 className="text-sm font-medium mb-2">子任务</h4>
        <div className="space-y-1 max-h-64 overflow-auto">
          {task.subtasks.map((sub) => (
            <div
              key={sub.id}
              className="flex items-center justify-between text-sm py-1.5 px-2 rounded bg-bg-muted"
            >
              <span className="truncate flex-1 mr-2" title={sub.query}>
                {sub.query}
              </span>
              <span className="text-xs text-muted whitespace-nowrap">
                {subStatusLabel(sub.status)} · {sub.created_leads_count} 条
              </span>
            </div>
          ))}
        </div>
      </div>

      {task.status === "completed" || task.status === "partial_failed" ? (
        <Link
          href="/"
          className="inline-block text-sm text-primary hover:underline"
        >
          查看新线索 →
        </Link>
      ) : null}
    </div>
  );
}
```

- [ ] **Step 2: 运行类型检查**

Run:
```bash
cd web && npm run typecheck
```

Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add web/src/components/manual-tasks/task-detail.tsx
git commit -m "feat(web): add manual task detail component"
```

---

## Task 15: 创建手动生成页面

**Files:**
- Create: `web/src/app/(with-sidebar)/manual-tasks/page.tsx`

- [ ] **Step 1: 创建页面**

```tsx
"use client";

import { useState } from "react";
import { TaskForm } from "@/components/manual-tasks/task-form";
import { TaskList } from "@/components/manual-tasks/task-list";
import { TaskDetail } from "@/components/manual-tasks/task-detail";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useManualTask, useManualTasks } from "@/hooks/use-manual-tasks";
import { useSources } from "@/hooks/use-sources";

export default function ManualTasksPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const { tasks, error: tasksError, isLoading: tasksLoading, mutate } = useManualTasks();
  const { task: selectedTask, error: detailError } = useManualTask(selectedTaskId);
  const { sources, isLoading: sourcesLoading } = useSources();

  const handleCreated = (taskId: string) => {
    setSelectedTaskId(taskId);
    mutate();
  };

  return (
    <div className="px-8 py-6">
      <div className="mb-6">
        <h1 className="font-heading text-2xl font-bold text-primary">手动生成线索</h1>
        <p className="text-sm text-muted mt-1">
          选择公开信息渠道，立即采集并生成线索
        </p>
      </div>

      {sourcesLoading ? (
        <Skeleton className="h-40 w-full" />
      ) : sources.length === 0 ? (
        <EmptyState title="无可用渠道" description="请先在配置页添加数据源" />
      ) : (
        <TaskForm sources={sources} onCreated={handleCreated} />
      )}

      <div className="grid grid-cols-12 gap-6 mt-6">
        <div className="col-span-5">
          <h2 className="text-sm font-medium mb-3">任务列表</h2>
          {tasksLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : tasksError ? (
            <ErrorState onRetry={() => mutate()} />
          ) : (
            <TaskList
              tasks={tasks}
              selectedTaskId={selectedTaskId}
              onSelect={setSelectedTaskId}
            />
          )}
        </div>

        <div className="col-span-7">
          <h2 className="text-sm font-medium mb-3">任务详情</h2>
          {!selectedTaskId ? (
            <EmptyState title="未选择任务" description="从左侧选择一项任务查看进度" />
          ) : detailError ? (
            <ErrorState onRetry={() => {}} />
          ) : !selectedTask ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <TaskDetail task={selectedTask} />
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 创建 `useSources` hook**

Create: `web/src/hooks/use-sources.ts`

```typescript
"use client";

import useSWR from "swr";
import { listSources } from "@/lib/api-client";
import type { Source } from "@/lib/types";

export function useSources() {
  const { data, error, isLoading } = useSWR<Source[]>("sources", listSources, {
    revalidateOnFocus: false,
  });
  return { sources: data ?? [], error, isLoading };
}
```

- [ ] **Step 3: 运行类型检查**

Run:
```bash
cd web && npm run typecheck
```

Expected: 0 errors

- [ ] **Step 4: 提交**

```bash
git add web/src/hooks/use-sources.ts web/src/app/(with-sidebar)/manual-tasks/page.tsx
git commit -m "feat(web): add manual tasks page"
```

---

## Task 16: 添加侧边栏与线索池入口

**Files:**
- Modify: `web/src/components/layout/sidebar.tsx`
- Modify: `web/src/app/(with-sidebar)/page.tsx`

- [ ] **Step 1: 在侧边栏 `NAV_ITEMS` 中插入新项**

Insert after the dashboard item (index 1):

```typescript
  {
    href: "/manual-tasks" as const,
    label: "手动生成",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
```

- [ ] **Step 2: 在线索池空状态添加快捷入口**

In `web/src/app/(with-sidebar)/page.tsx`, replace the empty state block:

```tsx
import Link from "next/link";

// ... inside the empty-state branch ...

<EmptyState
  title="暂无线索"
  description="开始采集数据后，线索会出现在这里"
/>
<Link
  href="/manual-tasks"
  className="inline-block mt-4 text-sm text-primary hover:underline"
>
  去手动生成线索 →
</Link>
```

- [ ] **Step 3: 运行类型检查**

Run:
```bash
cd web && npm run typecheck
```

Expected: 0 errors

- [ ] **Step 4: 提交**

```bash
git add web/src/components/layout/sidebar.tsx web/src/app/(with-sidebar)/page.tsx
git commit -m "feat(web): add manual generation navigation entries"
```

---

## Task 17: 前端页面测试

**Files:**
- Create: `web/src/app/(with-sidebar)/manual-tasks/__tests__/page.test.tsx`

- [ ] **Step 1: 创建测试文件**

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ManualTasksPage from "../page";

vi.mock("@/hooks/use-manual-tasks", () => ({
  useManualTasks: () => ({
    tasks: [],
    error: null,
    isLoading: false,
    mutate: vi.fn(),
  }),
  useManualTask: () => ({
    task: null,
    error: null,
    isLoading: false,
    mutate: vi.fn(),
  }),
}));

vi.mock("@/hooks/use-sources", () => ({
  useSources: () => ({
    sources: [
      { id: "s1", source_key: "test_source", name: "测试源 A", source_type: "government_procurement", enabled: true, rate_limit_per_minute: 20 },
    ],
    error: null,
    isLoading: false,
  }),
}));

describe("ManualTasksPage", () => {
  it("renders form and empty task list", () => {
    render(<ManualTasksPage />);
    expect(screen.getByText("手动生成线索")).toBeInTheDocument();
    expect(screen.getByText("生成线索")).toBeInTheDocument();
    expect(screen.getByText("测试源 A")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行测试**

Run:
```bash
cd web && npm run test -- src/app/(with-sidebar)/manual-tasks/__tests__/page.test.tsx
```

Expected: 1 passed

- [ ] **Step 3: 提交**

```bash
git add web/src/app/(with-sidebar)/manual-tasks/__tests__/page.test.tsx
git commit -m "test(web): add manual tasks page test"
```

---

## Task 18: 质量门

**Files:**
- All modified files

- [ ] **Step 1: 运行后端测试**

Run:
```bash
make test
```

Expected: all tests pass

- [ ] **Step 2: 运行后端 lint**

Run:
```bash
make lint
```

Expected: no errors

- [ ] **Step 3: 运行前端 lint、类型检查、测试**

Run:
```bash
cd web && npm run lint && npm run typecheck && npm run test
```

Expected: all pass

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: quality gates pass for manual lead generation"
```

---

## 自检

### 1. Spec 覆盖检查

| Spec 要求 | 对应任务 |
|---|---|
| 新增 `ManualTask`/`ManualSubtask` 模型 | Task 1 |
| 读取关键词配置并展开查询 | Task 3 |
| 异步后台执行 | Task 4, 5 |
| 父/子任务进度 | Task 5, 14 |
| API 端点 | Task 6, 7 |
| 前端页面、表单、列表、详情 | Task 12, 13, 14, 15 |
| 侧边栏与线索池入口 | Task 16 |
| 错误处理（子任务独立失败） | Task 4, 5 |
| 重复跳过 | Task 4（复用 CrawlerService 去重） |
| 测试覆盖 | Task 2, 3, 8, 17 |

### 2. Placeholder 扫描

- 无 "TBD"/"TODO"/"implement later"。
- 每个任务包含具体代码、命令、期望输出。
- 每个文件路径明确。

### 3. 类型一致性检查

- 后端：`keyword_mode` 在 enum、模型、schema、service 中均使用 `str` 或 `KeywordMode`，输出为 `.value`。
- 前端：`ManualTaskCreate` / `ManualTaskOut` / `ManualSubtaskOut` 从生成的 OpenAPI 类型获取，与后端 schema 一致。
- 任务状态字符串前后端对齐：pending/running/completed/failed/partial_failed。

---

## 执行交接

**Plan complete and saved to `docs/superpowers/plans/2026-06-13-manual-lead-generation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
