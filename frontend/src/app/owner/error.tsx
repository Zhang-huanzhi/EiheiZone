"use client";

import { ErrorState } from "@/components/feedback/error-state";

type OwnerErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function OwnerError({ error, reset }: OwnerErrorProps) {
  void error;
  return <ErrorState onRetry={reset} />;
}
