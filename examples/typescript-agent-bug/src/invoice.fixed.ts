export interface Invoice {
  id: string;
  ownerId: string;
}

export function canViewInvoice(
  actorId: string | null,
  invoice: Invoice,
  isAdmin = false,
): boolean {
  if (isAdmin) {
    return true;
  }
  if (actorId === null) {
    return false;
  }
  return actorId === invoice.ownerId;
}
