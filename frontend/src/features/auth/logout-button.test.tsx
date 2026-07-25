import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { logoutUser } from "@/features/auth/auth-api";
import { LogoutButton } from "@/features/auth/logout-button";
import { ApiRequestError } from "@/lib/api/client";

const replace = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, refresh }),
}));

vi.mock("@/features/auth/auth-api", () => ({
  logoutUser: vi.fn(),
}));

const mockedLogoutUser = vi.mocked(logoutUser);

afterEach(() => {
  vi.clearAllMocks();
});

describe("LogoutButton", () => {
  it("returns to the public home after logout", async () => {
    mockedLogoutUser.mockResolvedValue();
    const user = userEvent.setup();
    render(<LogoutButton />);

    await user.click(screen.getByRole("button", { name: "退出登录" }));

    expect(mockedLogoutUser).toHaveBeenCalledTimes(1);
    expect(replace).toHaveBeenCalledWith("/");
    expect(refresh).toHaveBeenCalled();
  });

  it("treats an expired session as logged out", async () => {
    mockedLogoutUser.mockRejectedValue(
      new ApiRequestError({
        status: 401,
        code: "UNAUTHORIZED",
        message: "Authentication is required",
      }),
    );
    const user = userEvent.setup();
    render(<LogoutButton />);

    await user.click(screen.getByRole("button", { name: "退出登录" }));

    expect(replace).toHaveBeenCalledWith("/login");
  });

  it("keeps a retryable error on other failures", async () => {
    mockedLogoutUser.mockRejectedValue(new Error("service failed"));
    const user = userEvent.setup();
    render(<LogoutButton />);

    await user.click(screen.getByRole("button", { name: "退出登录" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "暂时无法退出，请重试。",
    );
    expect(screen.getByRole("button", { name: "退出登录" })).toBeEnabled();
  });
});
