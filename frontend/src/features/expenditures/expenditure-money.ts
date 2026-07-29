const DECIMAL_PATTERN = /^[0-9]+(?:\.[0-9]{1,4})?$/;

export function validateAmountInput(value: string): string | null {
  if (!value) {
    return "请输入金额。";
  }
  if (!DECIMAL_PATTERN.test(value)) {
    return "金额必须是最多四位小数的十进制字符串。";
  }

  const [integerPart, fractionPart = ""] = value.split(".");
  const significantInteger = integerPart.replace(/^0+/, "") || "0";
  if (significantInteger.length > 14) {
    return "金额整数部分不能超过 14 位。";
  }
  if ([integerPart, fractionPart].join("").split("").every((digit) => digit === "0")) {
    return "金额必须大于 0。";
  }
  return null;
}

export function canonicalizeAmount(value: string): string {
  if (!DECIMAL_PATTERN.test(value)) {
    return value;
  }
  const [integerPart, fractionPart = ""] = value.split(".");
  const integer = integerPart.replace(/^0+(?=[0-9])/, "") || "0";
  const fraction = fractionPart.replace(/0+$/, "");
  return fraction ? `${integer}.${fraction}` : integer;
}

export function formatExactAmount(amount: string, currency: string): string {
  const canonical = canonicalizeAmount(amount);
  if (!DECIMAL_PATTERN.test(canonical)) {
    return `${currency} ${amount}`;
  }
  const [integerPart, fractionPart] = canonical.split(".");
  const groupedInteger = integerPart.replace(/\B(?=([0-9]{3})+(?![0-9]))/g, ",");
  return `${currency} ${fractionPart ? `${groupedInteger}.${fractionPart}` : groupedInteger}`;
}
