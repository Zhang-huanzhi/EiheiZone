import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import FamilyExpendituresPage from "@/app/family/expenditures/page";
import OwnerExpendituresPage from "@/app/owner/expenditures/page";
import { getServerExpenditures } from "@/features/expenditures/expenditure-server";

vi.mock("next/navigation", () => ({ redirect: vi.fn() }));
vi.mock("@/features/expenditures/expenditure-server", () => ({ getServerExpenditures: vi.fn() }));
vi.mock("@/features/expenditures/expenditure-display", () => ({
  ExpenditureList: ({ detailBasePath }: { detailBasePath: string }) => <p>expenditure list {detailBasePath}</p>,
}));

const mockedGetServerExpenditures = vi.mocked(getServerExpenditures);
const emptyPage = { items: [], total: 0, offset: 0, limit: 20 };

afterEach(() => vi.clearAllMocks());

describe("Expenditure pages", () => {
  it("uses authenticated reading without management controls for Family", async () => {
    mockedGetServerExpenditures.mockResolvedValue(emptyPage);
    render(await FamilyExpendituresPage({ searchParams: Promise.resolve({ offset: "20" }) }));
    expect(mockedGetServerExpenditures).toHaveBeenCalledWith({ offset: 20 });
    expect(screen.getByText("expenditure list /family/expenditures")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "记录支出" })).not.toBeInTheDocument();
  });

  it("shows the Owner management entry", async () => {
    mockedGetServerExpenditures.mockResolvedValue(emptyPage);
    render(await OwnerExpendituresPage({ searchParams: Promise.resolve({}) }));
    expect(mockedGetServerExpenditures).toHaveBeenCalledWith({ offset: 0 });
    expect(screen.getByText("expenditure list /owner/expenditures")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "记录支出" })).toHaveAttribute("href", "/owner/expenditures/new");
  });
});
