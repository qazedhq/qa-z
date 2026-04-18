const unused = 1;

export function invoiceTotal(items: number[]): number {
  return items.reduce((total, value) => total + value, 0);
}
