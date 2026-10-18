import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createWeChatBindingCode,
  getWeChatBindingStatus,
  unbindWeChat,
} from "@/features/notifications/notification-api";
import { NotificationSettings } from "@/features/notifications/notification-settings";
import { ApiRequestError } from "@/lib/api/client";

vi.mock("@/features/notifications/notification-api", () => ({
  getWeChatBindingStatus: vi.fn(),
  createWeChatBindingCode: vi.fn(),
  unbindWeChat: vi.fn(),
}));

const mockedGetStatus = vi.mocked(getWeChatBindingStatus);
const mockedCreateCode = vi.mocked(createWeChatBindingCode);
const mockedUnbind = vi.mocked(unbindWeChat);

afterEach(() => {
  vi.resetAllMocks();
  vi.useRealTimers();
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

    fireEvent.click(screen.getByRole("button", { name: "生成绑定码" }));

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
    expect(screen.getByRole("button", { name: "生成绑定码" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("微信绑定已解除。");
  });

  it("does not offer code generation while the bound status is loaded", async () => {
    mockedGetStatus.mockResolvedValue({
      bound: true,
      bound_at: "2026-10-15T10:00:00Z",
    });

    render(<NotificationSettings />);

    expect(await screen.findByText("已绑定微信，可以接收通知。")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "生成绑定码" })).not.toBeInTheDocument();
  });

  it("does not offer actions before the binding status is loaded", () => {
    mockedGetStatus.mockImplementation(() => new Promise(() => {}));

    render(<NotificationSettings />);

    expect(screen.getByText("正在读取微信绑定状态...")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "生成绑定码" })).not.toBeInTheDocument();
  });

  it("refreshes the status and clears the code after binding succeeds", async () => {
    vi.useFakeTimers();
    mockedGetStatus
      .mockResolvedValueOnce({ bound: false, bound_at: null })
      .mockResolvedValueOnce({ bound: true, bound_at: "2026-10-15T10:01:00Z" });
    mockedCreateCode.mockResolvedValue({
      code: "WXYZ5678",
      expires_at: "2026-10-15T10:30:00Z",
    });

    render(<NotificationSettings />);
    await act(async () => { await Promise.resolve(); });
    fireEvent.click(screen.getByRole("button", { name: "生成绑定码" }));
    await act(async () => { await Promise.resolve(); });
    expect(screen.getByText("WXYZ5678")).toBeInTheDocument();

    await act(async () => { await vi.advanceTimersByTimeAsync(5000); });

    expect(screen.getByText("微信绑定已完成。")).toBeInTheDocument();
    expect(screen.queryByText("WXYZ5678")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "生成绑定码" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "解除绑定" })).toBeInTheDocument();
  });

  it("surfaces errors when status loading or code generation fails", async () => {
    mockedGetStatus.mockRejectedValue(new Error("Network error"));

    render(<NotificationSettings />);

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent("暂时无法读取微信绑定状态。");
    expect(screen.queryByRole("button", { name: "生成绑定码" })).not.toBeInTheDocument();
  });

  it("surfaces errors when code generation fails", async () => {
    const user = userEvent.setup();
    mockedGetStatus.mockResolvedValue({ bound: false, bound_at: null });
    mockedCreateCode.mockRejectedValue(new Error("Code error"));

    render(<NotificationSettings />);

    await user.click(await screen.findByRole("button", { name: "生成绑定码" }));

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent("暂时无法生成绑定码，请重试。");
  });

  it("refreshes status when the API reports an already bound account", async () => {
    const user = userEvent.setup();
    mockedGetStatus
      .mockResolvedValueOnce({ bound: false, bound_at: null })
      .mockResolvedValueOnce({ bound: true, bound_at: "2026-10-15T10:01:00Z" });
    mockedCreateCode.mockRejectedValue(
      new ApiRequestError({
        status: 409,
        code: "WECHAT_ALREADY_BOUND",
        message: "WeChat is already bound",
      }),
    );

    render(<NotificationSettings />);

    await user.click(await screen.findByRole("button", { name: "生成绑定码" }));
    expect(await screen.findByText("已绑定微信，可以接收通知。")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "生成绑定码" })).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("微信已经绑定，无需生成绑定码。");
  });
});
