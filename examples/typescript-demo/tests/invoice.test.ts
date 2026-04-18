import { describe, expect, test } from "vitest";

import { invoiceTotalCents } from "../src/invoice";

describe("invoiceTotalCents", () => {
  test("adds each line quantity times unit price", () => {
    expect(
      invoiceTotalCents([
        { description: "Base plan", quantity: 1, unitPriceCents: 1200 },
        { description: "Seats", quantity: 3, unitPriceCents: 500 }
      ])
    ).toBe(2700);
  });
});
