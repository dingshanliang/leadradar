# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

LeadRadar 是一个垂直 B2B 销售情报系统，从公开政府采购/公共资源公告中发现食品、农产品、包装、检测相关的"预算正在发生"商机，生成可电话跟进的高质量线索列表。

**MVP 边界**：只做公开信息采集、LLM 结构化抽取、线索评分和列表管理。不做自动拨号、自动群发、绕过验证码/登录、个人手机号抓取。

## 常用命令

```bash
# 后端
make setup          # 安装 Python 依赖 + Playwright chromium
make dev            # uvicorn 启动后端 (port 8000)
make test           # pytest 运行全部测试
make lint           # ruff + mypy 检查
make format         # ruff 自动格式化

# 前端 (在 web/ 目录)
make web-setup      # npm install
make web-dev        # next dev (port 3000)
make web-build      # next build
npm run lint        # eslint
npm run test        # vitest
npm run generate-types  # 从 OpenAPI spec 生成 api-types.ts（需后端运行）

# 运行单个测试
pytest tests/test_scoring.py -q
pytest tests/test_scoring.py::test_grade_thresholds -v
```

## 架构概览

```
用户查询 → CrawlerService → SearchProvider (搜索) → FetchProvider (抓取)
         → HtmlDocumentParser (正文提取) → RawDocument (存库)
         → LLMProvider.extract() (结构化抽取) → ExtractionResult
         → validate_extraction() (防编造校验) → Signal (存库)
         → score_lead() (评分) → Lead + LeadScore (存库)
```

### 后端 (`src/leadradar/`)

| 模块 | 职责 |
|------|------|
| `models.py` | SQLModel 数据模型：Source, RawDocument, ExtractionRun, Signal, Organization, Lead, LeadScore, Contact, FollowUp, Blocklist |
| `schemas.py` | Pydantic schema：ExtractionResult, LeadScoringInput/Result, 类型约束（ProductPackage, SignalType） |
| `scoring.py` | 规则评分引擎，加载 `data/scoring_rules.yml`，五维评分（预算强度/场景匹配/时间窗口/可触达性/成交杠杆） |
| `config.py` | pydantic-settings 配置，从 `.env` 读取，默认 SQLite |
| `db.py` | SQLModel engine/session 工厂 |
| `llm/extraction.py` | LLM 抽取层：`LLMProvider` ABC + `MockLLMProvider` + `OpenAICompatibleLLMProvider` + `validate_extraction()` 防编造校验 |
| `crawlers/base.py` | 采集器 ABC：`SearchProvider`, `FetchProvider`, `DocumentParser` |
| `crawlers/registry.py` | 采集器注册表，通过 source name 获取 provider 对 |
| `crawlers/` | 各数据源实现：ccgp, ggzy, spc, zycg, aqsc, greenfood, plap, provincial (多省) |
| `services/pipeline.py` | 端到端流水线：crawl → extract → signal → scored lead |
| `services/lead_service.py` | 核心业务逻辑：`document_to_signal()`, `signal_to_scored_lead()`, 标志位映射 |
| `services/crawler_service.py` | 爬虫任务管理 |
| `services/dedup.py` | 内容去重（基于 content_hash） |
| `services/config_service.py` | 评分规则 CRUD（支持 UI 编辑） |
| `services/call_script.py` | 电话话术生成 |
| `api/routes.py` | FastAPI REST 端点 (prefix `/api/v1`) |
| `api/schemas.py` | API 响应模型 |
| `api/auth_routes.py` | JWT 认证路由 |
| `auth.py` | 认证工具函数 |

### 前端 (`web/`)

Next.js 16 + React 19 + Tailwind CSS 4 + SWR + Recharts + openapi-typescript。

**重要**：此 Next.js 版本有 breaking changes，修改前端前必须先阅读 `web/node_modules/next/dist/docs/` 中的指南。

#### 目录结构

