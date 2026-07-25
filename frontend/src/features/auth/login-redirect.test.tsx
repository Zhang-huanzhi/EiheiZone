import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LoginRedirect } from "@/features/auth/login-redirect";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/family/posts/1",
  useRouter: () => ({ replace }),
}));

afterEach(() => {
  vi.clearAllMocks();
});

describe("LoginRedirect", () => {
  it("preserves the protected target path", async () => {
    render(<LoginRedirect />);

    expect(screen.getByText("正在转到登录页...")).toBeInTheDocument();
    await waitFor(() => {
      expect(replace).toHaveBeenCalledWith(
        "/login?next=%2Ffamily%2Fposts%2F1",
      );
    });
  });
});
