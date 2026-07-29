import { describe, expect, it } from "vitest";

import {
  canonicalizeAmount,
  formatExactAmount,
  validateAmountInput,
} from "@/features/expenditures/expenditure-money";
import { formatBusinessDate } from "@/features/expenditures/expenditure-display";

describe("exact expenditure money helpers", () => {
  it("validates decimal strings without floating point conversion", () => {
    expect(validateAmountInput("0.0001")).toBeNull();
    expect(validateAmountInput("99999999999999.9999")).toBeNull();
    expect(validateAmountInput("0.0000")).toBe("金额必须大于 0。");
    expect(validateAmountInput("1.23456")).not.toBeNull();
    expect(validateAmountInput("1e3")).not.toBeNull();
    expect(validateAmountInput("1,000.00")).not.toBeNull();
  });

  it("formats grouping from strings while preserving exact decimals", () => {
    expect(formatExactAmount("12345678901234.5600", "CNY")).toBe("CNY 12,345,678,901,234.56");
    expect(formatExactAmount("0.0001", "JPY")).toBe("JPY 0.0001");
    expect(canonicalizeAmount("001.2300")).toBe("1.23");
  });

  it("formats business dates without constructing a timezone instant", () => {
    expect(formatBusinessDate("2026-07-28")).toBe("2026年7月28日");
  });
});
