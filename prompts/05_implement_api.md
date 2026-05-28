# Prompt：实现 FastAPI API

请基于 docs/07_api_spec.md 实现或完善：

- src/leadradar/main.py
- src/leadradar/services/lead_service.py
- 相关 Pydantic schemas
- tests/test_api.py

要求：

1. 实现 /health。
2. 实现 /api/v1/leads 列表和详情。
3. 实现 /api/v1/leads/{id}/follow-ups。
4. 实现 /api/v1/leads/{id}/generate-call-script。
5. 实现 CSV 导出。
6. 使用内存/SQLite mock 或 service stub 完成测试，不依赖真实数据库。
7. API 错误返回结构化 JSON。
