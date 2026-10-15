import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createWeChatBindingCode,
  getWeChatBindingStatus,
  unbindWeChat,
} from "@/features/notifications/notification-api";
import { NotificationSettings } from "@/features/notifications/notification-settings";

vi.mock("@/features/notifications/notification-api", () => ({
  getWeChatBindingStatus: vi.fn(),
  createWeChatBindingCode: vi.fn(),
  unbindWeChat: vi.fn(),
}));

const mockedGetStatus = vi.mocked(getWeChatBindingStatus);
const mockedCreateCode = vi.mocked(createWeChatBindingCode);
const mockedUnbind = vi.mocked(unbindWeChat);

afterEach(() => {
  vi.clearAllMocks();
});

describe("NotificationSettings", () => {
  it("displays unbound status, generates a one-time binding code, and copies it", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });

    mockedGetStatus.mockResolvedValue({ bound: false, bound_at: null });
    mockedCreateCode.mockResolvedValue({
      code: "WXYZ5678",
      expires_at: "2026-10-15T10:30:00Z",
    });

    render(<NotificationSettings />);

    expect(await screen.findByText("当前尚未绑定微信。")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "生成绑定码" }));

    expect(await screen.findByText("WXYZ5678")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "请关注测试号后，把绑定码发送给测试号。绑定码 10 分钟内有效。",
    );

    await user.click(screen.getByRole("button", { name: "复制绑定码" }));
    expect(writeText).toHaveBeenCalledWith("WXYZ5678");
    expect(screen.getByRole("status")).toHaveTextContent("绑定码已复制。");
  });

  it("displays bound status and allows unbinding WeChat", async () => {
    const user = userEvent.setup();
    mockedGetStatus.mockResolvedValue({
      bound: true,
      bound_at: "2026-10-15T10:00:00Z",
    });
    mockedUnbind.mockResolvedValue(undefined);

    render(<NotificationSettings />);

    expect(
      await screen.findByText("已绑定微信，可以接收通知。"),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "解除绑定" }));

    await waitFor(() => {
      expect(mockedUnbind).toHaveBeenCalledTimes(1);
    });
    expect(screen.getByText("当前尚未绑定微信。")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("微信绑定已解除。");
  });

  it("surfaces errors when status loading or code generation fails", async () => {
    const user = userEvent.setup();
    mockedGetStatus.mockRejectedValue(new Error("Network error"));
    mockedCreateCode.mockRejectedValue(new Error("Code error"));

    render(<NotificationSettings />);

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent("暂时无法读取微信绑定状态。");

    await user.click(screen.getByRole("button", { name: "生成绑定码" }));

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent("暂时无法生成绑定码，请重试。");
  });
});
