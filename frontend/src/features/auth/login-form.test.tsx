import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { getCsrfToken, loginUser } from "@/features/auth/auth-api";
import { LoginForm } from "@/features/auth/login-form";
import { ApiRequestError } from "@/lib/api/client";

const replace = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, refresh }),
}));

vi.mock("@/features/auth/auth-api", () => ({
  getCsrfToken: vi.fn(),
  loginUser: vi.fn(),
}));

const mockedGetCsrfToken = vi.mocked(getCsrfToken);
const mockedLoginUser = vi.mocked(loginUser);

afterEach(() => {
  vi.clearAllMocks();
});

async function fillAndSubmit(loginName = "family", password = "test-password") {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("登录账号"), loginName);
  await user.type(screen.getByLabelText("密码"), password);
  await user.click(screen.getByRole("button", { name: "登录" }));
  return user;
}

describe("LoginForm", () => {
  it("shows required field errors without making a request", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.click(screen.getByRole("button", { name: "登录" }));

    expect(screen.getByText("请输入登录账号。")).toBeInTheDocument();
    expect(screen.getByText("请输入密码。")).toBeInTheDocument();
    expect(mockedGetCsrfToken).not.toHaveBeenCalled();
  });

  it("gets CSRF, logs in, and routes Family to its allowed target", async () => {
    mockedGetCsrfToken.mockResolvedValue("anonymous-token");
    mockedLoginUser.mockResolvedValue({
      user: {
        id: "family-id",
        login_name: "family",
        display_name: "Family",
        role: "family",
      },
      csrf_token: "rotated-token",
    });
    render(<LoginForm nextPath="/family/posts" />);

    await fillAndSubmit();

    expect(mockedGetCsrfToken).toHaveBeenCalledTimes(1);
    expect(mockedLoginUser).toHaveBeenCalledWith(
      { login_name: "family", password: "test-password" },
      "anonymous-token",
    );
    expect(replace).toHaveBeenCalledWith("/family/posts");
    expect(refresh).toHaveBeenCalled();
  });

  it("routes Owner to the Owner home", async () => {
    mockedGetCsrfToken.mockResolvedValue("anonymous-token");
    mockedLoginUser.mockResolvedValue({
      user: {
        id: "owner-id",
        login_name: "owner",
        display_name: "Owner",
        role: "owner",
      },
      csrf_token: "rotated-token",
    });
    render(<LoginForm />);

    await fillAndSubmit("owner");

    expect(replace).toHaveBeenCalledWith("/owner");
  });

  it("shows the same safe message for invalid credentials", async () => {
    mockedGetCsrfToken.mockResolvedValue("anonymous-token");
    mockedLoginUser.mockRejectedValue(
      new ApiRequestError({
        status: 401,
        code: "INVALID_CREDENTIALS",
        message: "The login name or password is incorrect",
      }),
    );
    render(<LoginForm />);

    await fillAndSubmit("missing", "wrong-password");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "账号或密码不正确。",
    );
  });

  it("disables submission while login is pending", async () => {
    mockedGetCsrfToken.mockImplementation(() => new Promise(() => undefined));
    render(<LoginForm />);

    const user = await fillAndSubmit();
    const button = screen.getByRole("button", { name: "正在登录..." });

    expect(button).toBeDisabled();
    await user.click(button);
    expect(mockedGetCsrfToken).toHaveBeenCalledTimes(1);
  });
});
