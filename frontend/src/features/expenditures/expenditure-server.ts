import "server-only";

import { cookies } from "next/headers";

import { getExpenditure, getExpenditures } from "@/features/expenditures/expenditure-api";
import type {
  ExpenditureListParams,
  ExpenditurePage,
  ExpenditureRecord,
} from "@/features/expenditures/expenditure-types";

const NO_STORE = { cache: "no-store" } as const;

async function authenticatedOptions(): Promise<RequestInit> {
  const cookieHeader = (await cookies()).toString();
  return {
    ...NO_STORE,
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  };
}

export async function getServerExpenditures(
  params: ExpenditureListParams = {},
): Promise<ExpenditurePage> {
  return getExpenditures(params, await authenticatedOptions());
}

export async function getServerExpenditure(expenditureId: string): Promise<ExpenditureRecord> {
  return getExpenditure(expenditureId, await authenticatedOptions());
}
