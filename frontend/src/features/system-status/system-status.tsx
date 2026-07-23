"use client";

import { useEffect, useState } from "react";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { ApiRequestError, apiRequest } from "@/lib/api/client";
import type { HealthResponse } from "@/lib/api/types";

type SystemStatusState =
  | { kind: "loading" }
  | { kind: "success" }
  | { kind: "error"; error: ApiRequestError };

export function SystemStatus() {
  const [state, setState] = useState<SystemStatusState>({ kind: "loading" });
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    let isActive = true;

    async function checkHealth() {
      setState({ kind: "loading" });

      try {
        const response = await apiRequest<HealthResponse>("/health");
        if (response.status !== "ok") {
          throw new ApiRequestError({
            status: null,
            code: "INVALID_RESPONSE",
            message: "后端服务返回了无法识别的响应。",
          });
        }

        if (isActive) {
          setState({ kind: "success" });
        }
      } catch (error) {
        if (!isActive) {
          return;
        }

        setState({
          kind: "error",
          error:
            error instanceof ApiRequestError
              ? error
              : new ApiRequestError({
                  status: null,
                  code: "UNKNOWN_ERROR",
                  message: "暂时无法连接后端服务。",
                }),
        });
      }
    }

    void checkHealth();

    return () => {
      isActive = false;
    };
  }, [requestVersion]);

  if (state.kind === "loading") {
    return <LoadingState message="正在检查后端服务..." />;
  }

  if (state.kind === "error") {
    return (
      <ErrorState
        message={state.error.message}
        requestId={state.error.requestId}
        onRetry={() => setRequestVersion((version) => version + 1)}
      />
    );
  }

  return (
    <p aria-live="polite" className="text-sm text-emerald-700 dark:text-emerald-400">
      后端 API 可用
    </p>
  );
}
