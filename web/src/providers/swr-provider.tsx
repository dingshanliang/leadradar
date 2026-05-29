"use client";

import { SWRConfig } from "swr";

/**
 * Global SWR configuration provider.
 *
 * - Redirects to /login on 401 errors
 * - Logs non-401 errors for debugging
 * - Retries on network errors only (not 4xx client errors)
 */
export function SWRProvider({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        onError: (error: Error, key: string) => {
          // 401 — redirect to login (same logic as api-client handleUnauthorized)
          if (error.message === "Unauthorized") {
            if (typeof window !== "undefined") {
              localStorage.removeItem("token");
              localStorage.removeItem("role");
              window.location.href = "/login";
            }
            return;
          }

          // Log other errors for debugging
          if (process.env.NODE_ENV === "development") {
            console.error(`[SWR Error] key=${key}`, error.message);
          }
        },
        onErrorRetry: (
          error: Error,
          _key: string,
          _config: unknown,
          revalidate: (opts: { retryCount: number }) => void,
          { retryCount }: { retryCount: number }
        ) => {
          // Never retry on 4xx client errors (including 401, 403, 404)
          if (error.message === "Unauthorized") return;

          // Retry up to 3 times for network / server errors
          if (retryCount >= 3) return;

          // Exponential backoff: 1s, 2s, 4s
          const delay = Math.min(1000 * 2 ** retryCount, 10000);
          setTimeout(() => revalidate({ retryCount: retryCount + 1 }), delay);
        },
        errorRetryCount: 3,
        revalidateOnFocus: false,
      }}
    >
      {children}
    </SWRConfig>
  );
}
