#!/usr/bin/env node
// cp-accessibility static checker.
//
// Usage:
//   node check.mjs <file-or-folder> [more paths] [--json] [--config <path>]
//
// Folders are searched for .html and .htm files. Exit codes:
//   0  no findings
//   1  findings reported
//   2  no input, or a path could not be read

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join, relative, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { checkHtml } from "./lib/rules.mjs";
import { formatJson, formatMarkdown, resolveConfig } from "./lib/report.mjs";

function collectHtmlFiles(target) {
  const st = statSync(target);
  if (st.isFile()) return [target];
  const out = [];
  for (const entry of readdirSync(target, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if ([".git", "node_modules", "_audit"].includes(entry.name)) continue;
      out.push(...collectHtmlFiles(join(target, entry.name)));
    } else if ([".html", ".htm"].includes(extname(entry.name).toLowerCase())) {
      out.push(join(target, entry.name));
    }
  }
  return out;
}

export function runCheck(paths, config) {
  const results = [];
  for (const input of paths) {
    const abs = resolve(input);
    if (!existsSync(abs)) {
      results.push({ path: input, findings: [], error: "path does not exist" });
      continue;
    }
    for (const file of collectHtmlFiles(abs)) {
      const display = relative(process.cwd(), file) || file;
      try {
        const html = readFileSync(file, "utf8");
        results.push({ path: display, findings: checkHtml(html, config) });
      } catch (err) {
        results.push({ path: display, findings: [], error: err.message });
      }
    }
  }
  return results;
}

function main(argv) {
  let configPath;
  let json = false;
  const paths = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--json") json = true;
    else if (arg === "--config") configPath = argv[++i];
    else if (arg === "--format") json = argv[++i] === "json";
    else if (!arg.startsWith("--")) paths.push(arg);
  }
  if (paths.length === 0) {
    console.error("Usage: node check.mjs <file-or-folder> [more paths] [--json] [--config <path>]");
    return 2;
  }

  const config = resolveConfig(configPath);
  if (!json && config.format === "json") json = true;
  const results = runCheck(paths, config);

  console.log(json ? formatJson(results) : formatMarkdown(results));
  if (!json) {
    console.log(
      config.configLoaded
        ? `Config: ${config.configPath}`
        : `Config: none found at ${config.configPath} (defaults in use)`
    );
  }

  if (results.some((r) => r.error)) return 2;
  return results.some((r) => r.findings.length > 0) ? 1 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}
