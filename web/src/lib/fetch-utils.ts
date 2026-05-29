/** Shared fetch primitives used by both client-side and server-side API layers. */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Low-level JSON fetch helper.
 *
 * - Injects the base URL
 * - Adds ``Content-Type: application/json``
 * - Adds ``Authorization`` header when ``authToken`` is provided
 * - Throws ``ApiError`` on non-2xx responses (body parsed for ``detail``)
 */
export async function fetchJson<T>(
  path: string,
  init?: RequestInit & { authToken?: string | null }
): Promise<T> {
  const { authToken, ...rest } = init ?? {};
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(rest.headers as Record<string, string> | undefined),
  };
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}
