# AGENTS.md

本文件为 AI 编码代理提供项目上下文。阅读本文前请假设你对该项目一无所知；所有信息均来自仓库实际内容，优先使用中文撰写（与项目注释和文档保持一致）。

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->

---

## 项目概述

**LeadRadar（数字包装商机雷达）** 是一个垂直 B2B 销售情报系统。它面向食品、农产品、区域品牌、包装设计/印刷、检测认证、电商代运营等场景，从公开政府采购/公共资源公告、认证名录、企业官网、新闻报道等来源中，发现“预算正在发生”的商机信号，生成可电话跟进的高质量线索列表。

当前仓库包含一套可运行的后端 API + 管理后台前端脚手架，以及完整的产品文档。核心能力包括：

- 关键词与数据源 YAML 配置
- 公告/网页采集任务
- 正文抽取与基于 content_hash 的去重
- LLM 结构化抽取与防编造校验
- 预算信号识别
- 五维规则评分（预算强度/场景匹配/时间窗口/可触达性/成交杠杆）
- 客户详情、证据链、电话开场白生成
- 外呼跟进状态管理
- Excel/CSV 导出

## 技术栈

### 后端

- **Python** 3.11+（Dockerfile 使用 3.14-slim，CI 矩阵 3.11/3.12）
- **FastAPI** + **uvicorn**（异步 ASGI）
- **Pydantic v2** + **pydantic-settings**（配置校验）
- **SQLModel** / **SQLAlchemy**（ORM）
- **PostgreSQL**（生产），默认 **SQLite**（开发）
- **psycopg**（PostgreSQL 驱动）
- **httpx**（异步 HTTP）
- **trafilatura** / **BeautifulSoup4**（正文抽取）
- **PyJWT** + **passlib[bcrypt]**（JWT 认证）
- **PyYAML**（配置读取）
- **openpyxl**（Excel 导出）

### 前端

- **Next.js** 16.2.6
- **React** 19.2.4
- **TypeScript** 5
- **Tailwind CSS** 4
- **SWR**（数据获取）
- **Recharts**（图表）
- **Zod**（运行时校验）
- **Vitest** + **@testing-library/react**（测试）
- **openapi-typescript**（从后端 OpenAPI 生成 `web/src/lib/api-types.ts`）

### 基础设施

- **Docker** + **docker-compose**（多服务编排：api、web、postgres、redis）
- **GitHub Actions** CI（`.github/workflows/ci.yml`）
- **beads (bd)** 本地问题追踪

## 目录结构

```
.
├── data/                       # YAML 业务配置
│   ├── keywords.yml            # 关键词分组
│   ├── scoring_rules.yml       # 评分规则（支持 API 在线编辑）
│   ├── sources.yml             # 数据源配置
│   └── sample_leads.csv        # 示例线索
├── docs/                       # 产品/技术文档（PRD、架构、API 规范等）
├── prompts/                    # 分阶段实现提示词
├── schemas/                    # JSON Schema
├── scripts/                    # 一次性脚本
├── sql/                        # 数据库 Schema 脚本
├── src/leadradar/              # Python 后端源码
│   ├── adapters/               # 导出适配器（CSV/XLSX）
│   ├── api/                    # FastAPI 路由与请求/响应模型
│   ├── crawlers/               # 各数据源采集器
│   ├── llm/                    # LLM 抽取 Provider
│   ├── repositories/           # 数据访问层
│   ├── services/               # 业务逻辑层
│   ├── auth.py                 # JWT 工具
│   ├── config.py               # pydantic-settings 配置
│   ├── db.py                   # SQLModel engine/session
│   ├── main.py                 # FastAPI 应用入口
│   ├── models.py               # SQLModel 数据模型
│   ├── schemas.py              # Pydantic 领域 schema
│   └── scoring.py              # 评分引擎入口
├── tests/                      # Python 测试
├── web/                        # Next.js 前端
│   ├── src/app/                # App Router 页面
│   ├── src/components/         # React 组件
│   ├── src/hooks/              # SWR hooks
│   ├── src/lib/                # API 客户端、类型、schema、工具
│   └── src/providers/          # 全局 Provider
├── pyproject.toml              # Python 项目配置
├── docker-compose.yml          # 本地编排
├── Dockerfile                  # 后端镜像
├── Makefile                    # 常用命令
└── AGENTS.md                   # 本文件
```

