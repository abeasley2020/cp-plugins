import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { validateMarketplace } from "../lib/validate.mjs";

let root;

function write(rel, content) {
  const abs = join(root, rel);
  mkdirSync(join(abs, ".."), { recursive: true });
  writeFileSync(abs, typeof content === "string" ? content : JSON.stringify(content, null, 2) + "\n");
}

function marketplace(plugins) {
  return {
    name: "cp-plugins",
    owner: { name: "Purdue University Online Course Production" },
    metadata: { description: "Test marketplace", version: "0.1.0" },
    plugins,
  };
}

function plugin(name, overrides = {}) {
  write(`plugins/${name}/.claude-plugin/plugin.json`, {
    name,
    version: "1.0.0",
    description: `The ${name} plugin.`,
    author: { name: "Purdue University Online Course Production" },
    ...overrides,
  });
  write(`plugins/${name}/README.md`, `# ${name}\n`);
  write(`plugins/${name}/skills/check/SKILL.md`, `---\nname: check\ndescription: Run the check.\n---\n\nDo the check.\n`);
}

function template() {
  write("templates/plugin-template/.claude-plugin/plugin.json", {
    name: "cp-PLUGIN_NAME",
    version: "0.1.0",
    description: "PLUGIN_DESCRIPTION",
    author: { name: "Purdue University Online Course Production" },
  });
  write("templates/plugin-template/README.md", "# cp-PLUGIN_NAME\n");
}

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "cp-plugins-validate-"));
  template();
});

afterEach(() => {
  rmSync(root, { recursive: true, force: true });
});

test("a well-formed marketplace with one listed plugin passes", () => {
  plugin("cp-example");
  write(
    ".claude-plugin/marketplace.json",
    marketplace([{ name: "cp-example", source: "./plugins/cp-example", description: "Example.", version: "1.0.0" }])
  );
  const result = validateMarketplace(root);
  assert.deepEqual(result.errors, []);
});

test("a plugin folder that is not listed in marketplace.json is an error", () => {
  plugin("cp-example");
  plugin("cp-orphan");
  write(
    ".claude-plugin/marketplace.json",
    marketplace([{ name: "cp-example", source: "./plugins/cp-example", description: "Example.", version: "1.0.0" }])
  );
  const { errors } = validateMarketplace(root);
  assert.ok(errors.some((e) => e.includes("cp-orphan") && e.includes("not listed")), errors.join("\n"));
});

test("a listed plugin whose folder is missing is an error", () => {
  write(
    ".claude-plugin/marketplace.json",
    marketplace([{ name: "cp-ghost", source: "./plugins/cp-ghost", description: "Ghost.", version: "1.0.0" }])
  );
  const { errors } = validateMarketplace(root);
  assert.ok(errors.some((e) => e.includes("cp-ghost") && e.includes("does not exist")), errors.join("\n"));
});

test("name and version must match between marketplace.json and plugin.json", () => {
  plugin("cp-example", { version: "2.0.0" });
  write(
    ".claude-plugin/marketplace.json",
    marketplace([{ name: "cp-example", source: "./plugins/cp-example", description: "Example.", version: "1.0.0" }])
  );
  const { errors } = validateMarketplace(root);
  assert.ok(errors.some((e) => e.includes("version") && e.includes("cp-example")), errors.join("\n"));
});

test("plugin names must use the cp- prefix and kebab-case", () => {
  plugin("MyPlugin");
  write(
    ".claude-plugin/marketplace.json",
    marketplace([{ name: "MyPlugin", source: "./plugins/MyPlugin", description: "Bad name.", version: "1.0.0" }])
  );
  const { errors } = validateMarketplace(root);
  assert.ok(errors.some((e) => e.includes("MyPlugin") && e.includes("cp-")), errors.join("\n"));
});

test("listed name exceptions pass without the cp- prefix", () => {
  plugin("course-production-agents");
  write(
    ".claude-plugin/marketplace.json",
    marketplace([{ name: "course-production-agents", source: "./plugins/course-production-agents", description: "Exception.", version: "1.0.0" }])
  );
  const { errors } = validateMarketplace(root);
  assert.ok(!errors.some((e) => e.includes("cp- prefix")), errors.join("\n"));
});

test("source must be ./plugins/<name>", () => {
  plugin("cp-example");
  write(
    ".claude-plugin/marketplace.json",
    marketplace([{ name: "cp-example", source: "./cp-example", description: "Example.", version: "1.0.0" }])
  );
  const { errors } = validateMarketplace(root);
  assert.ok(errors.some((e) => e.includes("source") && e.includes("./plugins/cp-example")), errors.join("\n"));
});

test("placeholders left over from the template are an error", () => {
  plugin("cp-example", { description: "PLUGIN_DESCRIPTION" });
  write(
    ".claude-plugin/marketplace.json",
    marketplace([{ name: "cp-example", source: "./plugins/cp-example", description: "Example.", version: "1.0.0" }])
  );
  const { errors } = validateMarketplace(root);
  assert.ok(errors.some((e) => e.includes("placeholder")), errors.join("\n"));
});

test("a plugin needs a README and at least one component", () => {
  write("plugins/cp-empty/.claude-plugin/plugin.json", {
    name: "cp-empty",
    version: "1.0.0",
    description: "Nothing here.",
    author: { name: "Purdue University Online Course Production" },
  });
  write(
    ".claude-plugin/marketplace.json",
    marketplace([{ name: "cp-empty", source: "./plugins/cp-empty", description: "Nothing.", version: "1.0.0" }])
  );
  const { errors } = validateMarketplace(root);
  assert.ok(errors.some((e) => e.includes("README.md")), errors.join("\n"));
  assert.ok(errors.some((e) => e.includes("component")), errors.join("\n"));
});

test("skill and command files need frontmatter with a description", () => {
  plugin("cp-example");
  write("plugins/cp-example/skills/check/SKILL.md", "No frontmatter here.\n");
  write("plugins/cp-example/commands/go.md", "---\nname: go\n---\nBody.\n");
  write(
    ".claude-plugin/marketplace.json",
    marketplace([{ name: "cp-example", source: "./plugins/cp-example", description: "Example.", version: "1.0.0" }])
  );
  const { errors } = validateMarketplace(root);
  assert.ok(errors.some((e) => e.includes("SKILL.md") && e.includes("frontmatter")), errors.join("\n"));
  assert.ok(errors.some((e) => e.includes("go.md") && e.includes("description")), errors.join("\n"));
});

test("owner and author email addresses are rejected", () => {
  plugin("cp-example", { author: { name: "Team", email: ["team", "example.com"].join("@") } });
  const m = marketplace([{ name: "cp-example", source: "./plugins/cp-example", description: "Example.", version: "1.0.0" }]);
  m.owner.email = ["owner", "example.com"].join("@");
  write(".claude-plugin/marketplace.json", m);
  const { errors } = validateMarketplace(root);
  assert.equal(errors.filter((e) => e.includes("email")).length, 2, errors.join("\n"));
});

test("missing marketplace.json or invalid JSON is reported, not thrown", () => {
  assert.ok(validateMarketplace(root).errors.some((e) => e.includes("marketplace.json")));
  write(".claude-plugin/marketplace.json", "{ not json");
  assert.ok(validateMarketplace(root).errors.some((e) => e.includes("JSON")));
});
