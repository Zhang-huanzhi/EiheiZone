import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import FamilyPage from "@/app/family/page";
import OwnerPage from "@/app/owner/page";
import type { DashboardData } from "@/features/dashboard/dashboard-types";
import { getServerDashboard } from "@/features/dashboard/dashboard-server";

vi.mock("next/navigation", () => ({ redirect: vi.fn() }));
vi.mock("@/features/dashboard/dashboard-server", () => ({
  getServerDashboard: vi.fn(),
}));

const mockedGetServerDashboard = vi.mocked(getServerDashboard);

const dashboard: DashboardData = {
  posts: {
    total: 1,
    items: [{
      id: "post-id",
      title: "家庭近况",
      body: "正文",
      visibility: "family",
      created_at: "2026-07-29T08:00:00Z",
      updated_at: "2026-07-29T08:00:00Z",
    }],
  },
  qas: {
    total: 1,
    items: [{
      id: "qa-id",
      asked_by: "family-id",
      asked_by_display_name: "Family User",
      question: "最近的问题",
      answer: null,
      answered_by: null,
      answered_by_display_name: null,
      status: "unanswered",
      answered_at: null,
      created_at: "2026-07-29T08:00:00Z",
      updated_at: "2026-07-29T08:00:00Z",
    }],
  },
  expenditures: {
    total: 1,
    items: [{
      id: "expenditure-id",
      created_by: "owner-id",
      created_by_display_name: "Owner User",
      spent_on: "2026-07-29",
      amount: "1234.5600",
      currency: "CNY",
      category: "设备",
      description: "测试支出",
      created_at: "2026-07-29T08:00:00Z",
      updated_at: "2026-07-29T08:00:00Z",
    }],
  },
  unanswered_qas: {
    total: 1,
    items: [],
  },
};
dashboard.unanswered_qas.items = [...dashboard.qas.items];

const emptyDashboard: DashboardData = {
  posts: { items: [], total: 0 },
  qas: { items: [], total: 0 },
  expenditures: { items: [], total: 0 },
  unanswered_qas: { items: [], total: 0 },
};

afterEach(() => vi.clearAllMocks());

describe("Dashboard pages", () => {
  it("renders the three Family summaries from one dashboard request", async () => {
    mockedGetServerDashboard.mockResolvedValue(dashboard);

    render(await FamilyPage());

    expect(mockedGetServerDashboard).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("heading", { name: "最近近况" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "最近问答" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "最近重大支出" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /家庭近况/ })).toHaveAttribute(
      "href",
      "/family/posts/post-id",
    );
    expect(screen.getByRole("link", { name: /最近的问题/ })).toHaveAttribute(
      "href",
      "/family/qas/qa-id",
    );
    expect(screen.getByText("CNY 1,234.56")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "近况管理" })).not.toBeInTheDocument();
  });

  it("renders Owner management entrances and pending QA summary", async () => {
    mockedGetServerDashboard.mockResolvedValue(dashboard);

    render(await OwnerPage());

    expect(mockedGetServerDashboard).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("link", { name: /近况管理/ })).toHaveAttribute(
      "href",
      "/owner/posts",
    );
    expect(screen.getByRole("link", { name: /问答管理/ })).toHaveAttribute(
      "href",
      "/owner/qas",
    );
    expect(screen.getByRole("link", { name: /支出管理/ })).toHaveAttribute(
      "href",
      "/owner/expenditures",
    );
    expect(screen.getByRole("heading", { name: "待回答问题" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /最近的问题/ })).toHaveAttribute(
      "href",
      "/owner/qas/qa-id",
    );
  });

  it("keeps module-specific empty states distinct from request failures", async () => {
    mockedGetServerDashboard.mockResolvedValue(emptyDashboard);

    const { unmount } = render(await FamilyPage());
    expect(screen.getByText("目前还没有可查看的近况。")).toBeInTheDocument();
    expect(screen.getByText("目前还没有家庭问答。")).toBeInTheDocument();
    expect(screen.getByText("目前还没有重大支出记录。")).toBeInTheDocument();
    unmount();

    render(await OwnerPage());
    expect(screen.getByText("当前没有等待回答的问题。")).toBeInTheDocument();
  });
});
