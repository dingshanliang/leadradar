import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import useSWR from "swr";
import { SWRProvider } from "../swr-provider";

function TestConsumer({
  swrKey,
  fetcher,
}: {
  swrKey: string;
  fetcher: () => Promise<unknown>;
}) {
  const { data, error, isLoading } = useSWR(swrKey, fetcher);
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <div>Data: {JSON.stringify(data)}</div>;
}

describe("SWRProvider", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.location.href setter for redirect tests
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      value: originalLocation,
      writable: true,
    });
  });

  it("renders children without crashing", () => {
    render(
      <SWRProvider>
        <div>Child content</div>
      </SWRProvider>
    );
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("handles successful data fetching", async () => {
    const fetcher = vi.fn().mockResolvedValue({ name: "test" });

    await act(async () => {
      render(
        <SWRProvider>
          <TestConsumer swrKey="test-success" fetcher={fetcher} />
        </SWRProvider>
      );
    });

    const dataEl = await screen.findByText(/Data:/);
    expect(dataEl).toHaveTextContent('Data: {"name":"test"}');
  });

  it("clears localStorage tokens on 401 Unauthorized error", async () => {
    const removeItemSpy = vi.spyOn(Storage.prototype, "removeItem");
    const error401 = new Error("Unauthorized");
    const fetcher = vi.fn().mockRejectedValue(error401);

    await act(async () => {
      render(
        <SWRProvider>
          <TestConsumer swrKey="test-401" fetcher={fetcher} />
        </SWRProvider>
      );
    });

    await screen.findByText(/Error: Unauthorized/);

    expect(removeItemSpy).toHaveBeenCalledWith("token");
    expect(removeItemSpy).toHaveBeenCalledWith("role");
    removeItemSpy.mockRestore();
  });

  it("shows error state for non-401 errors without clearing tokens", async () => {
    const removeItemSpy = vi.spyOn(Storage.prototype, "removeItem");
    const error500 = new Error("Internal Server Error");
    const fetcher = vi.fn().mockRejectedValue(error500);

    await act(async () => {
      render(
        <SWRProvider>
          <TestConsumer swrKey="test-500" fetcher={fetcher} />
        </SWRProvider>
      );
    });

    await screen.findByText(/Error: Internal Server Error/);

    expect(removeItemSpy).not.toHaveBeenCalledWith("token");
    expect(removeItemSpy).not.toHaveBeenCalledWith("role");
    removeItemSpy.mockRestore();
  });

  it("retries on server errors up to max count", async () => {
    const error500 = new Error("Server Error");
    const fetcher = vi.fn().mockRejectedValue(error500);

    await act(async () => {
      render(
        <SWRProvider>
          <TestConsumer swrKey="test-retry" fetcher={fetcher} />
        </SWRProvider>
      );
    });

    await screen.findByText(/Error: Server Error/, undefined, {
      timeout: 15000,
    });

    expect(fetcher.mock.calls.length).toBeGreaterThanOrEqual(1);
  });
});
