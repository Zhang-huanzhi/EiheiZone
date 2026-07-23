"use client";

import { ErrorState } from "@/components/feedback/error-state";

type FamilyErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function FamilyError({ error, reset }: FamilyErrorProps) {
  void error;
  return <ErrorState onRetry={reset} />;
}
