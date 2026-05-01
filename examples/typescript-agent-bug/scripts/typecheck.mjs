import { readFileSync } from "node:fs";

const source = readFileSync("src/invoice.ts", "utf8");

for (const token of ["interface Invoice", "actorId: string | null", "): boolean"]) {
  if (!source.includes(token)) {
    console.error(`type surface missing: ${token}`);
    process.exit(1);
  }
}

console.log("typecheck passed");
