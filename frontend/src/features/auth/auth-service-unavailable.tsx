"use client";

import { useRouter } from "next/navigation";

import { ErrorState } from "@/components/feedback/error-state";

type AuthServiceUnavailableProps = {
  requestId?: string | null;
};

export function AuthServiceUnavailable({
  requestId,
}: AuthServiceUnavailableProps) {
  const router = useRouter();

  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-lg">
        <ErrorState
          title="服务暂时不可用"
          message="暂时无法确认登录状态，请稍后重试。"
          requestId={requestId}
          onRetry={() => router.refresh()}
        />
      </div>
    </main>
  );
}
