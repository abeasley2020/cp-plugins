#!/usr/bin/env node
// Run every CI check locally, in the same order GitHub Actions runs them:
//   1. marketplace and plugin structure validation
//   2. content scan
//   3. unit tests for the scripts and for every plugin
//
// Usage: node scripts/ci.mjs
// Exit code is 0 only when all three steps pass.

import { spawnSync } from "node:child_process";
import { REPO_ROOT } from "./lib/files.mjs";

const steps = [
  { name: "Validate marketplace", args: ["scripts/validate-marketplace.mjs"] },
  { name: "Content scan", args: ["scripts/scan-content.mjs"] },
  { name: "Unit tests", args: ["--test", "scripts/tests/*.test.mjs", "plugins/*/tests/*.test.mjs"] },
];

let failed = 0;
for (const step of steps) {
  console.log(`\n=== ${step.name} ===`);
  const result = spawnSync(process.execPath, step.args, { cwd: REPO_ROOT, stdio: "inherit" });
  if (result.status !== 0) {
    failed += 1;
    console.log(`--- ${step.name}: FAILED (exit ${result.status})`);
  } else {
    console.log(`--- ${step.name}: passed`);
  }
}

console.log(failed === 0 ? "\nCI: all checks passed." : `\nCI: ${failed} check(s) failed.`);
process.exit(failed === 0 ? 0 : 1);
