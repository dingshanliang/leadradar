'use client';

import { useEffect } from 'react';
import { ErrorState } from '@/components/ui/error-state';

export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error('[LeadRadar] 页面渲染错误:', error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="text-center max-w-md">
        <ErrorState onRetry={() => unstable_retry()} />
        {error.digest && (
          <p className="text-xs text-muted mt-2">
            错误编号: {error.digest}
          </p>
        )}
      </div>
    </div>
  );
}
