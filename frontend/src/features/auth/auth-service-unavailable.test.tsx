import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthServiceUnavailable } from "@/features/auth/auth-service-unavailable";

const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

afterEach(() => {
  vi.clearAllMocks();
});

describe("AuthServiceUnavailable", () => {
  it("shows only safe user-facing information and retries", async () => {
    const user = userEvent.setup();
    render(<AuthServiceUnavailable requestId="request-500" />);

    expect(screen.getByRole("alert")).toHaveTextContent("服务暂时不可用");
    expect(screen.getByRole("alert")).toHaveTextContent(
      "暂时无法确认登录状态，请稍后重试。",
    );
    expect(screen.getByText("请求编号：request-500")).toBeInTheDocument();
    expect(screen.queryByText("ApiRequestError")).not.toBeInTheDocument();
    expect(screen.queryByText("client.ts")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "重试" }));
    expect(refresh).toHaveBeenCalledTimes(1);
  });
});
