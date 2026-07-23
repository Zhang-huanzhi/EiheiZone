"use client";

import { ErrorState } from "@/components/feedback/error-state";

type PublicErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function PublicError({ error, reset }: PublicErrorProps) {
  void error;
  return <ErrorState onRetry={reset} />;
}
