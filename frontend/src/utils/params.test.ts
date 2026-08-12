import { describe, expect, it } from "vitest";

import { cleanParams } from "@/utils/params";

describe("cleanParams", () => {
  it("drops empty values", () => {
    expect(
      cleanParams({
        page: 1,
        search: "",
        status: "active",
        unused: undefined,
        blank: null,
      }),
    ).toEqual({ page: 1, status: "active" });
  });

  it("returns undefined when params omitted", () => {
    expect(cleanParams()).toBeUndefined();
  });
});
