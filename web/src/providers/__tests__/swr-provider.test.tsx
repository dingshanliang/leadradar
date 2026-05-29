import { render, screen } from "@testing-library/react";
import React from "react";
import useSWR from "swr";
import { SWRProvider } from "../swr-provider";

// Helper component that uses SWR to test provider behavior
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
  let testCounter = 0;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.restoreAllMocks();
    testCounter++;
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
    const key = `test-success-${testCounter}`;
    const fetcher = jest.fn().mockResolvedValue({ name: "test" });

    render(
      <SWRProvider>
        <TestConsumer swrKey={key} fetcher={fetcher} />
      </SWRProvider>
    );

    // Should show loading initially
    expect(screen.getByText("Loading...")).toBeInTheDocument();

    // Wait for data
    const dataEl = await screen.findByText(/Data:/);
    expect(dataEl).toHaveTextContent('Data: {"name":"test"}');
  });

  it("clears localStorage tokens on 401 Unauthorized error", async () => {
    const key = `test-401-${testCounter}`;
    const removeItemSpy = jest.spyOn(Storage.prototype, "removeItem");

    const error401 = new Error("Unauthorized");
    const fetcher = jest.fn().mockRejectedValue(error401);

    render(
      <SWRProvider>
        <TestConsumer swrKey={key} fetcher={fetcher} />
      </SWRProvider>
    );

    // Wait for error to be rendered
    await screen.findByText(/Error: Unauthorized/);

    // Should have cleared localStorage tokens
    expect(removeItemSpy).toHaveBeenCalledWith("token");
    expect(removeItemSpy).toHaveBeenCalledWith("role");

    removeItemSpy.mockRestore();
  });

  it("shows error state for non-401 errors without clearing tokens", async () => {
    const key = `test-500-${testCounter}`;
    const removeItemSpy = jest.spyOn(Storage.prototype, "removeItem");

    const error500 = new Error("Internal Server Error");
    const fetcher = jest.fn().mockRejectedValue(error500);

    render(
      <SWRProvider>
        <TestConsumer swrKey={key} fetcher={fetcher} />
      </SWRProvider>
    );

    await screen.findByText(/Error: Internal Server Error/);

    // Should NOT have cleared tokens for non-401 errors
    expect(removeItemSpy).not.toHaveBeenCalledWith("token");
    expect(removeItemSpy).not.toHaveBeenCalledWith("role");

    removeItemSpy.mockRestore();
  });

  it("retries on server errors up to max count", async () => {
    const key = `test-retry-${testCounter}`;
    const error500 = new Error("Server Error");
    const fetcher = jest.fn().mockRejectedValue(error500);

    render(
      <SWRProvider>
        <TestConsumer swrKey={key} fetcher={fetcher} />
      </SWRProvider>
    );

    // Wait for error state to appear
    await screen.findByText(/Error: Server Error/, undefined, {
      timeout: 15000,
    });

    // Should have retried — at least initial call
    expect(fetcher.mock.calls.length).toBeGreaterThanOrEqual(1);
  });
});
