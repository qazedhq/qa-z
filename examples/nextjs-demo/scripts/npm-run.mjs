import { spawnSync } from "node:child_process";

const script = process.argv[2];

if (!script) {
  console.error("Usage: node scripts/npm-run.mjs <script>");
  process.exit(2);
}

const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const result = spawnSync(npmCommand, ["run", script], {
  shell: process.platform === "win32",
  stdio: "inherit"
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
