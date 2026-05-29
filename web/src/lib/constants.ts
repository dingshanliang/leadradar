import type { Grade, LeadStatus } from "./schemas";

export const GRADE_COLORS: Record<Grade, string> = {
  S: "bg-emerald-100 text-emerald-800",
  A: "bg-sky-100 text-sky-800",
  B: "bg-amber-100 text-amber-800",
  C: "bg-orange-100 text-orange-800",
  D: "bg-gray-100 text-gray-600",
};

export const GRADE_DOT_COLORS: Record<Grade, string> = {
  S: "bg-emerald-500",
  A: "bg-sky-500",
  B: "bg-amber-500",
  C: "bg-orange-500",
  D: "bg-gray-400",
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
  new: "bg-blue-50 text-blue-700",
  qualified: "bg-indigo-50 text-indigo-700",
  called: "bg-cyan-50 text-cyan-700",
  connected: "bg-teal-50 text-teal-700",
  diagnosis_scheduled: "bg-emerald-50 text-emerald-700",
  proposal_sent: "bg-violet-50 text-violet-700",
  won: "bg-green-50 text-green-700",
  lost: "bg-gray-50 text-gray-600",
  invalid: "bg-gray-100 text-gray-500 line-through",
  blocked: "bg-red-50 text-red-700",
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
