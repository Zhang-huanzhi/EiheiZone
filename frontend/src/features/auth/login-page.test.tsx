import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import LoginPage from "@/app/login/page";
import { getServerCurrentUser } from "@/features/auth/auth-server";
import { ApiRequestError } from "@/lib/api/client";

const { redirect } = vi.hoisted(() => ({ redirect: vi.fn() }));

vi.mock("next/navigation", () => ({ redirect }));

vi.mock("@/features/auth/auth-server", () => ({
  getServerCurrentUser: vi.fn(),
}));

vi.mock("@/features/auth/auth-service-unavailable", () => ({
  AuthServiceUnavailable: () => <p>safe service error</p>,
}));

vi.mock("@/features/auth/login-form", () => ({
  LoginForm: () => <form aria-label="login form" />,
}));

const mockedGetServerCurrentUser = vi.mocked(getServerCurrentUser);

afterEach(() => {
  vi.clearAllMocks();
});

describe("LoginPage", () => {
  it("shows the login form for an anonymous user", async () => {
    mockedGetServerCurrentUser.mockRejectedValue(
      new ApiRequestError({
        status: 401,
        code: "UNAUTHORIZED",
        message: "Authentication is required",
      }),
    );

    render(await LoginPage({ searchParams: Promise.resolve({}) }));

    expect(screen.getByRole("form", { name: "login form" })).toBeInTheDocument();
  });

  it("shows a safe state when the auth service is unavailable", async () => {
    mockedGetServerCurrentUser.mockRejectedValue(
      new ApiRequestError({
        status: null,
        code: "NETWORK_ERROR",
        message: "Unable to reach the service.",
      }),
    );

    render(await LoginPage({ searchParams: Promise.resolve({}) }));

    expect(screen.getByText("safe service error")).toBeInTheDocument();
    expect(screen.queryByText("Unable to reach the service.")).not.toBeInTheDocument();
  });

  it("redirects an authenticated user to the role home", async () => {
    mockedGetServerCurrentUser.mockResolvedValue({
      id: "owner-id",
      login_name: "owner",
      display_name: "Owner",
      role: "owner",
    });

    await LoginPage({ searchParams: Promise.resolve({}) });

    expect(redirect).toHaveBeenCalledWith("/owner");
  });
});
