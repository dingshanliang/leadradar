import type { Stats } from "./types";
import { fetchJson } from "./fetch-utils";

/**
 * Server-side fetch helper for calling the backend API from Server Components.
 * NOTE: Currently no auth — only safe for public endpoints (e.g. /api/v1/stats).
 * When auth is required, switch to httpOnly cookies or make the page a Client Component.
 */
export async function getServerStats(): Promise<Stats> {
  return fetchJson<Stats>("/api/v1/stats");
}
