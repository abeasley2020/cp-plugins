#!/usr/bin/env node
// Content scan: fails when any file in the repository contains a dollar
// amount, an email address, an internal URL, a credential-like value, a
// person-like name in a byline or author field, or an em-dash.
//
// Usage:
//   node scripts/scan-content.mjs            scan the whole repository
//   node scripts/scan-content.mjs <path...>  scan specific files or folders
//   node scripts/scan-content.mjs --json     machine-readable output

import { join, relative, sep } from "node:path";
import { statSync, readdirSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { scanText } from "./lib/scan-rules.mjs";
import { REPO_ROOT, listRepoFiles, isBinaryPath, readTextFile } from "./lib/files.mjs";

function expand(target) {
  const abs = join(REPO_ROOT, target);
  const st = statSync(abs);
  if (st.isFile()) return [target.split(sep).join("/")];
  const out = [];
  for (const entry of readdirSync(abs, { withFileTypes: true })) {
    if (entry.isDirectory() && [".git", "node_modules", "_audit"].includes(entry.name)) continue;
    out.push(...expand(join(target, entry.name)));
  }
  return out;
}

export function scanRepository(targets = []) {
  const files = targets.length
    ? targets.flatMap((t) => expand(relative(REPO_ROOT, join(REPO_ROOT, t))))
    : listRepoFiles();
  const findings = [];
  let scanned = 0;
  for (const file of files) {
    if (isBinaryPath(file)) continue;
    const text = readTextFile(join(REPO_ROOT, file));
    if (text === null) continue;
    scanned += 1;
    findings.push(...scanText(text, { path: file }));
  }
  return { scanned, findings };
}

function main(argv) {
  const json = argv.includes("--json");
  const targets = argv.filter((a) => !a.startsWith("--"));
  const { scanned, findings } = scanRepository(targets);

  if (json) {
    console.log(JSON.stringify({ scanned, findings }, null, 2));
  } else {
    for (const f of findings) {
      console.log(`${f.path}:${f.line}:${f.column}  [${f.rule}]  ${f.message}`);
      console.log(`    ${f.snippet}`);
    }
    const counts = {};
    for (const f of findings) counts[f.rule] = (counts[f.rule] ?? 0) + 1;
    const summary = Object.entries(counts)
      .map(([rule, n]) => `${rule}: ${n}`)
      .join(", ");
    console.log(
      findings.length === 0
        ? `Content scan passed. ${scanned} text files scanned, no findings.`
        : `Content scan FAILED. ${scanned} text files scanned, ${findings.length} finding(s): ${summary}`
    );
  }
  return findings.length === 0 ? 0 : 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}
