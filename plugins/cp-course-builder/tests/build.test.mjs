import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { cpSync, mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const plugin = join(here, "..");
const cli = join(plugin, "scripts", "cpbuild.py");
const example = join(plugin, "examples", "fspg-101", "modules", "module-03");
const lessonName = "01-gloves-and-handwashing.md";

// Find a Python 3.8+ that runs (on Windows, python3 can be a Store placeholder).
function findPython() {
  for (const cmd of ["python3", "python", "py"]) {
    const r = spawnSync(cmd, ["-c", "import sys; print(sys.version_info >= (3, 8))"], { encoding: "utf8" });
    if (r.status === 0 && r.stdout.trim() === "True") return cmd;
  }
  return null;
}
const python = findPython();
const skip = python ? false : "Python 3.8 or later not found";

function run(args) {
  return spawnSync(python, [cli, ...args], { encoding: "utf8", env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" } });
}

function copyModule() {
  const dir = mkdtempSync(join(tmpdir(), "cpb-"));
  cpSync(example, dir, { recursive: true, filter: (src) => !src.includes(`${join("module-03", "build")}`) });
  return dir;
}

function results(dir) {
  return JSON.parse(readFileSync(join(dir, "build", "checks.json"), "utf8"));
}

function fails(dir) {
  return results(dir).filter((r) => r.result === "fail").map((r) => r.criterion);
}

test("the fictional example passes every script check", { skip }, () => {
  const dir = copyModule();
  try {
    const r = run(["check", dir]);
    assert.equal(r.status, 0, r.stdout + r.stderr);
    assert.deepEqual(fails(dir), []);
    const page = readFileSync(join(dir, "build", "site", "fspg-module03-when-to-wash-and-why-gloves-are-not-enough.html"), "utf8");
    assert.equal((page.match(/<h1[\s>]/g) || []).length, 1);
    assert.ok(!/style="/.test(page), "no inline styles");
    assert.ok(!/https?:\/\//.test(page.replace(/<a [^>]*>/g, "")), "no outside resources");
    const bank = JSON.parse(readFileSync(join(dir, "build", "item-bank.json"), "utf8"));
    assert.ok(bank.length >= 3 && bank.length <= 5);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("a lesson that breaks house style, feedback and problem-first fails the right criteria", { skip }, () => {
  const dir = copyModule();
  try {
    const path = join(dir, "lessons", lessonName);
    // A Windows checkout has CRLF line endings; the edits below assume LF.
    let md = readFileSync(path, "utf8").replace(/\r\n/g, "\n");
    md = md.replace(/:::problem[\s\S]*?\n:::\n/, "In this lesson we will cover handwashing.\n\n");
    md = md.replace(/^\s+Why:.*$/m, "");
    md = md.replace("## Hands are the shortest route to the food", "## Hands are the shortest route to the food\n\nGloves fail" + String.fromCharCode(0x2014) + "often.");
    writeFileSync(path, md);
    const r = run(["check", dir]);
    assert.equal(r.status, 1, r.stdout + r.stderr);
    const f = fails(dir);
    for (const c of ["A1", "R7", "D8"]) assert.ok(f.includes(c), `expected ${c} to fail, got ${f.join(", ")}`);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("package refuses a failing module unless --preview is given", { skip }, () => {
  const dir = copyModule();
  try {
    const path = join(dir, "lessons", lessonName);
    writeFileSync(path, readFileSync(path, "utf8").replace(/\r\n/g, "\n").replace(/^sources:[\s\S]*?(?=^draft:)/m, ""));
    const refused = run(["package", dir]);
    assert.equal(refused.status, 1, refused.stdout + refused.stderr);
    const preview = run(["package", dir, "--preview"]);
    assert.equal(preview.status, 0, preview.stdout + preview.stderr);
    assert.ok(existsSync(join(dir, "build", "fspg-module03-scorm-preview.zip")));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("a passing module packages as SCORM 1.2 with one SCO per lesson", { skip }, () => {
  const dir = copyModule();
  try {
    const r = run(["package", dir]);
    assert.equal(r.status, 0, r.stdout + r.stderr);
    const zip = join(dir, "build", "fspg-module03-scorm.zip");
    assert.ok(existsSync(zip));
    const list = spawnSync(python, ["-c", "import sys,zipfile;z=zipfile.ZipFile(sys.argv[1]);print(z.read('imsmanifest.xml').decode())", zip], { encoding: "utf8" });
    assert.equal(list.status, 0, list.stderr);
    assert.match(list.stdout, /<schemaversion>1\.2<\/schemaversion>/);
    assert.equal((list.stdout.match(/adlcp:scormtype="sco"/g) || []).length, 1);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("blueprint check fails a vague verb and an unmeasured objective", { skip }, () => {
  const dir = mkdtempSync(join(tmpdir(), "cpb-bp-"));
  try {
    const bp = {
      course: "Fictional course", prefix: "fic", credit_hours: 1,
      outcomes: [{ id: "CO1", text: "understand food safety.", bloom: "understand" }],
      objectives: [
        { id: "o1.1", module: 1, text: "identify the five moments for hand hygiene.", bloom: "remember", supports: ["CO1"] },
        { id: "o1.2", module: 1, text: "know glove rules.", bloom: "remember", supports: [] },
      ],
      lessons: [{ module: 1, file: "01-a.md", title: "A", objectives: ["o1.1", "o1.2"], minutes: 12 }],
      assessments: [{ id: "A1", module: 1, title: "Audit", graded: true, objectives: ["o1.1"], minutes: 60 }],
    };
    const path = join(dir, "blueprint.json");
    writeFileSync(path, JSON.stringify(bp));
    const r = run(["blueprint", path]);
    assert.equal(r.status, 1, r.stdout + r.stderr);
    const report = readFileSync(join(dir, "blueprint-checks.md"), "utf8");
    for (const c of ["R1", "R2", "R3"]) assert.match(report, new RegExp(`\\b${c}\\b[^\\n]*fail`, "i"), `expected ${c} fail in:\n${report}`);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("the standard file and its generated page agree", { skip }, () => {
  const std = JSON.parse(readFileSync(join(plugin, "standard", "cp-quality-standard.json"), "utf8"));
  assert.equal(std.criteria.length, 35);
  assert.equal(std.precedence.length, 7);
  const page = readFileSync(join(plugin, "skills", "cp-build", "references", "quality-standard.md"), "utf8");
  for (const c of std.criteria) assert.ok(page.includes(`| ${c.id} |`), `${c.id} missing from quality-standard.md`);
  for (const c of std.criteria) if (c.agent) assert.ok(existsSync(join(plugin, "agents", `${c.agent}.md`)), `${c.agent} agent missing`);
});

test("review agents are read-only", () => {
  for (const name of ["cp-rigor-reviewer", "cp-learning-science-reviewer", "cp-design-reviewer"]) {
    const text = readFileSync(join(plugin, "agents", `${name}.md`), "utf8");
    const tools = text.match(/^tools:\s*(.*)$/m);
    assert.ok(tools, `${name} has no tools line`);
    assert.deepEqual(tools[1].split(",").map((t) => t.trim()).sort(), ["Glob", "Grep", "Read"]);
  }
});
