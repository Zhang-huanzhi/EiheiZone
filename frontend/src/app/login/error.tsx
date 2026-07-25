"use client";

import { ErrorState } from "@/components/feedback/error-state";

type LoginErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function LoginError({ error, reset }: LoginErrorProps) {
  void error;
  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <ErrorState message="暂时无法确认登录状态。" onRetry={reset} />
    </main>
  );
}
