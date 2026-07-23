import type { ApiErrorDetail, ApiErrorResponse, FieldError } from "@/lib/api/types";

const API_PREFIX = "/api/v1";
const BACKEND_API_ORIGIN =
  process.env.BACKEND_API_ORIGIN ?? "http://127.0.0.1:8000";

type ApiRequestErrorOptions = {
  status: number | null;
  code: string;
  message: string;
  fieldErrors?: FieldError[];
  requestId?: string | null;
};

export class ApiRequestError extends Error {
  readonly status: number | null;
  readonly code: string;
  readonly fieldErrors: FieldError[];
  readonly requestId: string | null;

  constructor({
    status,
    code,
    message,
    fieldErrors = [],
    requestId = null,
  }: ApiRequestErrorOptions) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors;
    this.requestId = requestId;
  }
}

function getApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const apiPath = `${API_PREFIX}${normalizedPath}`;

  return typeof window === "undefined"
    ? `${BACKEND_API_ORIGIN}${apiPath}`
    : apiPath;
}

function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  if (typeof value !== "object" || value === null || !("error" in value)) {
    return false;
  }

  const error = value.error;
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof error.code === "string" &&
    "message" in error &&
    typeof error.message === "string" &&
    "field_errors" in error &&
    Array.isArray(error.field_errors) &&
    "request_id" in error &&
    typeof error.request_id === "string"
  );
}

async function readResponseBody(response: Response): Promise<unknown> {
  const body = await response.text();
  if (!body) {
    return undefined;
  }

  try {
    return JSON.parse(body) as unknown;
  } catch {
    return undefined;
  }
}

function toApiRequestError(
  status: number,
  payload: unknown,
  requestId: string | null,
): ApiRequestError {
  if (isApiErrorResponse(payload)) {
    const error: ApiErrorDetail = payload.error;
    return new ApiRequestError({
      status,
      code: error.code,
      message: error.message,
      fieldErrors: error.field_errors,
      requestId: error.request_id,
    });
  }

  return new ApiRequestError({
    status,
    code: "HTTP_ERROR",
    message: "The request could not be completed.",
    requestId,
  });
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(getApiUrl(path), {
      ...options,
      credentials: "include",
      headers: {
        Accept: "application/json",
        ...options.headers,
      },
    });
  } catch {
    throw new ApiRequestError({
      status: null,
      code: "NETWORK_ERROR",
      message: "Unable to reach the service.",
    });
  }

  const payload = await readResponseBody(response);

  if (!response.ok) {
    throw toApiRequestError(
      response.status,
      payload,
      response.headers.get("X-Request-ID"),
    );
  }

  return payload as T;
}
