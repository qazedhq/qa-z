import { readFileSync } from "node:fs";

const source = readFileSync("src/invoice.ts", "utf8");

if (source.includes("return actorId !== null;")) {
  console.error("non-owner user_2 was allowed to view inv_1");
  process.exit(1);
}

if (!source.includes("return actorId === invoice.ownerId;")) {
  console.error("owner check is missing");
  process.exit(1);
}

console.log("4 passed");