## 后端模块职责

| 文件/目录 | 职责 |
|---|---|
| `main.py` | FastAPI 应用实例、CORS、路由注册、`/health`、演示端点 |
| `config.py` | `Settings`（pydantic-settings），从 `.env` 加载，默认 SQLite |
| `db.py` | `create_engine`、`create_db_and_tables`、`get_session` 依赖 |
| `models.py` | SQLModel 表模型：`Source`、`CrawlTask`、`RawDocument`、`ExtractionRun`、`Signal`、`Organization`、`Lead`、`LeadScore`、`Contact`、`FollowUp`、`Blocklist`、`User` |
| `schemas.py` | Pydantic 领域模型：`ExtractionResult`、`LeadScoringInput/Result`、`ProductPackage`、`SignalType` |
| `api/schemas.py` | API 响应/请求模型（与前端类型对齐） |
| `api/routes.py` | `/api/v1/*` 业务路由：线索、配置、采集、统计、导出、跟进 |
| `api/auth_routes.py` | `/api/v1/auth/*` 注册/登录/当前用户 |
| `auth.py` | JWT 生成/解码、密码哈希、User 表模型 |
| `scoring.py` | `score_lead()`，加载 `data/scoring_rules.yml` 并返回五维评分 |
| `services/scoring_rule_set.py` | 评分规则集解析、维度上限、等级阈值 |
| `services/lead_service.py` | `document_to_signal()`、`signal_to_scored_lead()`、标志位映射、电话开场白 |
| `services/lead_query_service.py` | 线索列表、详情查询 |
| `services/lead_export_service.py` | Excel/CSV 导出行构造 |
| `services/lead_stats_service.py` | 仪表盘统计、周报 |
| `services/config_service.py` | 评分规则 CRUD |
| `services/crawler_service.py` | 爬虫任务管理 |
| `services/dedup.py` | 基于 content_hash 的去重 |
| `services/pipeline.py` | crawl → extract → signal → scored lead 端到端流水线 |
| `services/call_script.py` | 电话开场白生成 |
| `services/flag_derivation.py` | 从抽取结果推导评分标志位 |
| `llm/extraction.py` | `LLMProvider` ABC、`MockLLMProvider`、`OpenAICompatibleLLMProvider`、`validate_extraction()` 防编造校验 |
| `crawlers/base.py` | `SearchProvider`、`FetchProvider`、`DocumentParser` ABC + `SearchResult`、`RawPage` |
| `crawlers/registry.py` | 采集器注册表，按 source id 返回 provider 对 |
| `crawlers/*.py` | 各数据源实现：`ccgp`、`ggzy`、`spc`、`zycg`、`aqsc`、`greenfood`、`plap`、`provincial` 等 |
| `adapters/export_adapters.py` | `CsvExportAdapter`、`XlsxExportAdapter` |

## 前端模块职责

| 目录 | 职责 |
|---|---|
| `web/src/app/(with-sidebar)/` | 主布局（侧边栏）：线索池、仪表盘、配置、报告、线索详情 |
| `web/src/app/login/` | 登录页 |
| `web/src/app/workbench/[id]/` | 外呼工作台 |
| `web/src/components/config/` | 配置页 5 个 Tab（关键词、产品包、评分规则、话术、数据源） |
| `web/src/components/dashboard/` | 图表组件（metric-card、signal-type-chart、package-pie-chart、province-bar-chart） |
| `web/src/components/leads/` | 线索列表、筛选、导出、状态、等级徽章 |
| `web/src/components/lead-detail/` | 线索详情子组件 |
| `web/src/components/ui/` | 通用 UI 组件（button、card、skeleton、error-state、empty-state 等） |
| `web/src/hooks/` | `use-leads.ts`、`use-meta.ts`、`use-scoring-edit.ts` |
| `web/src/lib/api-client.ts` | 浏览器端 API，自动注入 JWT + 401 跳转 |
| `web/src/lib/server-api.ts` | Server Components 用 API 调用 |
| `web/src/lib/api-types.ts` | 由 `npm run generate-types` 从 OpenAPI 自动生成 |
| `web/src/lib/schemas.ts` | Zod 运行时校验 schema |

