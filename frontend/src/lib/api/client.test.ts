import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError, apiRequest } from "@/lib/api/client";
import type { ApiErrorResponse, HealthResponse } from "@/lib/api/types";

const validationError: ApiErrorResponse = {
  error: {
    code: "VALIDATION_ERROR",
    message: "Request fields are invalid",
    field_errors: [
      {
        field: "query.limit",
        message: "Input should be less than or equal to 100",
        type: "less_than_equal",
      },
    ],
    request_id: "request-422",
  },
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("returns parsed JSON from a successful response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiRequest<HealthResponse>("/health")).resolves.toEqual({
      status: "ok",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/health",
      expect.objectContaining({
        credentials: "include",
        headers: expect.objectContaining({ Accept: "application/json" }),
      }),
    );
  });

  it("keeps structured backend validation errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(validationError), { status: 422 }),
      ),
    );

    await expect(apiRequest("/items?limit=101")).rejects.toMatchObject({
      status: 422,
      code: "VALIDATION_ERROR",
      fieldErrors: validationError.error.field_errors,
      requestId: "request-422",
    } satisfies Partial<ApiRequestError>);
  });

  it("returns a safe error for a non-JSON failure response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("Internal implementation detail", {
          headers: { "X-Request-ID": "request-500" },
          status: 500,
        }),
      ),
    );

    await expect(apiRequest("/health")).rejects.toMatchObject({
      status: 500,
      code: "HTTP_ERROR",
      message: "The request could not be completed.",
      requestId: "request-500",
    } satisfies Partial<ApiRequestError>);
  });

  it("returns a safe error when the service cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(apiRequest("/health")).rejects.toMatchObject({
      status: null,
      code: "NETWORK_ERROR",
      message: "Unable to reach the service.",
    } satisfies Partial<ApiRequestError>);
  });
});
