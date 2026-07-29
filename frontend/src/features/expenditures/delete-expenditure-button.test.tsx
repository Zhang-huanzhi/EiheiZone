import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { deleteExpenditure } from "@/features/expenditures/expenditure-api";
import { DeleteExpenditureButton } from "@/features/expenditures/delete-expenditure-button";
import type { ExpenditureRecord } from "@/features/expenditures/expenditure-types";

const replace = vi.fn();
const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace, refresh }) }));
vi.mock("@/features/expenditures/expenditure-api", () => ({ deleteExpenditure: vi.fn() }));

const mockedDelete = vi.mocked(deleteExpenditure);
const record: ExpenditureRecord = {
  id: "expenditure-id",
  created_by: "owner-id",
  created_by_display_name: "Owner User",
  spent_on: "2026-07-28",
  amount: "1234.5600",
  currency: "CNY",
  category: "Equipment",
  description: "Test equipment purchase",
  created_at: "2026-07-28T00:00:00Z",
  updated_at: "2026-07-28T00:00:00Z",
};

afterEach(() => vi.clearAllMocks());

describe("DeleteExpenditureButton", () => {
  it("does not delete when cancelled", async () => {
    const user = userEvent.setup();
    render(<DeleteExpenditureButton expenditure={record} />);
    await user.click(screen.getByRole("button", { name: "删除记录" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("CNY 1,234.56");
    await user.click(screen.getByRole("button", { name: "取消" }));
    expect(mockedDelete).not.toHaveBeenCalled();
  });

  it("deletes after confirmation", async () => {
    const user = userEvent.setup();
    mockedDelete.mockResolvedValue();
    render(<DeleteExpenditureButton expenditure={record} />);
    await user.click(screen.getByRole("button", { name: "删除记录" }));
    await user.click(screen.getByRole("button", { name: "确认删除" }));
    expect(mockedDelete).toHaveBeenCalledWith("expenditure-id");
    expect(replace).toHaveBeenCalledWith("/owner/expenditures");
    expect(refresh).toHaveBeenCalled();
  });
});
