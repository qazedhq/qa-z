import { describe, expect, test } from "vitest";

import {
  canViewInvoice,
  invoiceAccessMessage,
  visibleInvoices,
  type Invoice,
  type User
} from "../src/invoice-access";

const invoice: Invoice = {
  id: "inv_1001",
  ownerEmail: "customer@example.com",
  status: "sent",
  totalCents: 4200
};

describe("invoice access", () => {
  test("lets finance review every invoice", () => {
    const user: User = {
      email: "finance@example.com",
      role: "finance",
      assignedInvoiceIds: []
    };

    expect(canViewInvoice(invoice, user)).toBe(true);
  });

  test("lets support review assigned invoices only", () => {
    const assignedUser: User = {
      email: "support@example.com",
      role: "support",
      assignedInvoiceIds: ["inv_1001"]
    };
    const unassignedUser: User = {
      email: "support@example.com",
      role: "support",
      assignedInvoiceIds: ["inv_9999"]
    };

    expect(canViewInvoice(invoice, assignedUser)).toBe(true);
    expect(canViewInvoice(invoice, unassignedUser)).toBe(false);
  });

  test("filters visible invoices and renders deterministic copy", () => {
    const user: User = {
      email: "support@example.com",
      role: "support",
      assignedInvoiceIds: ["inv_1001"]
    };
    const hiddenInvoice: Invoice = {
      id: "inv_1002",
      ownerEmail: "other@example.com",
      status: "draft",
      totalCents: 9900
    };

    expect(visibleInvoices([invoice, hiddenInvoice], user)).toEqual([invoice]);
    expect(invoiceAccessMessage(hiddenInvoice, user)).toBe(
      "support@example.com needs explicit access for inv_1002."
    );
  });
});
