# 05 LLM 结构化抽取规范

## 1. 大模型职责

大模型只做从公开文本中抽取和归类，不负责编造。

允许：

- 判断公告类型
- 提取项目、预算、采购单位、地区、联系人
- 提取证据片段
- 判断匹配关键词
- 推荐产品包
- 生成电话话术

禁止：

- 编造电话号码
- 编造联系人
- 编造预算金额
- 编造采购时间
- 编造不存在的来源链接

## 2. 输入内容

每次抽取输入：

```json
{
  "url": "...",
  "title": "...",
  "published_at": "...",
  "source_name": "...",
  "text": "清洗后的正文，不超过模型上下文限制",
  "keyword_context": ["区域公用品牌", "农产品追溯"]
}
```

## 3. 输出 JSON Schema

见 `schemas/extraction.schema.json`。

关键字段：

```json
{
  "is_relevant": true,
  "signal_type": "procurement_intent",
  "customer_type": "region_brand_government",
  "organization_name": "某县农业农村局",
  "project_name": "某县农产品区域公用品牌建设项目",
  "budget_amount": {"value": 1200000, "currency": "CNY", "raw": "120万元"},
  "expected_time": "2026-07",
  "region": {"province": "江西省", "city": "...", "county": "..."},
  "need_summary": "区域品牌建设、产品包装、品牌推广、数字化展示",
  "matched_keywords": ["区域公用品牌", "农产品品牌"],
  "product_fit": ["区域品牌数字化管理包", "包装二维码升级包"],
  "budget_source_guess": ["区域品牌运营预算"],
  "evidence": [
    {"field": "budget_amount", "text": "预算金额：120万元"}
  ],
  "confidence": 0.87,
  "uncertainties": []
}
```

## 4. 抽取 Prompt 模板

```text
你是 B2B 销售信号抽取器。请只根据输入文本抽取结构化信息。

规则：
1. 不确定就填 null 或加入 uncertainties。
2. 不允许编造电话、联系人、预算、时间。
3. 每个关键字段必须给 evidence。
4. 只输出合法 JSON，不输出解释性文字。
5. product_fit 只能从给定枚举中选择。

产品包枚举：
- 数字标签合规启动包
- 溯源信任包
- 包装扫码增长包
- 区域品牌数字化管理包
- 渠道白标工具包

信号类型枚举：
- procurement_intent
- tender_notice
- winning_notice
- contract_notice
- certification_registry
- recruiting_signal
- exhibition_signal
- product_launch
- packaging_upgrade
- channel_partner
- company_website
- news_report
- irrelevant

输入文本：
{{document_text}}
```

## 5. 置信度规则

- 0.9+：字段完整，有预算/时间/单位/证据。
- 0.7-0.89：相关性明确，但部分字段缺失。
- 0.5-0.69：可能相关，需人工确认。
- <0.5：不进入线索池。

## 6. 话术生成 Prompt

输入：客户类型、信号、预算口、推荐产品包。

输出：

- 80-120 字电话开场白
- 3-5 个诊断问题
- 微信跟进文案
- 不应提及的内容

原则：不说“卖SaaS”，而说“包装二维码升级/数字标签/溯源/区域品牌数字化”。
