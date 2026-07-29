import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AreaNavigation } from "@/features/auth/area-navigation";

const { mockedUsePathname } = vi.hoisted(() => ({
  mockedUsePathname: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: mockedUsePathname,
}));

afterEach(() => {
  vi.clearAllMocks();
});

describe("AreaNavigation", () => {
  it("marks the current Family module on a nested route", () => {
    mockedUsePathname.mockReturnValue("/family/qas/question-id");

    render(<AreaNavigation area="family" />);

    expect(screen.getByRole("navigation", { name: "家庭区域主导航" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "问答" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "家庭首页" })).not.toHaveAttribute(
      "aria-current",
    );
    expect(screen.getByRole("link", { name: "重大支出" })).toHaveAttribute(
      "href",
      "/family/expenditures",
    );
  });

  it("marks the current Owner module on an edit route", () => {
    mockedUsePathname.mockReturnValue("/owner/expenditures/expenditure-id/edit");

    render(<AreaNavigation area="owner" />);

    expect(screen.getByRole("navigation", { name: "管理区域主导航" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "支出管理" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "管理工作台" })).not.toHaveAttribute(
      "aria-current",
    );
  });
});
