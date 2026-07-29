import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AccountMenu } from "@/features/auth/account-menu";

vi.mock("@/features/auth/logout-button", () => ({
  LogoutButton: () => <button>退出登录</button>,
}));

describe("AccountMenu", () => {
  it("keeps logout inside the named account menu", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <AccountMenu displayName="Family User" roleLabel="Family" />,
    );
    const details = container.querySelector("details");
    const trigger = container.querySelector("summary");

    expect(details).not.toHaveAttribute("open");
    expect(trigger).toHaveAccessibleName("Family User的账号菜单");
    expect(screen.getByText("Family")).toBeInTheDocument();

    if (!trigger) {
      throw new Error("Account menu trigger was not rendered");
    }
    await user.click(trigger);

    expect(details).toHaveAttribute("open");
    expect(screen.getByRole("button", { name: "退出登录" })).toBeInTheDocument();
  });
});
