import { describe, expect, it } from "vitest";

import { formatMoney, titleCaseStatus, toNumber } from "@/utils/format";

describe("formatMoney", () => {
  it("formats numeric strings as INR", () => {
    expect(formatMoney("1500.5")).toContain("1,500.50");
  });

  it("treats invalid values as zero", () => {
    expect(formatMoney("nope")).toContain("0.00");
  });
});

describe("toNumber", () => {
  it("parses strings and numbers", () => {
    expect(toNumber("12.5")).toBe(12.5);
    expect(toNumber(3)).toBe(3);
  });
});

describe("titleCaseStatus", () => {
  it("replaces underscores with spaces", () => {
    expect(titleCaseStatus("partially_paid")).toBe("partially paid");
  });
});
