import "server-only";

import { cookies } from "next/headers";

import { getQA, getQAs } from "@/features/qas/qa-api";
import type { QAListParams, QAPage, QARecord } from "@/features/qas/qa-types";

const NO_STORE = { cache: "no-store" } as const;

async function authenticatedOptions(): Promise<RequestInit> {
  const cookieHeader = (await cookies()).toString();
  return {
    ...NO_STORE,
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  };
}

export async function getServerQAs(params: QAListParams = {}): Promise<QAPage> {
  return getQAs(params, await authenticatedOptions());
}

export async function getServerQA(qaId: string): Promise<QARecord> {
  return getQA(qaId, await authenticatedOptions());
}
