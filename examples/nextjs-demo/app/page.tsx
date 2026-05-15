import {
  invoiceAccessMessage,
  visibleInvoices,
  type Invoice,
  type User
} from "../src/invoice-access";

const demoUser: User = {
  email: "reviewer@example.com",
  role: "support",
  assignedInvoiceIds: ["inv_1001"]
};

const invoices: Invoice[] = [
  {
    id: "inv_1001",
    ownerEmail: "customer@example.com",
    status: "sent",
    totalCents: 4200
  },
  {
    id: "inv_1002",
    ownerEmail: "finance@example.com",
    status: "draft",
    totalCents: 9900
  }
];

export default function Page() {
  const allowedInvoices = visibleInvoices(invoices, demoUser);

  return (
    <main>
      <h1>QA-Z Next.js invoice access demo</h1>
      <p>{invoiceAccessMessage(invoices[0], demoUser)}</p>
      <ul>
        {allowedInvoices.map((invoice) => (
          <li key={invoice.id}>
            {invoice.id}: ${Number(invoice.totalCents / 100).toFixed(2)}
          </li>
        ))}
      </ul>
    </main>
  );
}
