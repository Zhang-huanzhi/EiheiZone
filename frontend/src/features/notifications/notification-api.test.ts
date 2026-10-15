import { afterEach, describe, expect, it, vi } from "vitest";

import { getCsrfToken } from "@/features/auth/auth-api";
import {
  createWeChatBindingCode,
  getWeChatBindingStatus,
  unbindWeChat,
} from "@/features/notifications/notification-api";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/features/auth/auth-api", () => ({ getCsrfToken: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));

const mockedGetCsrfToken = vi.mocked(getCsrfToken);
const mockedApiRequest = vi.mocked(apiRequest);

afterEach(() => {
  vi.clearAllMocks();
});

describe("Notification API", () => {
  it("reads WeChat binding status without CSRF", async () => {
    mockedApiRequest.mockResolvedValue({ bound: false, bound_at: null });

    const status = await getWeChatBindingStatus();

    expect(status).toEqual({ bound: false, bound_at: null });
    expect(mockedApiRequest).toHaveBeenCalledWith("/notifications/wechat");
  });

  it("attaches a CSRF token when generating a binding code and unbinding", async () => {
    mockedGetCsrfToken.mockResolvedValue("csrf-token");
    mockedApiRequest
      .mockResolvedValueOnce({ code: "ABCD1234", expires_at: "2026-10-15T12:00:00Z" })
      .mockResolvedValueOnce(undefined);

    const codeResult = await createWeChatBindingCode();
    await unbindWeChat();

    expect(codeResult.code).toBe("ABCD1234");
    expect(mockedGetCsrfToken).toHaveBeenCalledTimes(2);
    expect(mockedApiRequest).toHaveBeenNthCalledWith(1, "/notifications/wechat/code", {
      method: "POST",
      headers: { "X-CSRF-Token": "csrf-token" },
    });
    expect(mockedApiRequest).toHaveBeenNthCalledWith(2, "/notifications/wechat", {
      method: "DELETE",
      headers: { "X-CSRF-Token": "csrf-token" },
    });
  });
});
