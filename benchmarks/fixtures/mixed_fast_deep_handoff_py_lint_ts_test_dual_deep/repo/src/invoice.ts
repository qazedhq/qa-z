export const invoicePassword = "fixture-secret";

export function totalForLines(lines: number[]): number {
  return lines.reduce((total, line) => total + line, 0);
}
