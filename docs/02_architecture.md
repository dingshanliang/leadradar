# 02 技术架构

## 1. 总体架构

```text
数据源层
  ├─ 政府采购/公共资源
  ├─ 市监/农业/认证名录
  ├─ 搜索引擎/网页搜索
  ├─ 官网/新闻/展会/招聘
  └─ 第三方企业信息 API

采集层
  ├─ 定时任务
  ├─ 搜索任务
  ├─ 网页抓取
  ├─ PDF解析
  ├─ 正文抽取
  └─ 去重与快照

理解层
  ├─ 规则匹配
  ├─ LLM结构化抽取
  ├─ 实体识别
  ├─ 预算信号识别
  └─ 置信度评估

业务层
  ├─ 线索评分
  ├─ 客户画像
  ├─ 产品包匹配
  ├─ 话术生成
  ├─ 跟进管理
  └─ 导出/报表

应用层
  ├─ 线索看板
  ├─ 客户详情
  ├─ 外呼工作台
  ├─ 配置管理
  └─ API/导出
```

## 2. 推荐技术栈

### 后端

- Python 3.11+
- FastAPI
- SQLModel/SQLAlchemy
- PostgreSQL
- Redis + RQ 或 Celery
- Pydantic

### 采集

- httpx：普通 HTTP
- Playwright：需要渲染的页面
- trafilatura / BeautifulSoup：正文抽取
- pypdf / pdfplumber：PDF 文本解析
- OCR 仅作为最后手段

### LLM

- 抽象 Provider 接口
- 支持 mock provider 便于测试
- 支持 OpenAI-compatible API
- 支持 Anthropic 或其他模型

### 检索

MVP 可以先不用 Elasticsearch，直接 PostgreSQL + ILIKE + 索引。第二阶段再引入 OpenSearch/Meilisearch/pgvector。

## 3. 核心数据流

```text
CrawlTask
↓
RawDocument
↓
DocumentClassifier
↓
ExtractionRun
↓
Signal
↓
Organization / Contact
↓
Lead
↓
LeadScore
↓
CallScript
↓
FollowUp
```

## 4. Provider 设计

外部依赖均封装为接口：

```python
class SearchProvider:
    async def search(self, query: str, *, limit: int) -> list[SearchResult]: ...

class FetchProvider:
    async def fetch(self, url: str) -> RawPage: ...

class LLMProvider:
    async def extract(self, prompt: str, schema: dict) -> dict: ...

class CompanyInfoProvider:
    async def lookup(self, organization_name: str) -> CompanyProfile | None: ...
```

## 5. 分层成本控制

```text
规则过滤 → 小模型/Mock初筛 → 强模型抽取 → 人工确认
```

- 不相关页面不进模型。
- 相同 URL / 正文 hash 不重复抽取。
- 高价值信号才调用强模型。
- LLM 输出必须保存原始响应，便于审计。

## 6. 异常与重试

- 网络错误：指数退避，最多 3 次。
- 解析失败：保存 raw document 并标记 parse_failed。
- LLM 格式错误：尝试一次修复；仍失败则人工队列。
- 低置信度：不进入高优先级外呼池。

## 7. 部署形态

### MVP 内部工具

```text
FastAPI + PostgreSQL + Redis + 单机定时任务
```

### V1 SaaS

```text
多租户 + 队列 worker + 独立采集 worker + 对象存储 + 权限系统
```
