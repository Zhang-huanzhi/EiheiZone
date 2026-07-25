import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError, apiRequest } from "@/lib/api/client";
import type { HealthResponse } from "@/lib/api/types";
import { SystemStatus } from "@/features/system-status/system-status";

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return {
    ...actual,
    apiRequest: vi.fn(),
  };
});

const mockedApiRequest = vi.mocked(apiRequest);

afterEach(() => {
  vi.clearAllMocks();
});

describe("SystemStatus", () => {
  it("shows a loading state while the health check is pending", () => {
    mockedApiRequest.mockImplementation(
      () => new Promise<HealthResponse>(() => undefined),
    );

    render(<SystemStatus />);

    expect(screen.getByText("正在检查后端服务...")).toBeInTheDocument();
  });

  it("shows success when the health check succeeds", async () => {
    mockedApiRequest.mockResolvedValue({ status: "ok" });

    render(<SystemStatus />);

    expect(await screen.findByText("后端 API 可用")).toBeInTheDocument();
  });

  it("shows a safe error and request ID when the health check fails", async () => {
    mockedApiRequest.mockRejectedValue(
      new ApiRequestError({
        status: 503,
        code: "SERVICE_UNAVAILABLE",
        message: "Internal upstream detail",
        requestId: "request-503",
      }),
    );

    render(<SystemStatus />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "暂时无法连接后端服务。",
    );
    expect(screen.queryByText("Internal upstream detail")).not.toBeInTheDocument();
    expect(screen.getByText("请求编号：request-503")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "重试" })).toBeInTheDocument();
  });

  it("retries a failed health check and recovers to success", async () => {
    const user = userEvent.setup();
    mockedApiRequest
      .mockRejectedValueOnce(
        new ApiRequestError({
          status: null,
          code: "NETWORK_ERROR",
          message: "暂时无法连接后端服务。",
        }),
      )
      .mockResolvedValueOnce({ status: "ok" });

    render(<SystemStatus />);

    await user.click(await screen.findByRole("button", { name: "重试" }));

    expect(await screen.findByText("后端 API 可用")).toBeInTheDocument();
    expect(mockedApiRequest).toHaveBeenCalledTimes(2);
  });
});
