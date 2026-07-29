import { afterEach, describe, expect, it, vi } from "vitest";

import { getCsrfToken } from "@/features/auth/auth-api";
import {
  createExpenditure,
  deleteExpenditure,
  getExpenditure,
  getExpenditures,
  updateExpenditure,
} from "@/features/expenditures/expenditure-api";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/features/auth/auth-api", () => ({ getCsrfToken: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));

const mockedGetCsrfToken = vi.mocked(getCsrfToken);
const mockedApiRequest = vi.mocked(apiRequest);

afterEach(() => vi.clearAllMocks());

describe("Expenditure API", () => {
  it("uses only authenticated read paths", async () => {
    mockedApiRequest.mockResolvedValue({});
    await getExpenditures({ offset: 20, limit: 5 });
    await getExpenditure("expenditure-id");

    expect(mockedApiRequest).toHaveBeenNthCalledWith(1, "/expenditures?offset=20&limit=5", {});
    expect(mockedApiRequest).toHaveBeenNthCalledWith(2, "/expenditures/expenditure-id", {});
  });

  it("keeps amount as a string and gets CSRF for every mutation", async () => {
    mockedGetCsrfToken.mockResolvedValue("csrf-token");
    mockedApiRequest.mockResolvedValue({});
    const input = {
      spent_on: "2026-07-28",
      amount: "1234.5600",
      currency: "CNY",
      category: "Equipment",
      description: "Test equipment purchase",
    };

    await createExpenditure(input);
    await updateExpenditure("expenditure-id", { amount: "10.2500" });
    await deleteExpenditure("expenditure-id");

    expect(mockedGetCsrfToken).toHaveBeenCalledTimes(3);
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      1,
      "/expenditures",
      expect.objectContaining({ method: "POST", body: JSON.stringify(input) }),
    );
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      2,
      "/expenditures/expenditure-id",
      expect.objectContaining({ method: "PATCH", body: JSON.stringify({ amount: "10.2500" }) }),
    );
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      3,
      "/expenditures/expenditure-id",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});
