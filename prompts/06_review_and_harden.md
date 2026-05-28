# Prompt：代码审查与加固

请对当前代码做一次 MVP 上线前审查。重点：

1. 是否存在硬编码 API key 或敏感信息。
2. 是否有外网访问测试。
3. 是否有自动外呼、自动群发、抓个人手机号等违规能力。
4. LLM 输出是否有 evidence 和 confidence。
5. 评分模型是否可解释。
6. 数据模型是否保留 source_url、fetched_at、evidence_text。
7. 是否所有核心逻辑有测试。
8. README 和 Makefile 是否能支持新开发者启动。

输出：

- Critical issues
- Warnings
- Suggestions
- Recommended patches

请只修改确有必要的问题。
