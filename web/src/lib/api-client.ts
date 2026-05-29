import type {
  AppConfig,
  Document,
  FollowUpCreate,
  FollowUpOut,
  LeadDetail,
  LeadFilters,
  LeadListItem,
  Meta,
  Source,
  Stats,
} from "./types";
import {
  leadStatusUpdateSchema,
  followUpCreateSchema,
  scoringRulesUpdateSchema,
} from "./schemas";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

function buildAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

function handleUnauthorized(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  window.location.href = "/login";
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const { headers: customHeaders, ...rest } = options ?? {};
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...buildAuthHeaders(),
      ...customHeaders,
    },
  });
  if (res.status === 401) {
    handleUnauthorized();
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }
  return res.json();
}

// ── Health ─────────────────────────────────────────────────────

export async function checkHealth(): Promise<{ status: string }> {
  return apiFetch("/health");
}

// ── Sources ────────────────────────────────────────────────────

export async function getConfig(): Promise<AppConfig> {
  return apiFetch("/api/v1/config");
}

export async function getScoringConfig(): Promise<Record<string, unknown>> {
  return apiFetch("/api/v1/config/scoring");
}

export async function updateScoringConfig(
  payload: Record<string, unknown>
): Promise<{ ok: boolean }> {
  const parsed = scoringRulesUpdateSchema.safeParse(payload);
  if (!parsed.success) {
    throw new Error(
      `校验失败: ${parsed.error.issues.map((i) => i.message).join(", ")}`
    );
  }
  return apiFetch("/api/v1/config/scoring", {
    method: "PUT",
    body: JSON.stringify(parsed.data),
  });
}

export async function listSources(): Promise<Source[]> {
  return apiFetch("/api/v1/sources");
}

// ── Documents ──────────────────────────────────────────────────

export async function listDocuments(): Promise<Document[]> {
  return apiFetch("/api/v1/documents");
}

// ── Leads ──────────────────────────────────────────────────────

export async function getStats(): Promise<Stats> {
  return apiFetch("/api/v1/stats");
}

export async function getMeta(): Promise<Meta> {
  return apiFetch("/api/v1/meta");
}

export async function listLeads(filters?: LeadFilters): Promise<LeadListItem[]> {
  const params = new URLSearchParams();
  if (filters?.grade) params.set("grade", filters.grade);
  if (filters?.status) params.set("status", filters.status);
  if (filters?.signal_type) params.set("signal_type", filters.signal_type);
  params.set("limit", String(filters?.limit ?? 50));
  params.set("offset", String(filters?.offset ?? 0));
  return apiFetch(`/api/v1/leads?${params.toString()}`);
}

export async function getLeadDetail(leadId: string): Promise<LeadDetail> {
  return apiFetch(`/api/v1/leads/${leadId}`);
}

export async function updateLeadStatus(
  leadId: string,
  status: string
): Promise<void> {
  const parsed = leadStatusUpdateSchema.safeParse({ status });
  if (!parsed.success) {
    throw new Error(
      `无效的状态值: ${status}`
    );
  }
  await apiFetch(`/api/v1/leads/${leadId}/status`, {
    method: "PATCH",
    body: JSON.stringify(parsed.data),
  });
}

// ── Export ─────────────────────────────────────────────────────

export async function exportLeads(
  format: "csv" | "xlsx",
  grade?: string
): Promise<void> {
  const params = new URLSearchParams({ format });
  if (grade) params.set("grade", grade);
  const res = await fetch(`${API_BASE}/api/v1/leads/export?${params}`, {
    headers: buildAuthHeaders(),
  });
  if (res.status === 401) {
    handleUnauthorized();
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `leads.${format === "xlsx" ? "xlsx" : "csv"}`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Weekly Report ──────────────────────────────────────────────

export async function getWeeklyReport(): Promise<Record<string, unknown>> {
  return apiFetch("/api/v1/weekly-report");
}

// ── Follow-ups ─────────────────────────────────────────────────

export async function createFollowUp(
  leadId: string,
  data: FollowUpCreate
): Promise<FollowUpOut> {
  const parsed = followUpCreateSchema.safeParse(data);
  if (!parsed.success) {
    throw new Error(
      `校验失败: ${parsed.error.issues.map((i) => i.message).join(", ")}`
    );
  }
  return apiFetch(`/api/v1/leads/${leadId}/follow-ups`, {
    method: "POST",
    body: JSON.stringify(parsed.data),
  });
}

export async function listFollowUps(leadId: string): Promise<FollowUpOut[]> {
  return apiFetch(`/api/v1/leads/${leadId}/follow-ups`);
}
