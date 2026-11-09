#!/usr/bin/env node
// a11y_check.mjs: run axe-core (WCAG 2.0, 2.1 and 2.2 A and AA rules) on every
// HTML page in the given folders and write axe-results.json.
//
//   node a11y_check.mjs <folder-or-file> [...] --out axe-results.json
//
// Engine: headless Chromium through Playwright when it is installed
// (see Setup in the plugin README). That is the full check: layout-based
// rules such as color-contrast and target-size run, and every page is also
// loaded at 320 px wide to confirm it reflows with no horizontal scroll
// (WCAG 1.4.10). Without Chromium it falls back to jsdom: every structural
// rule still runs, but layout rules come back "incomplete", so a11y_static.py
// covers contrast, target size and reflow from the CSS instead. The engine
// used is recorded in the results so the report says which one ran.

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const axePath = require.resolve("axe-core/axe.min.js");
const axeSource = fs.readFileSync(axePath, "utf8");
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

const args = process.argv.slice(2);
const outIdx = args.indexOf("--out");
const out = outIdx >= 0 ? args[outIdx + 1] : "axe-results.json";
const inputs = args.filter((a, i) => a !== "--out" && i !== outIdx + 1);
const forceJsdom = args.includes("--jsdom");

function collect(p, acc) {
  const st = fs.statSync(p);
  if (st.isDirectory()) {
    for (const f of fs.readdirSync(p).sort()) collect(path.join(p, f), acc);
  } else if (p.endsWith(".html")) acc.push(path.resolve(p));
  return acc;
}
const files = inputs.flatMap((p) => collect(p, []));
if (!files.length) {
  console.error("No HTML files found.");
  process.exit(2);
}

function slim(results) {
  const pick = (list) => list.map((r) => ({
    id: r.id, impact: r.impact, help: r.help, tags: r.tags.filter((t) => t.startsWith("wcag")),
    nodes: r.nodes.slice(0, 5).map((n) => n.target.join(" ")),
  }));
  return { violations: pick(results.violations), incomplete: pick(results.incomplete), passes: results.passes.length };
}

async function withChromium() {
  let pw;
  try { pw = await import("playwright"); } catch { return null; }
  let browser;
  try { browser = await pw.chromium.launch(); } catch { return null; }
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const report = [];
  for (const f of files) {
    await page.goto("file://" + f);
    await page.addScriptTag({ content: axeSource });
    const res = await page.evaluate(async (tags) => await window.axe.run(document, { runOnly: { type: "tag", values: tags } }), TAGS);
    await page.setViewportSize({ width: 320, height: 800 });
    const reflow = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
    await page.setViewportSize({ width: 1280, height: 900 });
    report.push({ file: f, reflow_320: reflow, ...slim(res) });
  }
  await browser.close();
  return { engine: "chromium (playwright)", pages: report };
}

async function withJsdom() {
  const { JSDOM, VirtualConsole } = await import("jsdom");
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => { if (!/Not implemented/.test(e.message)) console.error(e.message); });
  const report = [];
  for (const f of files) {
    const html = fs.readFileSync(f, "utf8").replace(/<script\b[^>]*src=[^>]*><\/script>/gi, "");
    const dom = new JSDOM(html, { runScripts: "outside-only", pretendToBeVisual: true, url: "file://" + f, virtualConsole: vc });
    dom.window.eval(axeSource);
    const res = await dom.window.axe.run(dom.window.document, { runOnly: { type: "tag", values: TAGS } });
    report.push({ file: f, reflow_320: null, ...slim(res) });
    dom.window.close();
  }
  return { engine: "jsdom (no layout: contrast, target size and reflow checked by a11y_static.py)", pages: report };
}

const result = (!forceJsdom && (await withChromium())) || (await withJsdom());
result.axe_version = JSON.parse(fs.readFileSync(path.join(path.dirname(axePath), "package.json"), "utf8")).version;
result.tags = TAGS;
fs.writeFileSync(out, JSON.stringify(result, null, 2));
const v = result.pages.reduce((n, p) => n + p.violations.length, 0);
const inc = result.pages.reduce((n, p) => n + p.incomplete.length, 0);
console.log(`axe-core ${result.axe_version} via ${result.engine}`);
console.log(`${result.pages.length} pages, ${v} violation(s), ${inc} incomplete check(s) -> ${out}`);
for (const p of result.pages) for (const x of p.violations) console.log(`  VIOLATION ${path.basename(p.file)} ${x.id}: ${x.help} (${x.nodes[0]})`);
process.exit(v ? 1 : 0);
