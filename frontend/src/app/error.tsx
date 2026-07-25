"use client";

import { ErrorState } from "@/components/feedback/error-state";

type RootErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function RootError({ error, reset }: RootErrorProps) {
  void error;

  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-lg">
        <ErrorState
          title="页面暂时不可用"
          message="页面遇到了问题，请稍后重试。"
          onRetry={reset}
        />
      </div>
    </main>
  );
}
