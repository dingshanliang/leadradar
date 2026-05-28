# 07 API 设计

## 1. 基础约定

- Base URL: `/api/v1`
- JSON UTF-8
- 时间使用 ISO 8601
- MVP 可先不做复杂鉴权，预留 API key / session

## 2. Endpoints

### Health

`GET /health`

返回：

```json
{"status": "ok"}
```

### Sources

`GET /sources`

`POST /sources`

```json
{
  "name": "中国政府采购网",
  "source_type": "government_procurement",
  "base_url": "https://www.ccgp.gov.cn/",
  "enabled": true
}
```

### Crawl Tasks

`POST /crawl-tasks`

```json
{
  "source_id": "uuid",
  "query": "采购意向 农产品区域公用品牌 预算金额",
  "limit": 50
}
```

`GET /crawl-tasks/{id}`

### Raw Documents

`GET /documents`

筛选：source_id、document_type、parse_status、date_range。

`GET /documents/{id}`

### Extraction

`POST /documents/{id}/extract`

触发 LLM 抽取。

### Leads

`GET /leads`

Query 参数：

```text
score_min
score_max
grade
signal_type
customer_type
province
status
recommended_package
keyword
```

`GET /leads/{id}`

`PATCH /leads/{id}`

```json
{
  "lead_status": "called",
  "owner": "Eric"
}
```

### Follow-ups

`POST /leads/{id}/follow-ups`

```json
{
  "channel": "phone",
  "result": "connected",
  "notes": "对方关注数字标签，约下周演示",
  "next_action_at": "2026-06-03T10:00:00+08:00"
}
```

### Call Script

`POST /leads/{id}/generate-call-script`

返回：

```json
{
  "opening": "您好，我看到贵单位近期...",
  "questions": ["当前包装二维码由谁维护？"],
  "wechat_followup": "您好，我是刚才电话...",
  "avoid": ["不要说买SaaS", "不要承诺销售额增长"]
}
```

### Export

`GET /leads/export.csv`

`GET /leads/export.xlsx`

## 3. 错误格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid signal_type",
    "details": {}
  }
}
```
