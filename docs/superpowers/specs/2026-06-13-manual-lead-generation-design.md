# 手动生成线索功能设计

## 1. 背景与目标

LeadRadar 已具备自动采集流水线（crawl → extract → score → lead），但销售/运营人员希望按需、即时地触发一次线索生成：选择公开信息渠道，点击按钮，系统读取配置好的关键词，立即搜索、抽取、评分并生成线索。

本功能聚焦「手动触发、异步执行、进度可视、结果可追踪」。

## 2. 范围边界

**包含：**
- 选择多个公开信息渠道（Source）。
- 按「关键词组」或「关键词」两种模式展开查询。
- 创建异步任务，后台执行 crawl → extract → score。
- 父/子任务进度展示与结果摘要。
- 生成完成后跳转到线索池查看新线索。

**不包含：**
- 自动拨号、自动外呼。
- 抓取个人手机号或绕过反爬。
- 任务取消（MVP 阶段）。
- 复杂任务调度（如 Cron、队列优先级）。

## 3. 数据模型

### `ManualTask`（父任务）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 主键 |
| `keyword_mode` | enum | `by_group` / `by_keyword` |
| `status` | enum | `pending` / `running` / `completed` / `failed` / `partial_failed` |
| `total_subtasks` | int | 子任务总数 |
| `completed_subtasks` | int | 已完成数 |
| `created_leads_count` | int | 本次生成的新线索数 |
| `skipped_duplicate_count` | int | 重复跳过数 |
| `error_message` | str \| None | 整体失败原因 |
| `created_at` | datetime | 创建时间 |
| `started_at` | datetime \| None | 开始时间 |
| `finished_at` | datetime \| None | 结束时间 |

### `ManualSubtask`（子任务）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 主键 |
| `manual_task_id` | FK → manual_task.id | 所属父任务 |
| `source_id` | FK → source.id | 渠道 |
| `query` | str | 实际搜索语句 |
| `keyword_group` | str | 关键词组名 |
| `keyword` | str \| None | 当 `keyword_mode=by_keyword` 时使用 |
| `status` | enum | `pending` / `running` / `completed` / `failed` |
| `created_leads_count` | int | 本子任务生成的新线索数 |
| `skipped_duplicate_count` | int | 本子任务重复跳过数 |
| `error_message` | str \| None | 失败原因 |
| `started_at` | datetime \| None | 开始时间 |
| `finished_at` | datetime \| None | 结束时间 |

**设计理由**
- 父任务对应用户一次点击；子任务对应一个可独立执行的「渠道 × 查询」组合。
- 不改动现有 `CrawlTask`，避免污染自动采集语义。
- 保留 `keyword_group` / `keyword` 上下文，便于复盘与重试。

## 4. 后端架构

### 新增模块

| 文件 | 职责 |
|---|---|
| `src/leadradar/models.py` | 追加 `ManualTask`、`ManualSubtask` 模型 |
| `src/leadradar/services/manual_generation_service.py` | 创建任务、展开子任务、启动执行 |
| `src/leadradar/services/manual_generation_runner.py` | 子任务执行器（crawl → extract → score） |
| `src/leadradar/api/manual_generation_routes.py` | REST API |
| `src/leadradar/main.py` | 注册新路由 |

### API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/v1/manual-tasks` | 创建手动生成任务 |
| `GET` | `/api/v1/manual-tasks` | 查询任务列表（含子任务摘要） |
| `GET` | `/api/v1/manual-tasks/{id}` | 查询单个任务详情（含子任务列表） |
| `POST` | `/api/v1/manual-tasks/{id}/retry` | 重试失败的子任务（可选） |

### 创建任务请求体

```json
{
  "source_ids": ["uuid-1", "uuid-2"],
  "keyword_mode": "by_group"
}
```

### 后端行为

1. 校验 `source_ids` 非空且全部存在、启用。
2. 读取 `data/keywords.yml`，根据 `keyword_mode` 展开查询列表：
   - `by_group`：每个 `keyword_groups` 的 key 作为一个查询，查询内容可拼接组内关键词或仅用组名（实现时决定）。
   - `by_keyword`：每个组内每个关键词单独作为一个查询。
3. 创建 `ManualTask`（`pending`）。
4. 为每个 `source_id × query` 创建 `ManualSubtask`（`pending`）。
5. 立即返回任务摘要（含 `task_id`）。
6. 通过 `BackgroundTasks` 或等效机制启动 `ManualGenerationRunner`。

### 子任务执行流程

```
ManualSubtask.run()
  ├── search(query)  → 搜索结果列表
  ├── 对每个结果 fetch + parse
  ├── URL / content_hash 去重
  ├── 对新文档执行 document_to_signal()
  ├── 若 signal 有效则执行 signal_to_scored_lead()
  └── 更新 subtask: created_leads_count / skipped_duplicate_count / status
```

### 父任务状态汇总

- 全部子任务 `completed` → `completed`
- 部分 `failed` → `partial_failed`
- 全部 `failed` → `failed`

