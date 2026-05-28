# LeadRadar 数字包装商机雷达

LeadRadar 是一个垂直 B2B 销售情报系统，面向食品、农产品、区域品牌、包装设计/印刷、检测认证、电商代运营等场景。

它不做普通企业名录，而是围绕“预算正在发生的信号”发现客户：采购意向、招标公告、中标公告、认证名录、数字标签政策窗口、包装升级、新品发布、招聘、电商活跃等。

## MVP 功能

- 关键词与数据源配置
- 公告/网页采集任务
- 正文抽取与去重
- LLM 结构化抽取
- 预算信号识别
- 线索评分与评分理由
- 客户详情和证据链
- 电话开场白生成
- 外呼跟进状态
- Excel/CSV 导出

## 技术栈建议

- Python 3.11+
- FastAPI
- SQLModel / SQLAlchemy
- PostgreSQL
- Redis + RQ/Celery
- Playwright / httpx / trafilatura
- Pydantic
- OpenAI / Anthropic / 兼容 OpenAI 协议的大模型接口
- Next.js 或简单管理后台（第二阶段）

## 本仓库状态

当前是开发交接包 + 轻量脚手架，不是完整可生产运行系统。Claude Code 应基于 docs 与 prompts 分阶段实现。

## 本地启动建议

```bash
cp .env.example .env
make setup
make test
make dev
```

第一阶段可以只跑后端 API 与测试，不必立刻实现前端。
