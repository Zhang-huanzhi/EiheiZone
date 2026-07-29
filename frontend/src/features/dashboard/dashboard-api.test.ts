import { afterEach, describe, expect, it, vi } from "vitest";

import { getDashboard } from "@/features/dashboard/dashboard-api";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));

const mockedApiRequest = vi.mocked(apiRequest);

afterEach(() => vi.clearAllMocks());

describe("Dashboard API", () => {
  it("uses the single authenticated dashboard path and forwards options", async () => {
    mockedApiRequest.mockResolvedValue({});
    const options = { cache: "no-store" as const, headers: { Cookie: "session" } };

    await getDashboard(options);

    expect(mockedApiRequest).toHaveBeenCalledWith("/dashboard", options);
  });
});
