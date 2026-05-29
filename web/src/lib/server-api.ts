import type { Stats } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Server-side fetch helper for calling the backend API from Server Components.
 * Forwards cookies from the incoming request for authentication.
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
