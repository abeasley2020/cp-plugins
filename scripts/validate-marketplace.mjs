#!/usr/bin/env node
// Validate .claude-plugin/marketplace.json and every plugin under plugins/.
//
// Usage:
//   node scripts/validate-marketplace.mjs          validate this repository
//   node scripts/validate-marketplace.mjs --json   machine-readable output

import { pathToFileURL } from "node:url";
import { validateMarketplace } from "./lib/validate.mjs";
import { REPO_ROOT } from "./lib/files.mjs";

function main(argv) {
  const json = argv.includes("--json");
  const result = validateMarketplace(REPO_ROOT);
  if (json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    for (const w of result.warnings) console.log(`WARN  ${w}`);
    for (const e of result.errors) console.log(`ERROR ${e}`);
    console.log(
      result.errors.length === 0
        ? `Marketplace validation passed (${result.warnings.length} warning(s)).`
        : `Marketplace validation FAILED with ${result.errors.length} error(s).`
    );
  }
  return result.errors.length === 0 ? 0 : 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}
