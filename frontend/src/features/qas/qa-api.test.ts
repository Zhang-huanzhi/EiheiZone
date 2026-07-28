import { afterEach, describe, expect, it, vi } from "vitest";

import { getCsrfToken } from "@/features/auth/auth-api";
import { createQuestion, getQA, getQAs, upsertAnswer } from "@/features/qas/qa-api";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/features/auth/auth-api", () => ({ getCsrfToken: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));

const mockedGetCsrfToken = vi.mocked(getCsrfToken);
const mockedApiRequest = vi.mocked(apiRequest);

afterEach(() => {
  vi.clearAllMocks();
});

describe("QA API", () => {
  it("uses only authenticated QA read paths", async () => {
    mockedApiRequest.mockResolvedValue({});

    await getQAs({ offset: 20, limit: 5 });
    await getQA("qa-id");

    expect(mockedApiRequest).toHaveBeenNthCalledWith(1, "/qas?offset=20&limit=5", {});
    expect(mockedApiRequest).toHaveBeenNthCalledWith(2, "/qas/qa-id", {});
  });

  it("gets CSRF before Family POST and Owner PUT mutations", async () => {
    mockedGetCsrfToken.mockResolvedValue("csrf-token");
    mockedApiRequest.mockResolvedValue({});

    await createQuestion({ question: "Question text" });
    await upsertAnswer("qa-id", { answer: "Answer text" });

    expect(mockedGetCsrfToken).toHaveBeenCalledTimes(2);
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      1,
      "/qas",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "Question text" }),
        headers: expect.objectContaining({ "X-CSRF-Token": "csrf-token" }),
      }),
    );
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      2,
      "/qas/qa-id/answer",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ answer: "Answer text" }),
        headers: expect.objectContaining({ "X-CSRF-Token": "csrf-token" }),
      }),
    );
  });
});
