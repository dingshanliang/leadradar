# 09 MVP 开发任务拆解

## Phase 0：准备

### T-000 阅读交接资料

- 阅读 START_HERE.md、CLAUDE.md、docs/00、docs/01、docs/02、docs/06、docs/10。
- 输出理解与实施计划。
- 不改代码。

## Phase 1：数据模型与配置

### T-101 建立 SQLModel 数据模型

文件：`src/leadradar/models.py`

完成：Source、CrawlTask、RawDocument、ExtractionRun、Organization、Signal、Lead、LeadScore、Contact、FollowUp、Blocklist。

验收：模型可导入，无循环引用；字段与 docs/04 对齐。

### T-102 配置加载

文件：`src/leadradar/config.py`

完成：读取 .env，支持 LLM、数据库、爬虫限速、合规开关。

### T-103 YAML 配置加载

文件：`data/keywords.yml`、`data/sources.yml`、`data/scoring_rules.yml`

完成：加载关键词、数据源、评分规则。

## Phase 2：评分模型

### T-201 实现评分引擎

文件：`src/leadradar/scoring.py`

完成：输入 Signal/LeadProfile，输出分数、等级、明细、原因。

验收：`tests/test_scoring.py` 通过。

### T-202 反馈字段预留

为后续销售反馈影响评分做数据结构预留。

## Phase 3：LLM 抽取

### T-301 定义抽取 Schema

文件：`schemas/extraction.schema.json`、`src/leadradar/schemas.py`

完成：Pydantic 模型与 JSON Schema 对齐。

### T-302 实现 LLM Provider 接口

文件：`src/leadradar/llm/extraction.py`

完成：Mock provider + OpenAI-compatible provider 接口。

### T-303 实现抽取校验

完成：验证 JSON、检查 evidence、禁止编造关键字段。

## Phase 4：采集器

### T-401 定义采集器接口

文件：`src/leadradar/crawlers/base.py`

完成：SearchProvider、FetchProvider、DocumentParser 接口。

### T-402 实现示例搜索 Provider

MVP 可先实现 mock/local provider，用 fixtures 模拟公开公告。

### T-403 实现正文抽取

文件：`src/leadradar/crawlers/parser.py`

完成：HTML → text；PDF 预留。

### T-404 去重

基于 URL hash + content hash。

## Phase 5：线索服务

### T-501 文档到信号流程

RawDocument → ExtractionRun → Signal。

### T-502 信号到线索流程

Signal → Organization → Lead → LeadScore。

### T-503 电话话术生成

根据客户类型、信号、产品包生成开场白、问题和微信跟进文案。

## Phase 6：API

### T-601 FastAPI 基础接口

完成 /health、/sources、/leads、/documents。

### T-602 线索详情和跟进

完成 lead detail、follow-up、status update。

### T-603 导出

完成 CSV/Excel 导出。

## Phase 7：UI 或临时工作台

MVP 可选：

- 简单 HTML 管理页；或
- Next.js 前端；或
- 先只用 Swagger + CSV。

## Phase 8：验收

### T-801 端到端演示

输入一条样例公告，系统生成：

- RawDocument
- ExtractionRun
- Signal
- Lead
- Score
- Call Script

### T-802 合规检查

确认不含自动骚扰、个人手机号抓取、绕过限制等能力。
