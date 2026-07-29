import { getCsrfToken } from "@/features/auth/auth-api";
import type {
  ExpenditureCreateInput,
  ExpenditureListParams,
  ExpenditurePage,
  ExpenditureRecord,
  ExpenditureUpdateInput,
} from "@/features/expenditures/expenditure-types";
import { apiRequest } from "@/lib/api/client";

function withPagination(path: string, params: ExpenditureListParams = {}): string {
  const searchParams = new URLSearchParams();
  if (params.offset !== undefined) {
    searchParams.set("offset", String(params.offset));
  }
  if (params.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }
  const query = searchParams.toString();
  return query ? `${path}?${query}` : path;
}

export function getExpenditures(
  params: ExpenditureListParams = {},
  options: RequestInit = {},
): Promise<ExpenditurePage> {
  return apiRequest<ExpenditurePage>(withPagination("/expenditures", params), options);
}

export function getExpenditure(
  expenditureId: string,
  options: RequestInit = {},
): Promise<ExpenditureRecord> {
  return apiRequest<ExpenditureRecord>(`/expenditures/${expenditureId}`, options);
}

export async function createExpenditure(
  input: ExpenditureCreateInput,
): Promise<ExpenditureRecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<ExpenditureRecord>("/expenditures", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(input),
  });
}

export async function updateExpenditure(
  expenditureId: string,
  input: ExpenditureUpdateInput,
): Promise<ExpenditureRecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<ExpenditureRecord>(`/expenditures/${expenditureId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(input),
  });
}

export async function deleteExpenditure(expenditureId: string): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiRequest<void>(`/expenditures/${expenditureId}`, {
    method: "DELETE",
    headers: { "X-CSRF-Token": csrfToken },
  });
}
