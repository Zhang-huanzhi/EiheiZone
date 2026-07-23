"use client";

import { Button } from "@/components/ui/button";

type ErrorStateProps = {
  message?: string;
  requestId?: string | null;
  onRetry?: () => void;
};

export function ErrorState({
  message = "暂时无法加载内容，请稍后重试。",
  requestId,
  onRetry,
}: ErrorStateProps) {
  return (
    <section className="space-y-3" role="alert">
      <div className="space-y-1">
        <h2 className="text-lg font-medium">无法加载内容</h2>
        <p className="text-muted-foreground">{message}</p>
        {requestId ? (
          <p className="text-sm text-muted-foreground">请求编号：{requestId}</p>
        ) : null}
      </div>
      {onRetry ? <Button onClick={onRetry}>重试</Button> : null}
    </section>
  );
}
