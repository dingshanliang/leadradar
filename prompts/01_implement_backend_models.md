# Prompt：实现后端数据模型

请基于 docs/04_data_model.md 和 sql/schema.sql 实现或完善：

- src/leadradar/models.py
- src/leadradar/db.py
- src/leadradar/schemas.py

要求：

1. 使用 SQLModel 或 SQLAlchemy，保持类型注解清晰。
2. 模型覆盖 Source、CrawlTask、RawDocument、ExtractionRun、Organization、Signal、Lead、LeadScore、Contact、FollowUp、Blocklist。
3. 不要实现复杂业务逻辑。
4. 添加最小单元测试，验证模型可导入、枚举值合法、关键字段存在。
5. 不要访问外网。
6. 保留审计字段 source_url、evidence_text、fetched_at。

完成后运行：

```bash
make test
```