```
web/src/
├── app/
│   ├── error.tsx, global-error.tsx   # 全局错误边界（'use client'）
│   ├── (with-sidebar)/               # 主布局（侧边栏）
│   │   ├── page.tsx                  # 线索池（Client Component + SWR）
│   │   ├── dashboard/                # Server Component（force-dynamic）
│   │   │   ├── page.tsx              # async 数据获取 + Suspense
│   │   │   ├── loading.tsx           # 骨架屏
│   │   │   └── error.tsx             # 路由级错误边界
│   │   ├── config/page.tsx           # 配置页（评分规则可在线编辑，其余 Tab 只读展示）
│   │   ├── report/page.tsx
│   │   └── leads/[id]/page.tsx
│   ├── login/page.tsx
│   └── workbench/[id]/page.tsx
├── components/
│   ├── config/          # 5 个独立 Tab 组件（各自管理 SWR）
│   ├── dashboard/       # 图表组件（metric-card, signal-type-chart, package-pie-chart, province-bar-chart）
│   ├── layout/          # 侧边栏布局
│   ├── lead-detail/     # 线索详情子组件
│   ├── leads/           # 线索列表
│   ├── ui/              # 通用 UI（button, card, skeleton, error-state, empty-state）
│   └── workbench/       # 工作台
├── hooks/
│   ├── use-leads.ts     # 线索列表 SWR
│   ├── use-meta.ts      # 枚举元数据 SWR
│   └── use-scoring-edit.ts  # 评分规则编辑（状态+校验+保存）
└── lib/
    ├── api-client.ts    # 客户端 API（自动注入 JWT + 401 跳转）
    ├── server-api.ts    # 服务端 API（Server Components 用）
    ├── api-types.ts     # OpenAPI 自动生成类型（npm run generate-types）
    ├── types.ts         # 手写类型（逐步迁移到 api-types.ts）
    ├── schemas.ts       # zod 运行时校验 schema
    ├── constants.ts
    └── utils.ts
```

#### 前端开发规范

- **错误处理**：所有 SWR 调用必须解构 `error` + `mutate`，失败时展示 `ErrorState` 组件
- **Server Components**：仅展示型页面用 Server Component，交互页面保持 Client Component
- **组件拆分**：页面只做数据获取+组合，业务逻辑抽到 hooks，UI 抽到独立组件
- **类型生成**：`npm run generate-types` 从后端 OpenAPI spec 生成 `api-types.ts`

### 数据文件 (`data/`)

- `scoring_rules.yml` — 评分规则配置（可通过 API 编辑）
- `keywords.yml` — 关键词组配置
- `sources.yml` — 数据源配置

### 数据库

默认 SQLite（开发），生产用 PostgreSQL（`DATABASE_URL` 环境变量切换）。所有模型在 `models.py` 中定义，通过 SQLModel 自动建表。

> 注意：`.env.example` 目前缺少 `JWT_SECRET` 和 `CORS_ORIGINS`，生产部署前需补齐。

## 核心约束

- 所有 AI 生成结论必须保存 `evidence_text`, `source_url`, `confidence`
- 不允许模型编造电话、联系人、预算金额、公告链接（`validate_extraction()` 强制执行）
- 测试中不得访问真实外网；使用 fixtures 或 mocks
- 爬虫必须限速、尊重 robots；优先 API 或公开 HTML
- 代码保持模块化：采集、抽取、评分、线索服务、API 分离
- Python 使用类型注解，核心逻辑必须有单元测试
- 配置走环境变量和 YAML，不硬编码密钥

## Git 工作流

- `main` ← 只从 `dev` 合并
- `dev` ← 特性分支和 bugfix 分支的合入目标
- 新功能在特性分支开发，完成后合并到 `dev`

## CI

GitHub Actions (`.github/workflows/ci.yml`)：Python 3.11/3.12 矩阵运行 lint + test，Node 20 运行前端 lint + build。


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