## 构建与运行

### 环境准备

```bash
cp .env.example .env
# 按需编辑 DATABASE_URL、LLM_*、JWT_SECRET_KEY 等
```

`.env.example` 中已包含：

- `DATABASE_URL`（默认 `postgresql+psycopg://...`，开发可直接改为 `sqlite:///./leadradar.db`）
- `REDIS_URL`
- `LLM_PROVIDER` / `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`
- 爬虫限速与合规开关

注意：`config.py` 当前未读取 `JWT_SECRET_KEY`，`auth.py` 使用环境变量 `JWT_SECRET_KEY`，默认值为开发密钥，生产必须显式设置。

### 后端

```bash
make setup          # 安装 Python 依赖 + Playwright chromium
make dev            # uvicorn 热重载启动，监听 0.0.0.0:8000
make test           # pytest -q
make lint           # ruff check + mypy
make format         # ruff format + ruff check --fix
```

### 前端

```bash
make web-setup      # cd web && npm install
make web-dev        # cd web && npm run dev，监听 3000
make web-build      # cd web && npm run build
```

前端额外命令：

```bash
cd web
npm run lint                 # eslint
npm run test                 # vitest run
npm run generate-types       # 从后端 /openapi.json 生成 api-types.ts（需后端运行）
npm run generate-types:live  # 同上
```

### Docker 全栈

```bash
docker-compose up --build
```

将启动：

- `api`：后端服务，端口 8000
- `web`：前端服务，端口 3000
- `postgres`：PostgreSQL 16，端口 5432
- `redis`：Redis 7，端口 6379

## 测试策略

### Python 测试

- 框架：**pytest** + **pytest-asyncio**
- 位置：`tests/`
- 覆盖范围：
  - 评分引擎：`test_scoring.py`、`test_scoring_rule_set.py`
  - 线索转换与服务：`test_lead_conversion.py`、`test_lead_services.py`、`test_lead_repository.py`
  - API 端点：`test_api.py`
  - 爬虫：`test_crawlers.py`、各数据源独立测试（`test_ccgp_crawler.py`、`test_ggzy_crawler.py` 等）
  - 去重：`test_dedup.py`
  - 流水线：`test_pipeline.py`
  - 配置/合规/抽取校验：`test_config.py`、`test_compliance.py`、`test_extraction_validation.py`
  - E2E：`test_e2e.py`
- 测试数据库：API 测试使用内存 SQLite + `StaticPool`，通过 `app.dependency_overrides` 替换 `get_session`
- 外部依赖：测试中不得访问真实外网；爬虫测试使用本地 fixtures/mocks；LLM 测试使用 `MockLLMProvider`

### 前端测试

- 框架：**Vitest** + **@testing-library/react** + **jsdom**
- 位置：`web/src/lib/__tests__/`、`web/src/providers/__tests__/`
- 运行：`npm run test`

### 运行单个测试示例

```bash
pytest tests/test_scoring.py -q
pytest tests/test_scoring.py::test_grade_thresholds -v
```

## 代码风格规范

### Python

- 使用 `from __future__ import annotations`（已在多数文件启用）
- 类型注解：核心逻辑必须有类型提示
- 行长度：**100**（`pyproject.toml` 中 `tool.ruff.line-length`）
- 格式化与检查：**ruff** + **mypy**
- 包布局：`src/leadradar/`，`pyproject.toml` 中 `package-dir = {"" = "src"}`
- 配置走环境变量或 YAML，不硬编码密钥
- 采集、抽取、评分、线索服务、API 分层清晰，避免跨层调用

### 前端

- TypeScript 严格模式
- **Next.js App Router**；展示型页面用 Server Component，交互型页面用 Client Component
- 页面只做数据获取与组合；业务逻辑抽到 hooks；UI 抽到独立组件
- SWR 调用必须解构 `error` + `mutate`，失败时展示 `ErrorState`
- 类型优先从 `api-types.ts` 获取；手写类型逐步迁移
- 修改 Next.js 代码前务必阅读 `web/node_modules/next/dist/docs/` 相关指南（该版本有破坏性变更）

