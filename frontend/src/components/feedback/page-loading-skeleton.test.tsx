import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PageLoadingSkeleton } from "@/components/feedback/page-loading-skeleton";

describe("PageLoadingSkeleton", () => {
  it.each([
    ["public", "公开区域正在加载"],
    ["family", "家庭区域正在加载"],
    ["owner", "管理区域正在加载"],
  ] as const)("renders the %s page structure", (variant, label) => {
    render(<PageLoadingSkeleton variant={variant} />);

    expect(screen.getByRole("status", { name: label })).toHaveAttribute("aria-busy", "true");
    expect(screen.getAllByRole("status")[0]).toBeInTheDocument();
  });
});
