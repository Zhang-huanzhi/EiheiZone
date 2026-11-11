import { getCsrfToken } from "@/features/auth/auth-api";
import type {
  QAAnswerInput,
  QACreateInput,
  QAListParams,
  QAPage,
  QARecord,
} from "@/features/qas/qa-types";
import { apiRequest } from "@/lib/api/client";

function withPagination(path: string, params: QAListParams = {}): string {
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

export function getQAs(
  params: QAListParams = {},
  options: RequestInit = {},
): Promise<QAPage> {
  return apiRequest<QAPage>(withPagination("/qas", params), options);
}

export function getQA(qaId: string, options: RequestInit = {}): Promise<QARecord> {
  return apiRequest<QARecord>(`/qas/${qaId}`, options);
}

export async function createQuestion(input: QACreateInput): Promise<QARecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<QARecord>("/qas", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify({
      question: input.question,
      is_proxy: input.is_proxy ?? false,
    }),
  });
}

export async function addAnswer(qaId: string, input: QAAnswerInput): Promise<QARecord> {
  const csrfToken = await getCsrfToken();
  const content = input.content ?? input.answer ?? "";
  return apiRequest<QARecord>(`/qas/${qaId}/answers`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify({
      content,
      is_proxy: input.is_proxy ?? false,
    }),
  });
}

export async function upsertAnswer(qaId: string, input: QAAnswerInput): Promise<QARecord> {
  const csrfToken = await getCsrfToken();
  const answer = input.answer ?? input.content ?? "";
  return apiRequest<QARecord>(`/qas/${qaId}/answer`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify({
      answer,
      is_proxy: input.is_proxy ?? false,
    }),
  });
}

export async function updateAnswer(
  qaId: string,
  answerId: string,
  input: QAAnswerInput,
): Promise<QARecord> {
  const csrfToken = await getCsrfToken();
  const content = input.content ?? input.answer ?? "";
  return apiRequest<QARecord>(`/qas/${qaId}/answers/${answerId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify({
      content,
      is_proxy: input.is_proxy ?? false,
    }),
  });
}

export async function deleteAnswer(qaId: string, answerId: string): Promise<QARecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<QARecord>(`/qas/${qaId}/answers/${answerId}`, {
    method: "DELETE",
    headers: {
      "X-CSRF-Token": csrfToken,
    },
  });
}
