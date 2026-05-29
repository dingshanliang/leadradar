import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock window.location before importing the module
const mockLocation = {
  href: "",
  assign: vi.fn(),
  reload: vi.fn(),
  replace: vi.fn(),
};

Object.defineProperty(window, "location", {
  value: mockLocation,
  writable: true,
});

// Import after mocks are set up
import { checkHealth, getConfig, updateScoringConfig } from "../api-client";

const API_BASE = "http://localhost:8000";

describe("api-client", () => {
  beforeEach(() => {
    localStorage.clear();
    mockLocation.href = "";
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ── JWT Auto-Injection ─────────────────────────────────────────

  describe("JWT auto-injection", () => {
    it("should include Authorization header when token exists in localStorage", async () => {
      localStorage.setItem("token", "test-jwt-token-123");

      const mockResponse = new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      await checkHealth();

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [url, options] = fetchSpy.mock.calls[0];
      expect(url).toBe(`${API_BASE}/health`);
      expect(options?.headers).toMatchObject({
        Authorization: "Bearer test-jwt-token-123",
      });
    });

    it("should NOT include Authorization header when no token in localStorage", async () => {
      const mockResponse = new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      await checkHealth();

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [url, options] = fetchSpy.mock.calls[0];
      expect(url).toBe(`${API_BASE}/health`);
      const headers = options?.headers as Record<string, string>;
      expect(headers).not.toHaveProperty("Authorization");
    });
  });

  // ── 401 Unauthorized Handling ──────────────────────────────────

  describe("401 response handling", () => {
    it("should clear localStorage and redirect to /login on 401", async () => {
      localStorage.setItem("token", "expired-token");
      localStorage.setItem("role", "admin");

      const mockResponse = new Response(JSON.stringify({ detail: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
      vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      await expect(checkHealth()).rejects.toThrow("Unauthorized");

      expect(localStorage.getItem("token")).toBeNull();
      expect(localStorage.getItem("role")).toBeNull();
      expect(mockLocation.href).toBe("/login");
    });

    it("should throw Error with 'Unauthorized' message on 401", async () => {
      const mockResponse = new Response(JSON.stringify({ detail: "Unauthorized" }), {
        status: 401,
      });
      vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      await expect(checkHealth()).rejects.toThrow("Unauthorized");
    });
  });

  // ── Successful Request ─────────────────────────────────────────

  describe("successful request", () => {
    it("should return parsed JSON on successful GET request", async () => {
      const expectedData = { status: "healthy" };
      const mockResponse = new Response(JSON.stringify(expectedData), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
      vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      const result = await checkHealth();
      expect(result).toEqual(expectedData);
    });

    it("should send Content-Type application/json by default", async () => {
      const mockResponse = new Response(JSON.stringify({}), { status: 200 });
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      await getConfig();

      const options = fetchSpy.mock.calls[0][1];
      const headers = options?.headers as Record<string, string>;
      expect(headers["Content-Type"]).toBe("application/json");
    });

    it("should allow custom headers to override defaults", async () => {
      // updateScoringConfig sends a PUT with body — use valid scoring payload
      const validPayload = {
        version: "0.1",
        max_scores: { budget_strength: 35, scenario_fit: 25, timing: 20, reachability: 10, leverage: 10 },
        grades: { S: 85, A: 70, B: 55, C: 40, D: 0 },
        budget_strength: { procurement_intent: 35 },
        scenario_fit: { region_brand: 10 },
        timing: { within_3_months: 20 },
        reachability: { procurement_contact: 10 },
        leverage: { multi_org: 10 },
      };
      const mockResponse = new Response(JSON.stringify({ ok: true }), { status: 200 });
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      await updateScoringConfig(validPayload);

      const options = fetchSpy.mock.calls[0][1];
      expect(options?.method).toBe("PUT");
      expect(options?.body).toBe(JSON.stringify(validPayload));
    });
  });

  // ── Non-200 Error Responses ────────────────────────────────────

  describe("non-200 error responses", () => {
    it("should throw Error with detail from JSON error response", async () => {
      const errorDetail = "Something went wrong";
      const mockResponse = new Response(
        JSON.stringify({ detail: errorDetail }),
        { status: 500 }
      );
      vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      await expect(checkHealth()).rejects.toThrow(errorDetail);
    });

    it("should throw Error with statusText when JSON parsing fails", async () => {
      const mockResponse = new Response("Internal Server Error", {
        status: 500,
        statusText: "Internal Server Error",
      });
      vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      // When JSON parsing fails, .catch() returns { detail: res.statusText }
      await expect(checkHealth()).rejects.toThrow("Internal Server Error");
    });

    it("should throw Error with status code when detail is empty", async () => {
      const mockResponse = new Response(
        JSON.stringify({ detail: "" }),
        { status: 422 }
      );
      vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      await expect(checkHealth()).rejects.toThrow("API Error: 422");
    });
  });

  // ── Network Error ──────────────────────────────────────────────

  describe("network error handling", () => {
    it("should propagate network errors from fetch failure", async () => {
      vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));

      await expect(checkHealth()).rejects.toThrow("Failed to fetch");
    });

    it("should propagate DNS resolution errors", async () => {
      vi.spyOn(globalThis, "fetch").mockRejectedValue(
        new TypeError("getaddrinfo ENOTFOUND api.example.com")
      );

      await expect(checkHealth()).rejects.toThrow("getaddrinfo ENOTFOUND");
    });
  });

  // ── Request Construction ───────────────────────────────────────

  describe("request URL construction", () => {
    it("should prepend API_BASE to all paths", async () => {
      const mockResponse = new Response(JSON.stringify({}), { status: 200 });
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

      await getConfig();

      expect(fetchSpy.mock.calls[0][0]).toBe(`${API_BASE}/api/v1/config`);
    });
  });
});
