import type {
  Document,
  FollowUpCreate,
  FollowUpOut,
  LeadDetail,
  LeadFilters,
  LeadListItem,
  Source,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const { headers: customHeaders, ...rest } = options ?? {};
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: { "Content-Type": "application/json", ...customHeaders },
  });
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

export async function listSources(): Promise<Source[]> {
  return apiFetch("/api/v1/sources");
}

// ── Documents ──────────────────────────────────────────────────

export async function listDocuments(): Promise<Document[]> {
  return apiFetch("/api/v1/documents");
}

// ── Leads ──────────────────────────────────────────────────────

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
  await apiFetch(`/api/v1/leads/${leadId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

// ── Export ─────────────────────────────────────────────────────

export async function exportLeads(
  format: "csv" | "xlsx",
  grade?: string
): Promise<void> {
  const params = new URLSearchParams({ format });
  if (grade) params.set("grade", grade);
  const res = await fetch(`${API_BASE}/api/v1/leads/export?${params}`);
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `leads.${format === "xlsx" ? "xlsx" : "csv"}`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Follow-ups ─────────────────────────────────────────────────

export async function createFollowUp(
  leadId: string,
  data: FollowUpCreate
): Promise<FollowUpOut> {
  return apiFetch(`/api/v1/leads/${leadId}/follow-ups`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listFollowUps(leadId: string): Promise<FollowUpOut[]> {
  return apiFetch(`/api/v1/leads/${leadId}/follow-ups`);
}
