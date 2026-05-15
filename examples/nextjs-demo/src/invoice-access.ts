export type InvoiceStatus = "draft" | "sent" | "paid";

export type Invoice = {
  id: string;
  ownerEmail: string;
  status: InvoiceStatus;
  totalCents: number;
};

export type UserRole = "finance" | "support" | "viewer";

export type User = {
  email: string;
  role: UserRole;
  assignedInvoiceIds: string[];
};

export function canViewInvoice(invoice: Invoice, user: User): boolean {
  if (user.role === "finance") {
    return true;
  }

  if (invoice.ownerEmail === user.email) {
    return true;
  }

  return user.role === "support" && user.assignedInvoiceIds.includes(invoice.id);
}

export function visibleInvoices(invoices: Invoice[], user: User): Invoice[] {
  return invoices.filter((invoice) => canViewInvoice(invoice, user));
}

export function invoiceAccessMessage(invoice: Invoice, user: User): string {
  if (canViewInvoice(invoice, user)) {
    return `${user.email} can review ${invoice.id}.`;
  }

  return `${user.email} needs explicit access for ${invoice.id}.`;
}
