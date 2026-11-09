// Marketplace and plugin structure validation for cp-plugins.
//
// validateMarketplace(root) never throws for repository problems. It returns
// { errors, warnings } so the CLI and the tests can decide what to do.

import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const PLUGIN_NAME_PATTERN = /^cp-[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MARKETPLACE_NAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const SEMVER_PATTERN = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/;
const PLACEHOLDER_PATTERN = /PLUGIN_NAME|PLUGIN_DESCRIPTION|PLUGIN_KEYWORD|REPLACE_ME|TODO:/;
const RESERVED_PREFIXES = ["claude-", "anthropic-"];

function readJson(path) {
  if (!existsSync(path)) return { error: `${path} is missing.` };
  try {
    return { value: JSON.parse(readFileSync(path, "utf8")) };
  } catch (err) {
    return { error: `${path} is not valid JSON: ${err.message}` };
  }
}

function listDirs(path) {
  if (!existsSync(path)) return [];
  return readdirSync(path, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort();
}

function listFiles(path, predicate) {
  if (!existsSync(path)) return [];
  const out = [];
  for (const entry of readdirSync(path, { withFileTypes: true })) {
    const full = join(path, entry.name);
    if (entry.isDirectory()) out.push(...listFiles(full, predicate));
    else if (predicate(entry.name)) out.push(full);
  }
  return out;
}

function parseFrontmatter(text) {
  const normalized = text.replace(/^\uFEFF/, "");
  const match = normalized.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!match) return null;
  const fields = {};
  for (const line of match[1].split(/\r?\n/)) {
    const m = line.match(/^([A-Za-z0-9_-]+)\s*:\s*(.*)$/);
    if (m) fields[m[1]] = m[2].trim();
  }
  return fields;
}

function checkMarkdownComponent(file, rel, errors) {
  const fm = parseFrontmatter(readFileSync(file, "utf8"));
  if (!fm) {
    errors.push(`${rel} has no YAML frontmatter. Add a block with at least a description.`);
    return;
  }
  if (!fm.description) errors.push(`${rel} frontmatter is missing a description.`);
}

function validatePlugin(root, entry, errors, warnings) {
  const rel = `plugins/${entry.name}`;
  const dir = join(root, rel);
  if (!existsSync(dir) || !statSync(dir).isDirectory()) {
    errors.push(`Plugin "${entry.name}" is listed in marketplace.json but ${rel} does not exist.`);
    return;
  }

  const manifestRel = `${rel}/.claude-plugin/plugin.json`;
  const manifest = readJson(join(root, manifestRel));
  if (manifest.error) {
    errors.push(manifest.error.replace(join(root, manifestRel), manifestRel));
  } else {
    const p = manifest.value;
    if (p.name !== entry.name) {
      errors.push(`${manifestRel} name "${p.name}" does not match the marketplace entry name "${entry.name}".`);
    }
    if (!p.version) {
      errors.push(`${manifestRel} is missing a version.`);
    } else if (!SEMVER_PATTERN.test(p.version)) {
      errors.push(`${manifestRel} version "${p.version}" is not semver (MAJOR.MINOR.PATCH).`);
    } else if (entry.version && p.version !== entry.version) {
      errors.push(
        `Plugin "${entry.name}" version mismatch: plugin.json says ${p.version}, marketplace.json says ${entry.version}. Bump both together.`
      );
    }
    if (!p.description || !String(p.description).trim()) errors.push(`${manifestRel} is missing a description.`);
    if (!p.author || !p.author.name) {
      warnings.push(`${manifestRel} has no author.name. Use the team name, never a person.`);
    }
    if (p.author && p.author.email) errors.push(`${manifestRel} author.email must be removed. No email addresses in this repository.`);
    const raw = JSON.stringify(p);
    if (PLACEHOLDER_PATTERN.test(raw)) {
      errors.push(`${manifestRel} still contains a template placeholder (PLUGIN_NAME, PLUGIN_DESCRIPTION, or similar).`);
    }
  }

  if (!existsSync(join(dir, "README.md"))) errors.push(`${rel}/README.md is missing.`);

  const skills = listFiles(join(dir, "skills"), (n) => n === "SKILL.md");
  const commands = listFiles(join(dir, "commands"), (n) => n.endsWith(".md"));
  const agents = listFiles(join(dir, "agents"), (n) => n.endsWith(".md"));
  const hasHooks = existsSync(join(dir, "hooks", "hooks.json"));
  const hasMcp = existsSync(join(dir, ".mcp.json"));
  if (skills.length + commands.length + agents.length === 0 && !hasHooks && !hasMcp) {
    errors.push(`${rel} has no component. Add a skill (skills/<name>/SKILL.md), a command, an agent, hooks, or an MCP server.`);
  }
  for (const file of [...skills, ...commands, ...agents]) {
    checkMarkdownComponent(file, file.slice(root.length + 1).split("\\").join("/"), errors);
  }
}

/**
 * Validate the marketplace repository rooted at `root`.
 * @param {string} root absolute path to the repository root
 * @returns {{ errors: string[], warnings: string[] }}
 */
export function validateMarketplace(root) {
  const errors = [];
  const warnings = [];

  const manifest = readJson(join(root, ".claude-plugin", "marketplace.json"));
  if (manifest.error) {
    errors.push(manifest.error.replace(root, "").replace(/^[\\/]/, "").split("\\").join("/"));
    return { errors, warnings };
  }
  const m = manifest.value;

  if (!m.name || !MARKETPLACE_NAME_PATTERN.test(m.name)) {
    errors.push(`marketplace.json name "${m.name}" is missing or invalid.`);
  }
  if (!m.owner || !m.owner.name) errors.push("marketplace.json owner.name is required. Use the team name.");
  if (m.owner && m.owner.email) errors.push("marketplace.json owner.email must be removed. No email addresses in this repository.");
  if (!m.metadata || !m.metadata.description) warnings.push("marketplace.json metadata.description is recommended.");
  if (!Array.isArray(m.plugins)) {
    errors.push("marketplace.json plugins must be an array.");
    return { errors, warnings };
  }

  const seen = new Set();
  for (const entry of m.plugins) {
    if (!entry || typeof entry !== "object") {
      errors.push("marketplace.json contains a plugin entry that is not an object.");
      continue;
    }
    const name = entry.name;
    if (!name || !PLUGIN_NAME_PATTERN.test(name)) {
      errors.push(`Plugin name "${name}" must be kebab-case with the cp- prefix, for example cp-accessibility.`);
    } else if (RESERVED_PREFIXES.some((p) => name.startsWith(p))) {
      errors.push(`Plugin name "${name}" uses a reserved prefix.`);
    }
    if (seen.has(name)) errors.push(`Plugin name "${name}" appears more than once in marketplace.json.`);
    seen.add(name);

    const expectedSource = `./plugins/${name}`;
    if (entry.source !== expectedSource) {
      errors.push(`Plugin "${name}" source must be "${expectedSource}" (got ${JSON.stringify(entry.source)}).`);
    }
    if (!entry.description || !String(entry.description).trim()) {
      errors.push(`Plugin "${name}" entry in marketplace.json is missing a description.`);
    }
    if (!entry.version) {
      errors.push(`Plugin "${name}" entry in marketplace.json is missing a version.`);
    } else if (!SEMVER_PATTERN.test(entry.version)) {
      errors.push(`Plugin "${name}" entry version "${entry.version}" is not semver.`);
    }
    if (entry.author && entry.author.email) errors.push(`Plugin "${name}" entry author.email must be removed.`);

    if (name && PLUGIN_NAME_PATTERN.test(name)) validatePlugin(root, entry, errors, warnings);
  }

  for (const dirName of listDirs(join(root, "plugins"))) {
    if (!seen.has(dirName)) {
      errors.push(
        `plugins/${dirName} exists but is not listed in .claude-plugin/marketplace.json. Add an entry or remove the folder.`
      );
    }
  }

  const templateManifest = join(root, "templates", "plugin-template", ".claude-plugin", "plugin.json");
  if (!existsSync(templateManifest)) {
    errors.push("templates/plugin-template/.claude-plugin/plugin.json is missing. CONTRIBUTING.md depends on it.");
  }

  return { errors, warnings };
}
