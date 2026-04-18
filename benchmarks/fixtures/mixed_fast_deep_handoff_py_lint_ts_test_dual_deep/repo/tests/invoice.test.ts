import { totalForLines } from "../src/invoice";

test("keeps invoice total numeric", () => {
  expect(totalForLines([1, 2, 3])).toBe("6");
});
