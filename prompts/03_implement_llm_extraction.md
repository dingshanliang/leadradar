# Prompt：实现 LLM 抽取模块

请基于 docs/05_llm_extraction.md 和 schemas/extraction.schema.json 实现：

- src/leadradar/llm/extraction.py
- src/leadradar/schemas.py
- tests/test_extraction_schema.py

要求：

1. 定义 LLMProvider 抽象接口。
2. 实现 MockLLMProvider，用固定 fixture 返回结构化结果。
3. 实现 OpenAICompatibleLLMProvider 的接口骨架，但测试中不要真实调用外部 API。
4. 对 LLM 输出做 JSON Schema/Pydantic 校验。
5. 校验 evidence：关键字段如果没有 evidence，应降低 confidence 或标记 review_required。
6. 不允许模型编造预算、电话、联系人。
