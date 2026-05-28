# 数字包装商机雷达 LeadRadar — 开发交接包

本交接包用于让 Claude Code 直接进入项目目录并开始开发 **“数字包装商机雷达”**。

产品一句话：

> 自动扫描公开预算信号、行业资质、招投标公告、企业动态和渠道信息，识别食品、农产品、区域品牌、包装/印刷/检测/代运营相关客户的真实商机，并生成可电话跟进的高质量线索。

## 建议使用方式

1. 解压本资料包。
2. 在项目根目录启动 Claude Code：

```bash
cd leadradar_handover_package
claude
```

3. 首次进入后，把下面这句话发给 Claude Code：

```text
请先阅读 START_HERE.md、CLAUDE.md、docs/00_product_handover.md 和 docs/09_mvp_tasks.md，然后不要立即写代码。先输出你对项目目标、MVP范围、技术架构、关键风险、开发顺序的理解，并列出第一阶段实施计划。等待我确认后再开始改文件。
```

4. 确认计划后，可使用 `prompts/00_first_prompt_for_claude_code.md` 作为第一轮开发提示词。
5. 后续按 `docs/09_mvp_tasks.md` 中的任务 ID 分批开发。

## 资料包结构

```text
.
├── START_HERE.md
├── CLAUDE.md                         # 给 Claude Code 的项目级常驻上下文
├── README.md                         # 项目说明
├── docs/                             # 产品、架构、数据、合规、验收资料
├── prompts/                          # 可直接复制给 Claude Code 的开发提示词
├── .claude/agents/                   # Claude Code 项目级子代理定义
├── .claude/skills/                   # Claude Code 项目级技能/命令模板
├── data/                             # 关键词、数据源、评分规则、样例线索
├── schemas/                          # LLM结构化抽取和线索对象 JSON Schema
├── sql/                              # 初版数据库 schema
├── src/leadradar/                    # Python 后端脚手架
├── tests/                            # 最小测试样例
├── scripts/                          # 辅助脚本
├── pyproject.toml
├── docker-compose.yml
├── Makefile
└── .env.example
```

## MVP 优先级

第一版只做：

```text
政府采购 / 公共资源公告
+ 农产品/食品/区域品牌/追溯/包装关键词
+ 大模型结构化抽取
+ 线索评分
+ 电话话术
+ Excel 导出
+ 跟进记录
```

暂不做：

```text
自动拨号、自动群发、自动加微信、个人手机号抓取、绕过反爬、全网社媒爬取、大而全CRM。
```

## 开发原则

- 先做内部工具，再做 SaaS 产品。
- 先做显性预算信号，再做弱信号。
- 所有 AI 结论必须有证据片段和来源链接。
- 不采集非公开个人信息；拒绝联系后必须加入黑名单。
- 先跑通“发现线索 → 评分 → 人工外呼 → 反馈回流”的闭环。
