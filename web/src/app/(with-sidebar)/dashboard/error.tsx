"use client";

import { ErrorState } from "@/components/ui/error-state";

export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  return <ErrorState onRetry={() => unstable_retry()} />;
}
