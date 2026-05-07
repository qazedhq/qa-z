import { readFileSync } from "node:fs";

const source = readFileSync("src/invoice.ts", "utf8");

if (!source.includes("export function canViewInvoice")) {
  console.error("missing canViewInvoice export");
  process.exit(1);
}

console.log("lint passed");
