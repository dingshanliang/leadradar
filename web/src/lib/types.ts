// TypeScript types mirroring backend Pydantic schemas

export interface Source {
  id: string;
  name: string;
  source_type: string;
  base_url: string | null;
  priority: string | null;
  enabled: boolean;
  rate_limit_per_minute: number;
  created_at: string;
}

export interface Document {
  id: string;
  source_id: string | null;
  url: string;
  title: string | null;
  published_at: string | null;
  fetched_at: string;
  parse_status: string;
  document_type: string | null;
}

export interface LeadListItem {
  id: string;
  organization_name: string | null;
  customer_type: string | null;
  recommended_package: string | null;
  budget_bucket: string | null;
  signal_type: string | null;
  province: string | null;
  lead_status: LeadStatus;
  total_score: number;
  grade: Grade;
  created_at: string;
}

export interface OrganizationBrief {
  id: string;
  name: string;
  province: string | null;
  city: string | null;
  county: string | null;
  organization_type: string | null;
}

export interface SignalBrief {
  id: string;
  signal_type: string;
  title: string | null;
  budget_amount: number | null;
  source_url: string | null;
  evidence_text: string | null;
  confidence: number;
  created_at: string;
}

export interface ScoreBrief {
  total_score: number;
  grade: string;
  budget_strength_score: number;
  scenario_fit_score: number;
  timing_score: number;
  reachability_score: number;
  leverage_score: number;
}

export interface CallScript {
  opening: string;
  questions: string[];
  wechat_follow_up: string;
}

export interface LeadDetail {
  id: string;
  organization: OrganizationBrief;
  signal: SignalBrief;
  score: ScoreBrief;
  call_script: CallScript;
  customer_type: string | null;
  recommended_package: string | null;
  budget_bucket: string | null;
  lead_status: LeadStatus;
  owner: string | null;
  created_at: string;
  updated_at: string;
}

export interface FollowUpCreate {
  channel: string;
  result: string;
  notes?: string | null;
  contact_id?: string | null;
}

export interface FollowUpOut {
  id: string;
  lead_id: string;
  contact_id: string | null;
  channel: string;
  result: string;
  notes: string | null;
  next_action_at: string | null;
  created_at: string;
}

export type Grade = "S" | "A" | "B" | "C" | "D";

export type LeadStatus =
  | "new"
  | "qualified"
  | "called"
  | "connected"
  | "diagnosis_scheduled"
  | "proposal_sent"
  | "won"
  | "lost"
  | "invalid"
  | "blocked";

export interface LeadFilters {
  grade?: string;
  status?: string;
  signal_type?: string;
  limit?: number;
  offset?: number;
}

export interface DistributionItem {
  name: string;
  count: number;
}

export interface Stats {
  total: number;
  sa_count: number;
  pending: number;
  scheduled: number;
  invalid: number;
  invalid_rate: string;
  signal_type_distribution: DistributionItem[];
  package_distribution: DistributionItem[];
  province_distribution: DistributionItem[];
}

export interface EnumItem {
  key: string;
  label: string;
}

export interface Meta {
  signal_types: EnumItem[];
  statuses: EnumItem[];
  grades: string[];
  budget_buckets: string[];
}

export interface KeywordGroup {
  name: string;
  description: string;
  keywords: string[];
}

export interface ScoringDimension {
  name: string;
  max_score: number;
  description: string;
}

export interface ProductPackage {
  name: string;
  target: string;
  desc: string;
}

export interface AppConfig {
  keyword_groups: KeywordGroup[];
  scoring_dimensions: ScoringDimension[];
  product_packages: ProductPackage[];
}
