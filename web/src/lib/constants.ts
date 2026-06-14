import type { Grade, LeadStatus } from "./schemas";

/** 通话结果类别 → 原因 & 对应线索状态 */
export const CALL_RESULT_CATEGORIES: Record<
  string,
  { reasons: readonly string[]; status: LeadStatus }
> = {
  未接通: { reasons: ["无人接听", "关机", "占线"], status: "called" },
  接通有意向: { reasons: ["需方案", "约演示", "询价"], status: "connected" },
  接通无意向: { reasons: ["暂无需求", "已有供应商"], status: "lost" },
};

/** 默认下次跟进时间建议（当后端 meta 未返回时兜底） */
export const FOLLOW_UP_SUGGESTIONS: Record<string, string> = {
  未接通: "2h",
  接通有意向: "1d",
  接通无意向: "7d",
};

export const GRADE_COLORS: Record<Grade, string> = {
  S: "bg-success/15 text-success",
  A: "bg-cta/15 text-cta",
  B: "bg-warning/15 text-warning",
  C: "bg-warning/15 text-warning",
  D: "bg-bg-muted text-muted",
};

export const GRADE_DOT_COLORS: Record<Grade, string> = {
  S: "bg-success",
  A: "bg-cta",
  B: "bg-warning",
  C: "bg-warning",
  D: "bg-muted",
};

export const STATUS_LABELS: Record<LeadStatus, string> = {
  new: "新建",
  qualified: "已验证",
  called: "已拨打",
  connected: "已接通",
  diagnosis_scheduled: "已预约诊断",
  proposal_sent: "已发送方案",
  won: "已成交",
  lost: "已流失",
  invalid: "无效",
  blocked: "已屏蔽",
};

export const STATUS_COLORS: Record<LeadStatus, string> = {
  new: "bg-cta/10 text-cta",
  qualified: "bg-primary/10 text-primary",
  called: "bg-secondary/10 text-secondary",
  connected: "bg-success/10 text-success",
  diagnosis_scheduled: "bg-success/15 text-success",
  proposal_sent: "bg-primary/15 text-primary",
  won: "bg-success/15 text-success",
  lost: "bg-bg-muted text-muted",
  invalid: "bg-bg-muted text-muted line-through",
  blocked: "bg-danger/10 text-danger",
};

export const SIGNAL_TYPE_LABELS: Record<string, string> = {
  procurement_intent: "采购意向",
  tender_notice: "招标公告",
  winning_notice: "中标公告",
  contract_notice: "合同公告",
  certification_registry: "认证登记",
  recruiting_signal: "招聘信号",
  exhibition_signal: "展会信号",
  product_launch: "产品发布",
  packaging_upgrade: "包装升级",
  channel_partner: "渠道合作",
  company_website: "企业官网",
  news_report: "新闻报道",
};

export const BUDGET_BUCKET_LABELS: Record<string, string> = {
  "<10万": "< 10万",
  "10-50万": "10-50万",
  "50-100万": "50-100万",
  "100-500万": "100-500万",
  ">500万": "> 500万",
};

export const CALL_RESULTS = [
  { value: "未接通", status: "called" },
  { value: "前台拦截", status: "called" },
  { value: "找到负责人", status: "connected" },
  { value: "负责人拒绝", status: "lost" },
  { value: "愿意了解", status: "connected" },
  { value: "预约诊断", status: "diagnosis_scheduled" },
  { value: "发送资料", status: "connected" },
  { value: "无效客户", status: "invalid" },
  { value: "加入拒绝联系", status: "blocked" },
] as const;
