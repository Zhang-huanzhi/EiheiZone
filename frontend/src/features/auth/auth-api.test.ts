import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getCsrfToken,
  getCurrentUser,
  loginUser,
  logoutUser,
} from "@/features/auth/auth-api";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({
  apiRequest: vi.fn(),
}));

const mockedApiRequest = vi.mocked(apiRequest);

afterEach(() => {
  vi.clearAllMocks();
});

describe("auth API", () => {
  it("gets the CSRF token from the response body", async () => {
    mockedApiRequest.mockResolvedValue({ csrf_token: "csrf-token" });

    await expect(getCsrfToken()).resolves.toBe("csrf-token");
    expect(mockedApiRequest).toHaveBeenCalledWith("/auth/csrf");
  });

  it("sends credentials with the CSRF header", async () => {
    mockedApiRequest.mockResolvedValue({
      user: {
        id: "user-id",
        login_name: "family",
        display_name: "Family",
        role: "family",
      },
      csrf_token: "rotated-token",
    });

    await loginUser(
      { login_name: "family", password: "test-password" },
      "anonymous-token",
    );

    expect(mockedApiRequest).toHaveBeenCalledWith("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": "anonymous-token",
      },
      body: JSON.stringify({
        login_name: "family",
        password: "test-password",
      }),
    });
  });

  it("can forward server request options when loading the current user", async () => {
    mockedApiRequest.mockResolvedValue({ role: "owner" });

    await getCurrentUser({ headers: { Cookie: "pfp_session=session" } });

    expect(mockedApiRequest).toHaveBeenCalledWith("/auth/me", {
      headers: { Cookie: "pfp_session=session" },
    });
  });

  it("gets a fresh session-bound CSRF token before logout", async () => {
    mockedApiRequest
      .mockResolvedValueOnce({ csrf_token: "session-csrf-token" })
      .mockResolvedValueOnce(undefined);

    await logoutUser();

    expect(mockedApiRequest).toHaveBeenNthCalledWith(1, "/auth/csrf");
    expect(mockedApiRequest).toHaveBeenNthCalledWith(2, "/auth/logout", {
      method: "POST",
      headers: { "X-CSRF-Token": "session-csrf-token" },
    });
  });
});
