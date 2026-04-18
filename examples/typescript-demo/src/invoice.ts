export type InvoiceLine = {
  description: string;
  quantity: number;
  unitPriceCents: number;
};

export function invoiceTotalCents(lines: InvoiceLine[]): number {
  return lines.reduce(
    (total, line) => total + line.quantity * line.unitPriceCents,
    0
  );
}