### 并发与限速

- 使用 `asyncio.Semaphore(3)` 控制同时运行的子任务数。
- 每个子任务内部已复用 `Source.rate_limit_per_minute`，形成双层保护。

### LLM Provider

- 复用现有 provider 选择逻辑：配置真实 provider 则使用真实 provider，否则 fallback 到 `MockLLMProvider`（开发环境）。

## 5. 前端设计

### 页面路由

新增 `/manual-tasks`，位于 `(with-sidebar)` 布局下。

### 页面结构

1. **标题区**
   - 标题：手动生成线索
   - 副标题：选择渠道和关键词模式，立即采集并生成线索

2. **生成表单区**
   - **渠道选择**：多选卡片/复选框，列出 `enabled=true` 的 `Source`。
   - **关键词模式**：
     - 按关键词组生成（默认）
     - 按关键词生成
   - **生成按钮**：至少选一个渠道才可用。

3. **任务列表区**
   - 展示最近 20 条手动任务。
   - 每行：创建时间、关键词模式、渠道数、状态、生成线索数、失败数。

4. **任务详情 / 进度面板**
   - 状态标签 + 进度条：`completed_subtasks / total_subtasks`
   - 子任务表格：渠道、查询、状态、生成数、跳过重、失败原因
   - 结果摘要：成功 N 条、跳过 M 条、失败 X 条
   - 「查看新线索」按钮：跳转线索池并带上时间范围筛选

### 实时刷新

- 任务列表和详情页使用 SWR `refreshInterval=3000` 轮询。
- 用户可离开页面，返回后自动刷新。

### 空状态

- 首次无任务时提示：「选择上方渠道并点击生成，开始第一次采集」。

### 入口

- 侧边栏「线索池」下方新增「手动生成」菜单项。
- 线索池空状态增加快捷入口：「还没有线索？去手动生成」。

## 6. 执行流程

```
用户提交表单
  │
  ▼
POST /api/v1/manual-tasks
  ├── 创建 ManualTask (pending)
  ├── 展开 source_ids × queries → ManualSubtask (pending)
  ├── 返回 { task_id }
  └── BackgroundTasks.add_task(run_manual_task, task_id)
  │
  ▼
前端跳转 /manual-tasks/{task_id}
  │
  ▼
后台执行器启动
  ├── 父任务 → running
  ├── Semaphore(3) 并发执行子任务
  │     ├── 子任务 → running
  │     ├── crawl / extract / score
  │     ├── 子任务 → completed / failed
  │     └── 更新父任务计数
  └── 全部完成后父任务 → completed / partial_failed / failed
  │
  ▼
前端轮询刷新，进度推进
```

## 7. 错误处理

| 场景 | 处理方式 |
|---|---|
| 单个渠道无法访问 | 该子任务 `failed`，其他子任务继续 |
| LLM 抽取失败 | 跳过该文档，子任务继续 |
| 全部子任务失败 | 父任务 `failed`，展示统一错误信息 |
| 关键词配置为空 | API 返回 422，提示先去配置页添加关键词 |
| 无可用渠道 | 禁用生成按钮并提示 |
| 服务重启导致任务挂起 | MVP 允许用户手动重试；后续可加心跳/超时检测 |

## 8. 重复与覆盖策略

- 子任务内复用 `CrawlerService` 的 URL 去重与 `content_hash` 去重。
- 已存在的文档不会被再次抽取，仅增加 `skipped_duplicate_count`。
- 不覆盖已有线索，避免破坏销售跟进状态。

## 9. 测试策略

### 后端测试

- `tests/test_manual_generation.py`
  - 1 渠道 + 1 关键词组 → 1 个子任务 → 成功生成线索
  - 2 渠道 + `by_keyword` → 子任务数 = 渠道数 × 关键词数
  - 重复 URL 被跳过，计数正确
  - 单个子任务失败不影响其他，父任务为 `partial_failed`
- 使用 `MockLLMProvider` + 内存 SQLite，不访问外网。
- 使用 `AsyncClient` 验证新 API 契约。

### 前端测试

- `web/src/app/(with-sidebar)/manual-tasks/__tests__/page.test.tsx`
  - 表单提交
  - 按钮禁用逻辑
  - 任务列表渲染
- 使用 MSW 或 mock SWR 模拟 API。

### 数据迁移

- 新增表通过 SQLModel `create_db_and_tables()` 自动创建。
- 当前项目未使用 Alembic，MVP 阶段不引入 migration。

## 10. 验收标准

- [ ] 用户可在「手动生成」页选择多个渠道和关键词模式，点击生成后创建任务。
- [ ] 任务页面实时展示父任务进度和子任务状态。
- [ ] 子任务失败不影响其他子任务，父任务正确标记为 `partial_failed`。
- [ ] 重复文档被跳过，不重复生成线索。
- [ ] 任务完成后显示结果摘要，并可跳转线索池查看新线索。
- [ ] 新增 API 与页面均有基础测试覆盖。
