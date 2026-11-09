import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { checkHtml, RULES, WCAG } from "../scripts/lib/rules.mjs";
import { formatMarkdown, resolveConfig } from "../scripts/lib/report.mjs";

const here = dirname(fileURLToPath(import.meta.url));

function rules(findings) {
  return findings.map((f) => f.rule).sort();
}

function page(body, { lang = ' lang="en"', title = "<title>Sample</title>" } = {}) {
  return `<!doctype html><html${lang}><head>${title}</head><body>\n${body}\n</body></html>`;
}

test("a clean page produces no findings", () => {
  const html = page(`
<h1>Welcome</h1>
<img src="a.png" alt="A labeled diagram of the water cycle">
<img src="spacer.png" alt="">
<p><a href="/syllabus.pdf">Download the course syllabus (PDF)</a></p>
<h2>Section</h2>
<table><tr><th scope="col">Week</th><th scope="col">Topic</th></tr><tr><td>1</td><td>Intro</td></tr></table>
<label for="name">Name</label><input id="name" type="text">
<iframe src="https://www.example.com/" title="Course introduction video"></iframe>
<video controls><source src="v.mp4"><track kind="captions" src="v.vtt" srclang="en" label="English"></video>`);
  assert.deepEqual(checkHtml(html), []);
});

test("reports a missing alt attribute with WCAG 1.1.1", () => {
  const findings = checkHtml(page(`<img src="chart.png">`));
  assert.equal(findings.length, 1);
  assert.equal(findings[0].rule, "img-alt");
  assert.equal(findings[0].criterion, "1.1.1");
  assert.equal(findings[0].level, "A");
  assert.equal(findings[0].line, 2);
});

test("reports generic link text with WCAG 2.4.4", () => {
  const findings = checkHtml(page(`<p>For the rubric, <a href="rubric.html">click here</a>.</p>\n<a href="x.html">Read More</a>\n<a href="y.html"><strong>here</strong></a>`));
  assert.deepEqual(rules(findings), ["link-text-generic", "link-text-generic", "link-text-generic"]);
  assert.ok(findings.every((f) => f.criterion === "2.4.4"));
  assert.deepEqual(findings.map((f) => f.line), [2, 3, 4]);
});

test("a generic link with a descriptive aria-label is accepted", () => {
  const findings = checkHtml(page(`<a href="rubric.html" aria-label="Open the grading rubric">click here</a>`));
  assert.deepEqual(findings, []);
});

test("reports empty links", () => {
  const findings = checkHtml(page(`<a href="x.html"></a><a href="y.html"><img src="i.png" alt=""></a><a href="z.html"><img src="i.png" alt="Zoo map"></a>`));
  assert.deepEqual(rules(findings), ["link-empty", "link-empty"]);
});

test("reports missing lang and missing title", () => {
  const findings = checkHtml(page(`<p>Hi</p>`, { lang: "", title: "" }));
  assert.deepEqual(rules(findings), ["html-lang", "page-title"]);
  assert.equal(findings.find((f) => f.rule === "html-lang").criterion, "3.1.1");
  assert.equal(findings.find((f) => f.rule === "page-title").criterion, "2.4.2");
});

test("fragments without html or head tags skip lang and title checks", () => {
  assert.deepEqual(checkHtml(`<h1>Topic</h1><p>Fragment for Brightspace.</p>`), []);
});

test("reports heading level skips and empty headings", () => {
  const findings = checkHtml(page(`<h1>Title</h1>\n<h3>Skipped</h3>\n<h4></h4>`));
  assert.deepEqual(rules(findings), ["heading-empty", "heading-skip"]);
  assert.equal(findings.find((f) => f.rule === "heading-skip").criterion, "1.3.1");
  assert.equal(findings.find((f) => f.rule === "heading-empty").criterion, "2.4.6");
});

test("reports iframes without a title", () => {
  const findings = checkHtml(page(`<iframe src="https://www.example.com/"></iframe><iframe src="b" title=""></iframe>`));
  assert.deepEqual(rules(findings), ["iframe-title", "iframe-title"]);
  assert.equal(findings[0].criterion, "4.1.2");
});

test("reports form controls without labels", () => {
  const html = page(`
<input type="text" id="unlabeled">
<input type="hidden" name="token">
<input type="submit" value="Send">
<label>Email <input type="email"></label>
<select id="pick"><option>One</option></select>
<label for="pick">Pick</label>
<textarea aria-label="Comments"></textarea>
<textarea></textarea>`);
  const findings = checkHtml(html);
  assert.deepEqual(rules(findings), ["input-label", "input-label"]);
  assert.ok(findings.every((f) => f.criterion === "3.3.2"));
});

test("reports positive tabindex, tables without headers, and media issues", () => {
  const html = page(`
<div tabindex="3">x</div>
<table><tr><td>a</td></tr></table>
<table role="presentation"><tr><td>layout</td></tr></table>
<video controls><source src="v.mp4"></video>
<audio autoplay src="a.mp3"></audio>`);
  const findings = checkHtml(html);
  assert.deepEqual(rules(findings), ["media-autoplay", "tabindex-positive", "table-headers", "video-captions"]);
  assert.equal(findings.find((f) => f.rule === "video-captions").criterion, "1.2.2");
  assert.equal(findings.find((f) => f.rule === "tabindex-positive").criterion, "2.4.3");
});

test("disabled rules and extra generic phrases come from config", () => {
  const html = page(`<img src="a.png"><a href="b.html">tap this</a>`);
  const findings = checkHtml(html, { disabledRules: ["img-alt"], genericLinkText: ["tap this"] });
  assert.deepEqual(rules(findings), ["link-text-generic"]);
});

test("every rule maps to a WCAG criterion with a name and level", () => {
  for (const rule of RULES) {
    const c = WCAG[rule.criterion];
    assert.ok(c, `${rule.id} points at unknown criterion ${rule.criterion}`);
    assert.ok(c.name && /^(A|AA)$/.test(c.level));
    assert.ok(rule.fix.length > 10, `${rule.id} needs a fix hint`);
  }
});

test("the shipped sample reports the missing alt and the click-here link", () => {
  const sample = readFileSync(join(here, "..", "samples", "needs-work.html"), "utf8");
  const findings = checkHtml(sample);
  const ids = rules(findings);
  assert.ok(ids.includes("img-alt"));
  assert.ok(ids.includes("link-text-generic"));
});

test("markdown report lists each finding with its criterion", () => {
  const findings = checkHtml(page(`<img src="chart.png">`)).map((f) => ({ ...f, path: "sample.html" }));
  const md = formatMarkdown([{ path: "sample.html", findings }]);
  assert.ok(md.includes("sample.html"));
  assert.ok(md.includes("1.1.1"));
  assert.ok(md.includes("Non-text Content"));
  assert.ok(!md.includes(String.fromCharCode(0x2014)), "report must not contain em-dashes");
});

test("config resolution tolerates a missing or invalid config file", () => {
  const missing = resolveConfig(join(here, "does-not-exist.json"));
  assert.deepEqual(missing.disabledRules, []);
  assert.deepEqual(missing.genericLinkText, []);
  assert.equal(missing.format, "markdown");
  const invalid = resolveConfig(join(here, "check.test.mjs"));
  assert.deepEqual(invalid.disabledRules, []);
});
