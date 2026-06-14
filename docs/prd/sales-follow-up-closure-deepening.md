# PRD: 销售跟进闭环深化

> **Author**: generated
> **Date**: 2026-06-14
> **Status**: Clarified
> **Pilot-ready**: Yes

## 1. Overview

在销售日常工作中，电话跟进后经常因没有明确的「下次跟进时间」和「到期提醒」而遗漏高意向客户。本 PRD 在现有「外呼工作台 + 跟进记录」基础上，补齐 **下次跟进时间设置、到期提醒入口、结构化通话原因、黑名单屏蔽** 四个能力，形成从拨打 → 记录 → 提醒 → 复盘的完整闭环。

## 2. Problem Statement

- **Who**: 一线销售人员、销售主管
- **Problem**:
  - 当前跟进表单只有渠道、结果、备注，无法设置下次跟进时间
  - 后台已有 `GET /follow-ups/due` 接口，但前端没有入口查看到期跟进
  - 通话结果使用纯文本（如"未接通"、"负责人拒绝"），无法按原因统计复盘
  - 遇到明确拒绝或无效客户时，没有快捷方式屏蔽，导致重复拨打
- **Impact**: 跟进遗漏、重复骚扰客户、复盘数据缺失，降低线索转化率
- **Current workaround**: 销售人员自行在备注中记录下次跟进时间，主管人工抽查

## 3. Target Users & Roles

| Role | Description | Key Actions |
|------|-------------|-------------|
| 销售代表 | 负责电话跟进线索 | 提交跟进记录、设置下次跟进时间、查看到期提醒、屏蔽无效客户 |
| 销售主管 | 负责复盘团队效率 | 查看按原因分类的跟进统计、检查到期跟进处理率 |

## 4. Functional Requirements

### 4.1 提交跟进记录时设置下次跟进时间

**Who**: 销售代表
**Description**: 在现有外呼工作台提交跟进记录时，增加「下次跟进时间」字段。

**Behavior**:
1. 销售在工作台填写渠道、通话结果、备注
2. 销售可选择「下次跟进时间」（日期 + 时间，精确到小时）
3. 提交后，`next_action_at` 写入 `FollowUp` 表
4. 系统根据所选通话结果自动建议一个默认的下次跟进时间（可修改）
5. 若销售清空时间，则该跟进记录无到期提醒

**Business Rules**:
- 下次跟进时间必须晚于当前时间，否则校验失败
- 默认建议规则（可配置，启动时从 `data/follow_up_suggestions.yml` 加载）：
  - 「未接通」→ 2 小时后
  - 「愿意了解」→ 1 个工作日后
  - 「预约诊断」→ 预约时间当天早 9 点
  - 「发送资料」→ 3 个工作日后
  - 「找到负责人」→ 1 个工作日后
- 建议值由后端根据 `result` 返回，前端展示并允许用户修改

**Error Handling**:
- 下次跟进时间早于当前时间：返回 `422` "下次跟进时间必须晚于当前时间"
- lead 不存在：返回 `404` "Lead not found"

### 4.2 工作台与侧边栏展示到期跟进提醒

**Who**: 销售代表、销售主管
**Description**: 基于已有 `GET /follow-ups/due` 接口，在前端增加到期跟进入口。

**Behavior**:
1. 侧边栏「线索池」图标旁展示到期跟进数量徽章（仅当 >0 时显示）
2. 点击徽章/菜单进入「到期跟进」页面，按到期时间升序展示线索
3. 每条展示：机构名称、到期时间、上次通话结果、快捷进入工作台按钮
4. MVP 阶段不过滤负责人，所有登录用户可见全部到期跟进

**Business Rules**:
- 到期定义：当前时间 >= `next_action_at` 且该线索状态不是 `won` / `lost` / `invalid` / `blocked`
- 默认展示未来 7 天内到期和已逾期的跟进
- 徽章数字最大显示 99+，实际数量 hover 显示

**Error Handling**:
- 后端返回空列表：展示空状态「暂无到期跟进」

### 4.3 通话结果结构化（结果 + 原因）

**Who**: 销售代表
**Description**: 将现有纯文本通话结果升级为「结果类别 + 原因」两级结构，便于统计。

**Behavior**:
1. 跟进表单中「通话结果」改为两级选择：
   - 先选结果类别：未接通 / 接通但无兴趣 / 接通有意向 / 已预约 / 已成交 / 无效
   - 再选具体原因：如「未接通」下可选「无人接听 / 关机 / 占线」
2. 选择后仍自动映射到现有 `LeadStatus`（保持状态流转不变）
3. 原因标签随跟进记录保存并展示在历史记录中

**Business Rules**:
- 结果类别与原因字典由 `data/call_results.yml` 配置，后端启动加载，并通过 `GET /api/v1/meta` 返回
- 必须选择原因后才能提交
- 现有 `CALL_RESULTS` 中的文本值作为原因字典的显示标签保留向后兼容

**Error Handling**:
- 未选择原因：前端阻止提交，提示「请选择具体原因」
- 原因不在允许字典中：返回 `422` "Invalid follow-up reason"

### 4.4 将线索或机构加入黑名单

**Who**: 销售代表
**Description**: 在跟进记录提交时或线索详情页，支持将线索/机构标记为拒绝联系。

**Behavior**:
1. 销售在通话结果中选择「无效客户」或「加入拒绝联系」
2. 提交后系统自动将该线索状态更新为 `blocked`
3. 同时在 `Blocklist` 表中写入记录：
   - `organization_id` = 该线索所属机构 ID
   - `reason` = 选择的拒绝原因
4. 线索池列表中屏蔽状态的线索默认不展示，可通过筛选单独查看
5. 线索详情页增加「解除屏蔽」按钮（任何登录用户均可操作，MVP 暂不细分权限）

