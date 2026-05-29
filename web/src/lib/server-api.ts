import type { Stats } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Server-side fetch helper for calling the backend API from Server Components.
 * NOTE: Currently no auth — only safe for public endpoints (e.g. /api/v1/stats).
 * When auth is required, switch to httpOnly cookies or make the page a Client Component.
 */
async function serverFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

export async function getServerStats(): Promise<Stats> {
  return serverFetch<Stats>("/api/v1/stats");
}
