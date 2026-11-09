// Config loading and report formatting for cp-accessibility.

import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

/** Default location of the team runtime config. Never inside the repository. */
export const DEFAULT_CONFIG_PATH = join(homedir(), ".cp-plugins", "config.json");

const DEFAULTS = Object.freeze({
  disabledRules: [],
  genericLinkText: [],
  format: "markdown",
});

/**
 * Read %USERPROFILE%\.cp-plugins\config.json (or the given path). The file is
 * optional. Anything missing or malformed falls back to the defaults.
 * Only the "accessibility" section is read here.
 */
export function resolveConfig(path = DEFAULT_CONFIG_PATH) {
  let section = {};
  try {
    if (existsSync(path)) {
      const parsed = JSON.parse(readFileSync(path, "utf8"));
      if (parsed && typeof parsed.accessibility === "object" && parsed.accessibility) section = parsed.accessibility;
    }
  } catch {
    section = {};
  }
  const list = (v) => (Array.isArray(v) ? v.filter((x) => typeof x === "string") : []);
  return {
    disabledRules: list(section.disabledRules),
    genericLinkText: list(section.genericLinkText),
    format: section.format === "json" ? "json" : DEFAULTS.format,
    configPath: path,
    configLoaded: existsSync(path),
  };
}

function escapeCell(value) {
  return String(value).replace(/\|/g, "\\|").replace(/\r?\n/g, " ");
}

/**
 * @param {Array<{ path: string, findings: Array<object>, error?: string }>} results
 */
export function formatMarkdown(results) {
  const lines = [];
  const total = results.reduce((n, r) => n + (r.findings ? r.findings.length : 0), 0);
  lines.push("# cp-accessibility report");
  lines.push("");
  lines.push(`Files checked: ${results.length}. Findings: ${total}.`);
  lines.push("");
  for (const result of results) {
    lines.push(`## ${result.path}`);
    lines.push("");
    if (result.error) {
      lines.push(`Could not check this file: ${result.error}`);
      lines.push("");
      continue;
    }
    if (result.findings.length === 0) {
      lines.push("No issues found by the static checks. Contrast, reflow, and focus visibility still need a browser review.");
      lines.push("");
      continue;
    }
    lines.push("| Line | WCAG | Level | Rule | Problem | Fix |");
    lines.push("|---|---|---|---|---|---|");
    for (const f of result.findings) {
      lines.push(
        `| ${f.line} | ${f.criterion} ${escapeCell(f.criterionName)} | ${f.level} | ${f.rule} | ${escapeCell(f.message)} | ${escapeCell(f.fix)} |`
      );
    }
    lines.push("");
    lines.push("Snippets:");
    lines.push("");
    for (const f of result.findings) {
      lines.push(`- Line ${f.line}: \`${f.snippet.replace(/`/g, "'")}\``);
    }
    lines.push("");
  }
  return lines.join("\n");
}

export function formatJson(results) {
  return JSON.stringify({ files: results }, null, 2);
}
