import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import FamilyQAsPage from "@/app/family/qas/page";
import NewQuestionPage from "@/app/family/qas/new/page";
import OwnerQAsPage from "@/app/owner/qas/page";
import { getServerCurrentUser } from "@/features/auth/auth-server";
import { getServerQAs } from "@/features/qas/qa-server";

vi.mock("next/navigation", () => ({ redirect: vi.fn() }));
vi.mock("@/features/auth/auth-server", () => ({ getServerCurrentUser: vi.fn() }));
vi.mock("@/features/qas/qa-server", () => ({ getServerQAs: vi.fn() }));
vi.mock("@/features/qas/qa-display", () => ({
  QAList: ({ detailBasePath }: { detailBasePath: string }) => <p>qa list {detailBasePath}</p>,
}));
vi.mock("@/features/qas/question-form", () => ({
  QuestionForm: () => <p>question form</p>,
}));

const mockedGetServerCurrentUser = vi.mocked(getServerCurrentUser);
const mockedGetServerQAs = vi.mocked(getServerQAs);
const emptyPage = { items: [], total: 0, offset: 0, limit: 20 };

afterEach(() => {
  vi.clearAllMocks();
});

describe("QA pages", () => {
  it("shows the question entry to a Family reader", async () => {
    mockedGetServerQAs.mockResolvedValue(emptyPage);
    mockedGetServerCurrentUser.mockResolvedValue({
      id: "family-id",
      login_name: "family-user",
      display_name: "Family User",
      role: "family",
    });

    render(await FamilyQAsPage({ searchParams: Promise.resolve({ offset: "20" }) }));

    expect(mockedGetServerQAs).toHaveBeenCalledWith({ offset: 20 });
    expect(screen.getByText("qa list /family/qas")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "提出问题" })).toBeInTheDocument();
  });

  it("shows the question entry to an Owner reader", async () => {
    mockedGetServerQAs.mockResolvedValue(emptyPage);
    mockedGetServerCurrentUser.mockResolvedValue({
      id: "owner-id",
      login_name: "owner-user",
      display_name: "Owner User",
      role: "owner",
    });

    render(await FamilyQAsPage({ searchParams: Promise.resolve({}) }));

    expect(screen.getByText("qa list /family/qas")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "提出问题" })).toBeInTheDocument();
  });

  it("uses the authenticated QA query for Owner management", async () => {
    mockedGetServerQAs.mockResolvedValue(emptyPage);

    render(await OwnerQAsPage({ searchParams: Promise.resolve({}) }));

    expect(mockedGetServerQAs).toHaveBeenCalledWith({ offset: 0 });
    expect(screen.getByText("qa list /owner/qas")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "提出问题" })).toHaveAttribute(
      "href",
      "/family/qas/new",
    );
    expect(screen.queryByRole("button", { name: /删除/ })).not.toBeInTheDocument();
  });

  it("lets Owner open the Family question page", async () => {
    mockedGetServerCurrentUser.mockResolvedValue({
      id: "owner-id",
      login_name: "owner-user",
      display_name: "Owner User",
      role: "owner",
    });

    render(await NewQuestionPage());

    expect(screen.getByRole("heading", { name: "提出问题" })).toBeInTheDocument();
    expect(screen.getByText("question form")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "取消" })).toHaveAttribute("href", "/family/qas");
  });
});
