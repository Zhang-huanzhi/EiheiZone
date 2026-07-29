import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import FamilyLayout from "@/app/family/layout";
import OwnerLayout from "@/app/owner/layout";
import { getServerCurrentUser } from "@/features/auth/auth-server";
import { ApiRequestError } from "@/lib/api/client";

vi.mock("@/features/auth/auth-server", () => ({
  getServerCurrentUser: vi.fn(),
}));

vi.mock("@/features/auth/auth-service-unavailable", () => ({
  AuthServiceUnavailable: ({ requestId }: { requestId?: string | null }) => (
    <p>auth service unavailable {requestId}</p>
  ),
}));

vi.mock("@/features/auth/login-redirect", () => ({
  LoginRedirect: () => <p>login redirect</p>,
}));

vi.mock("@/features/auth/account-menu", () => ({
  AccountMenu: ({ displayName }: { displayName: string }) => (
    <button>{displayName}的账号菜单</button>
  ),
}));

vi.mock("@/features/auth/area-navigation", () => ({
  AreaNavigation: ({ area }: { area: "family" | "owner" }) => (
    <nav aria-label={`${area} navigation`} />
  ),
}));

const mockedGetServerCurrentUser = vi.mocked(getServerCurrentUser);
const familyUser = {
  id: "family-id",
  login_name: "family",
  display_name: "Family User",
  role: "family" as const,
};
const ownerUser = {
  id: "owner-id",
  login_name: "owner",
  display_name: "Owner User",
  role: "owner" as const,
};

afterEach(() => {
  vi.clearAllMocks();
});

describe("protected layouts", () => {
  it("sends an anonymous Family request to login", async () => {
    mockedGetServerCurrentUser.mockRejectedValue(
      new ApiRequestError({
        status: 401,
        code: "UNAUTHORIZED",
        message: "Authentication is required",
      }),
    );

    render(await FamilyLayout({ children: <p>private</p> }));

    expect(screen.getByText("login redirect")).toBeInTheDocument();
    expect(screen.queryByText("private")).not.toBeInTheDocument();
  });

  it("allows Family and Owner users into the Family area", async () => {
    for (const user of [familyUser, ownerUser]) {
      mockedGetServerCurrentUser.mockResolvedValueOnce(user);
      const { unmount } = render(
        await FamilyLayout({ children: <p>family content</p> }),
      );

      expect(screen.getByText("family content")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: `${user.display_name}的账号菜单` }),
      ).toBeInTheDocument();
      expect(screen.getByRole("navigation", { name: "family navigation" })).toBeInTheDocument();
      unmount();
    }
  });

  it("shows forbidden instead of Owner content to a Family user", async () => {
    mockedGetServerCurrentUser.mockResolvedValue(familyUser);

    render(await OwnerLayout({ children: <p>owner content</p> }));

    expect(screen.getByText("无权访问管理区域")).toBeInTheDocument();
    expect(screen.queryByText("owner content")).not.toBeInTheDocument();
  });

  it("allows an Owner user into the Owner area", async () => {
    mockedGetServerCurrentUser.mockResolvedValue(ownerUser);

    render(await OwnerLayout({ children: <p>owner content</p> }));

    expect(screen.getByText("owner content")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Owner User的账号菜单" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "owner navigation" })).toBeInTheDocument();
  });

  it("shows a safe service state when Family identity lookup fails", async () => {
    mockedGetServerCurrentUser.mockRejectedValue(
      new ApiRequestError({
        status: null,
        code: "NETWORK_ERROR",
        message: "Unable to reach the service.",
      }),
    );

    render(await FamilyLayout({ children: <p>private</p> }));

    expect(screen.getByText("auth service unavailable")).toBeInTheDocument();
    expect(screen.queryByText("private")).not.toBeInTheDocument();
  });

  it("keeps only the request ID when Owner identity lookup returns an API error", async () => {
    mockedGetServerCurrentUser.mockRejectedValue(
      new ApiRequestError({
        status: 500,
        code: "INTERNAL_SERVER_ERROR",
        message: "Internal detail must stay hidden",
        requestId: "request-500",
      }),
    );

    render(await OwnerLayout({ children: <p>private</p> }));

    expect(
      screen.getByText("auth service unavailable request-500"),
    ).toBeInTheDocument();
    expect(screen.queryByText("Internal detail must stay hidden")).not.toBeInTheDocument();
  });
});