## 安全与合规

这是项目不可逾越的底线：

- **不得抓取非公开个人信息**
- **不得绕过登录/验证码/反爬**
- **不得自动骚扰外呼**
- `ALLOW_PERSONAL_PHONE_COLLECTION=false`（默认）时，禁止收集个人手机号
- `ALLOW_AUTOMATED_OUTBOUND_CALLS=false`（默认）时，禁止自动外呼
- `validate_extraction()` 强制执行防编造校验：
  - 预算金额、机构名称等关键字段必须有 `evidence`
  - 证据中若出现疑似个人手机号（`1[3-9]\d{9}`），降低置信度并标记
  - 置信度设有下限 `_CONFIDENCE_FLOOR = 0.3`
- 所有 AI 生成结论必须保存 `evidence_text`、`source_url`、`confidence`
- 爬虫必须限速、尊重 robots，优先使用公开 API 或公开 HTML
- JWT 密钥生产环境必须显式设置，不可使用默认开发密钥

## 部署与 CI/CD

### GitHub Actions

`.github/workflows/ci.yml`：

- Python 3.11/3.12 矩阵运行 `make lint` + `make test`
- Node 20 运行前端 `npm run lint` + `npm run build`
- 触发分支：`main`、`dev` 的 push/pull_request

### 容器

- `Dockerfile`：Python 3.14-slim，安装依赖后拷贝 `src/`、`data/`、`tests/`，默认启动 uvicorn
- `web/Dockerfile`：Next.js 多阶段构建（需结合 `web/package.json` 推断）
- `docker-compose.yml`：本地一键启动全栈

## 常用端点速查

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/api/v1/demo-score` | 评分演示 |
| POST | `/api/v1/demo-call-script` | 话术演示 |
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| GET | `/api/v1/auth/me` | 当前用户 |
| GET | `/api/v1/stats` | 仪表盘统计 |
| GET | `/api/v1/weekly-report` | 周报 |
| GET | `/api/v1/meta` | 枚举元数据 |
| GET | `/api/v1/config` | 配置（关键词/评分维度/产品包） |
| GET/PUT | `/api/v1/config/scoring` | 评分规则读取/更新 |
| GET | `/api/v1/sources` | 数据源列表 |
| GET | `/api/v1/documents` | 原始文档列表 |
| GET | `/api/v1/leads` | 线索列表 |
| GET | `/api/v1/leads/export?format=csv|xlsx` | 导出 |
| GET | `/api/v1/leads/{id}` | 线索详情 |
| PATCH | `/api/v1/leads/{id}/status` | 更新线索状态 |
| POST/GET | `/api/v1/leads/{id}/follow-ups` | 创建/查询跟进记录 |
| GET | `/api/v1/follow-ups/due` | 到期跟进 |
| POST | `/api/v1/crawl/trigger` | 触发采集任务 |
| POST | `/api/v1/pipeline/run` | 触发端到端流水线 |

## 给 AI 代理的关键提示

1. **先读 `CLAUDE.md`**：Claude Code 优先读取根目录 `CLAUDE.md`，其中包含更具体的架构图、前端目录说明和约束。
2. **先查 `web/AGENTS.md`**：修改前端代码前，阅读 `web/AGENTS.md` 中关于 Next.js 版本破坏性变更的警告。
3. **不要假设实现存在**：当前是“开发交接包 + 轻量脚手架”，部分功能仅有接口或测试骨架，需按 `docs/` 和 `prompts/` 分阶段实现。
4. **保持模块化**：新增采集器请继承 `crawlers/base.py` 的 ABC 并在 `crawlers/registry.py` 注册；新增 LLM Provider 请继承 `llm/extraction.py` 的 `LLMProvider`。
5. **修改评分规则请同步测试**：`data/scoring_rules.yml` 支持 API 在线编辑，修改后确保 `tests/test_scoring.py` 与 `tests/test_scoring_rule_set.py` 仍通过。
6. **配置变更需更新 `.env.example`**：新增环境变量时同步更新示例文件与 `config.py` 的 `Settings` 类。
7. **工作结束前必须完成 Beads 流程**：创建 issue、运行质量门、更新状态、推送到远程。具体见本文件开头的 Beads 集成章节。
