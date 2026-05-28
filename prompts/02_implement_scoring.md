# Prompt：实现线索评分模型

请基于 docs/06_scoring_model.md 和 data/scoring_rules.yml 实现：

- src/leadradar/scoring.py
- tests/test_scoring.py

要求：

1. 输入 LeadScoringInput，输出 LeadScoringResult。
2. 输出 total_score、grade、breakdown、reasons。
3. 评分逻辑必须可配置，优先读取 data/scoring_rules.yml。
4. 同一输入结果稳定。
5. 覆盖至少 4 个测试：S级采购意向、A级中标服务商、B级认证客户、D级无关线索。
6. 不要调用外部服务。
