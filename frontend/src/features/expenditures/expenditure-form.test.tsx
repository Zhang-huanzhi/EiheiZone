import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createExpenditure,
  updateExpenditure,
} from "@/features/expenditures/expenditure-api";
import { ExpenditureForm } from "@/features/expenditures/expenditure-form";
import type { ExpenditureRecord } from "@/features/expenditures/expenditure-types";

const replace = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace, refresh }) }));
vi.mock("@/features/expenditures/expenditure-api", () => ({
  createExpenditure: vi.fn(),
  updateExpenditure: vi.fn(),
}));

const mockedCreate = vi.mocked(createExpenditure);
const mockedUpdate = vi.mocked(updateExpenditure);
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

describe("ExpenditureForm", () => {
  it("shows local errors and has no private-data controls", async () => {
    const user = userEvent.setup();
    render(<ExpenditureForm />);

    await user.click(screen.getByRole("button", { name: "记录支出" }));

    expect(screen.getByText("请选择支出日期。")).toBeInTheDocument();
    expect(screen.getByText("请输入金额。")).toBeInTheDocument();
    expect(screen.getByText("请输入分类。")).toBeInTheDocument();
    expect(screen.getByText("请输入说明。")).toBeInTheDocument();
    expect(screen.getByText(/不记录银行卡号/)).toBeInTheDocument();
    expect(screen.queryByLabelText(/银行卡/)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/流水/)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/附件/)).not.toBeInTheDocument();
    expect(mockedCreate).not.toHaveBeenCalled();
  });

  it("creates with an exact string amount", async () => {
    const user = userEvent.setup();
    mockedCreate.mockResolvedValue(record);
    render(<ExpenditureForm />);

    await user.type(screen.getByLabelText("支出日期"), "2026-07-28");
    await user.type(screen.getByLabelText("金额"), "1234.5600");
    await user.type(screen.getByLabelText("分类"), "Equipment");
    await user.type(screen.getByLabelText("说明"), "Test equipment purchase");
    await user.click(screen.getByRole("button", { name: "记录支出" }));

    expect(mockedCreate).toHaveBeenCalledWith({
      spent_on: "2026-07-28",
      amount: "1234.5600",
      currency: "CNY",
      category: "Equipment",
      description: "Test equipment purchase",
    });
    expect(replace).toHaveBeenCalledWith("/owner/expenditures");
  });

  it("sends only changed fields and treats equivalent decimals as unchanged", async () => {
    const user = userEvent.setup();
    mockedUpdate.mockResolvedValue(record);
    render(<ExpenditureForm initialExpenditure={record} />);

    await user.clear(screen.getByLabelText("分类"));
    await user.type(screen.getByLabelText("分类"), "Updated category");
    await user.click(screen.getByRole("button", { name: "保存修改" }));

    expect(mockedUpdate).toHaveBeenCalledWith("expenditure-id", { category: "Updated category" });
  });

  it("does not send an empty PATCH", async () => {
    const user = userEvent.setup();
    render(<ExpenditureForm initialExpenditure={record} />);

    await user.click(screen.getByRole("button", { name: "保存修改" }));

    expect(screen.getByRole("alert")).toHaveTextContent("没有需要保存的修改。");
    expect(mockedUpdate).not.toHaveBeenCalled();
  });
});
