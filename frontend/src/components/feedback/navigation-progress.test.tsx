import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Link from "next/link";

import { NavigationProgress } from "@/components/feedback/navigation-progress";

const { mockedUsePathname } = vi.hoisted(() => ({
  mockedUsePathname: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: mockedUsePathname,
}));

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
  document.body.innerHTML = "";
});

describe("NavigationProgress", () => {
  it("shows progress immediately and a slow-network message after the delay", () => {
    vi.useFakeTimers();
    mockedUsePathname.mockReturnValue("/");
    render(
      <>
        <NavigationProgress />
        <Link href="/posts">公开近况</Link>
      </>,
    );

    fireEvent.click(screen.getByRole("link", { name: "公开近况" }));

    expect(document.querySelector(".navigation-progress-bar")).toBeInTheDocument();
    expect(screen.queryByText("网络较慢，仍在加载...")).not.toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1200);
    });

    expect(screen.getByText("网络较慢，仍在加载...")).toBeInTheDocument();
  });

  it("clears progress when the pathname changes", () => {
    mockedUsePathname.mockReturnValue("/");
    const view = render(
      <>
        <NavigationProgress />
        <Link href="/posts">公开近况</Link>
      </>,
    );

    fireEvent.click(screen.getByRole("link", { name: "公开近况" }));
    expect(document.querySelector(".navigation-progress-bar")).toBeInTheDocument();

    mockedUsePathname.mockReturnValue("/posts");
    view.rerender(
      <>
        <NavigationProgress />
        <Link href="/posts">公开近况</Link>
      </>,
    );

    expect(document.querySelector(".navigation-progress-bar")).not.toBeInTheDocument();
  });

  it("ignores external and modified clicks", () => {
    mockedUsePathname.mockReturnValue("/");
    render(
      <>
        <NavigationProgress />
        <a href="https://example.com">外部链接</a>
        <Link href="/posts">公开近况</Link>
      </>,
    );

    fireEvent.click(screen.getByRole("link", { name: "外部链接" }));
    expect(document.querySelector(".navigation-progress-bar")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "公开近况" }), { ctrlKey: true });
    expect(document.querySelector(".navigation-progress-bar")).not.toBeInTheDocument();
  });
});