**Business Rules**:
- 被屏蔽的线索不参与仪表盘统计和周报统计
- 被屏蔽的机构下新产生的线索进入系统时自动标记为 `blocked` 并不提醒
- 屏蔽操作不可逆，但可解除屏蔽（解除后状态恢复为 `new`）

**Error Handling**:
- 重复屏蔽同一机构：返回 `409` "该机构已在黑名单中"
- 无权限解除屏蔽：返回 `403` "无权限操作"

### 4.5 查看带原因标签与下次跟进提示的历史记录

**Who**: 销售代表、销售主管
**Description**: 增强现有跟进历史展示，增加原因标签和下次跟进时间。

**Behavior**:
1. 工作台右侧历史记录区域展示每条跟进的：
   - 时间
   - 结果类别 + 原因标签
   - 渠道
   - 备注（折叠，点击展开）
   - 下次跟进时间（如有，且已过期标红）
2. 线索详情页「跟进记录」组件同步展示相同信息

**Business Rules**:
- 历史记录按时间倒序排列
- 已过期的下次跟进时间用红色高亮
- 备注默认折叠，超过 60 字符自动折叠

## 5. Dependencies

| Dependency | Type | Integration Point | Notes |
|------------|------|-------------------|-------|
| JWT 认证 | internal | 现有 `auth.py` + `api-client.ts` | 黑名单解除权限校验复用现有 role |
| Lead 状态机 | internal | 现有 `LeadStatus` 枚举 | 新增 `blocked` 状态已在枚举中 |
| FollowUp 模型 | internal | 现有 `models.FollowUp` | `next_action_at` 字段已存在 |
| Blocklist 模型 | internal | 现有 `models.Blocklist` | 当前无 API，需要新增路由 |
| 到期跟进 API | internal | 现有 `GET /follow-ups/due` | 仅补充前端入口 |
| Meta 枚举 | internal | 现有 `GET /api/v1/meta` | 需要扩展返回通话原因字典 |

## 6. Data Model

### 变更说明

| Entity | 变更 | Key Fields | Notes |
|--------|------|-----------|-------|
| FollowUp | schema 扩展 | `next_action_at` 已存在；`result` 从纯文本改为「类别 + 原因」结构存储 | 保持字符串存储，格式为 `category:reason`，便于查询 |
| FollowUpCreate / FollowUpOut | schema 扩展 | 增加 `next_action_at`, `reason`, `result_category` | 向后兼容：旧数据 `reason` 为空时展示为 legacy |
| Blocklist | 新增 API 使用 | `organization_id`, `contact_value_hash`, `reason`, `created_at` | 现有表已定义 |
| Lead | 行为变更 | `lead_status` 可因屏蔽操作更新为 `blocked` | 枚举已支持 |

### 状态机

```
[任意非终态] -- 提交跟进选择"无效/拒绝联系" --> [blocked]
[blocked] -- 解除屏蔽 --> [new]

其他现有状态流转保持不变：
new -> qualified -> called -> connected -> diagnosis_scheduled -> proposal_sent -> won
                                          |
                                          +-> lost
```

## 7. Edge Cases & Boundary Conditions

| Scenario | Expected Behavior |
|----------|-------------------|
| 销售设置下次跟进时间为节假日 | 不自动跳过节假日，按自然时间计算 |
| 同一机构多个线索，屏蔽其中一个 | 默认仅屏蔽该线索；提交表单提供「同时屏蔽整个机构」复选框 |
| 到期跟进已被其他销售处理 | 列表实时刷新，不再展示 |
| 提交跟进时 result 与 reason 不匹配 | 后端校验返回 `422` "结果类别与原因不匹配" |
| 解除屏蔽后该机构又有新线索 | 新线索不再自动屏蔽（解除仅针对当前黑名单记录） |

## 8. Out of Scope

- 自动拨号 / 自动外呼
- 个人手机号抓取
- 短信 / 邮件模板自动发送
- 复杂的审批流（如黑名单解除需主管审批）
- 多租户下的权限隔离
- 与外部 CRM / 企微集成

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| 跟进记录中设置下次跟进时间的比例 | ≥ 70% | 统计 FollowUp.next_action_at 非空占比 |
| 到期跟进 24 小时内处理率 | ≥ 60% | 统计到期后在 24h 内有新跟进记录的线索占比 |
| 无效线索重复拨打率 | ≤ 10% | 统计被屏蔽线索在屏蔽后再次被跟进的次数 |
| 通话原因分类覆盖率 | ≥ 80% | 统计 reason 字段非空的跟进记录占比 |

## 10. Clarifications Applied

以下 Open Questions 已在 Phase 1 确认并应用默认值：

| ID | Decision | Applied Value |
|----|----------|---------------|
| OQ-001 | 默认建议时间规则 | 使用 `data/follow_up_suggestions.yml` 配置，启动加载 |
| OQ-002 | 到期跟进可见性 | MVP 不过滤负责人，全部登录用户可见 |
| OQ-003 | 到期跟进展示范围 | 未来 7 天 + 已逾期 |
| OQ-004/OQ-005 | 原因字典 | 使用 `data/call_results.yml`，启动加载，通过 `/api/v1/meta` 返回 |
| OQ-006/OQ-010 | 黑名单记录范围 | 默认记录 organization_id；提交时提供「同时屏蔽整个机构」复选框 |
| OQ-007 | 解除权限 | MVP 任何登录用户可解除 |
| OQ-008 | 新线索自动屏蔽 | 是，被屏蔽机构的新线索自动标记 blocked |
| OQ-009 | 节假日处理 | 不跳过，按自然时间 |
| OQ-011 | 解除屏蔽的后续影响 | 不影响该机构后续新线索 |
