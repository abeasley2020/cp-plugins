import { test } from "node:test";
import assert from "node:assert/strict";
import { scanText, RULE_IDS } from "../lib/scan-rules.mjs";

// Fixtures are assembled at runtime so this test file itself passes the scan.
const at = String.fromCharCode(64);
const dollar = String.fromCharCode(36);
const emDash = String.fromCharCode(0x2014);

function ruleIds(findings) {
  return findings.map((f) => f.rule).sort();
}

test("clean text produces no findings", () => {
  const text = [
    "# cp-plugins",
    "Install with /plugin marketplace add and then /plugin install cp-accessibility" + at + "cp-plugins.",
    "See https://www.purdue.edu/ and https://github.com/example/repo for details.",
    "Use actions/checkout" + at + "v4 in CI. The variable is " + dollar + "ARGUMENTS.",
  ].join("\n");
  assert.deepEqual(scanText(text), []);
});

test("detects dollar amounts in several forms", () => {
  const text = [
    "The quote came to " + dollar + "1,250.00 per module.",
    "Budget: " + dollar + "500",
    "About 12,000 " + "USD was approved.",
  ].join("\n");
  const findings = scanText(text);
  assert.equal(findings.length, 3);
  assert.ok(findings.every((f) => f.rule === "dollar-amount"));
  assert.deepEqual(findings.map((f) => f.line), [1, 2, 3]);
});

test("detects email addresses but not plugin or action specs", () => {
  const text = [
    "Contact: someone" + at + "example.com",
    "Run /plugin install cp-accessibility" + at + "cp-plugins",
    "uses: actions/setup-node" + at + "v4",
  ].join("\n");
  const findings = scanText(text);
  assert.deepEqual(ruleIds(findings), ["email-address"]);
  assert.equal(findings[0].line, 1);
});

test("detects internal URLs and allows public ones", () => {
  const sp = ["purdue", "sharepoint", "com"].join(".");
  const bs = ["purdue", "brightspace", "com"].join(".");
  const sub = ["intranet", "purdue", "edu"].join(".");
  const text = [
    "https://" + sp + "/sites/team/Shared%20Documents/file.docx",
    "https://" + bs + "/d2l/home/12345",
    "https://" + sub + "/portal",
    "http://10.0.0." + "5/admin",
    "http://" + ["local", "host"].join("") + ":3000/",
    "https://www.purdue.edu/accessibility/",
    "https://online.purdue.edu/",
    "https://docs.anthropic.com/en/docs/claude-code/plugins",
  ].join("\n");
  const findings = scanText(text);
  assert.ok(findings.every((f) => f.rule === "internal-url"));
  assert.deepEqual(findings.map((f) => f.line), [1, 2, 3, 4, 5]);
});

test("detects credential patterns", () => {
  const anthropicKey = ["sk", "ant", "api03", "abcdefghijklmnopqrstuvwxyz0123456789"].join("-");
  const awsKey = "AKIA" + "ABCDEFGHIJKLMNOP";
  const ghToken = "ghp_" + "abcdefghijklmnopqrstuvwxyz0123456789ABCD";
  const text = [
    "ANTHROPIC_API_KEY=" + anthropicKey,
    "aws_access_key_id = " + awsKey,
    "token: " + ghToken,
    "password = " + "hunter2hunter2",
    "-----BEGIN RSA " + "PRIVATE KEY-----",
    "Authorization: Bearer " + "abcdefghijklmnopqrstuvwxyz0123456789",
  ].join("\n");
  const findings = scanText(text);
  assert.equal(findings.length, 6);
  assert.ok(findings.every((f) => f.rule === "credential"));
});

test("does not flag prose that merely mentions passwords or keys", () => {
  const text = [
    "Never commit a password or an API key to this repository.",
    "The scan looks for api_key assignments.",
  ].join("\n");
  assert.deepEqual(scanText(text), []);
});

test("flags person-like names in bylines and author fields, not team names", () => {
  const first = "Jordan";
  const last = "Example";
  const text = [
    "Author: " + first + " " + last,
    '"author": { "name": "' + first + " " + last + '" }',
    '"author": { "name": "Purdue University Online Course Production" }',
    "Created by the Course Production team",
    "Written by Dr. " + last,
  ].join("\n");
  const findings = scanText(text);
  assert.ok(findings.every((f) => f.rule === "person-name"));
  assert.deepEqual(findings.map((f) => f.line), [1, 2, 5]);
});

test("flags em-dashes as characters and as entities", () => {
  const text = [
    "A sentence " + emDash + " with a dash.",
    "A &" + "mdash; entity.",
    "A plain - hyphen and an en dash: 2020-2021.",
  ].join("\n");
  const findings = scanText(text);
  assert.ok(findings.every((f) => f.rule === "em-dash"));
  assert.deepEqual(findings.map((f) => f.line), [1, 2]);
});

test("reports line numbers, columns, and redacted snippets", () => {
  const text = "ok\nok\nTotal " + dollar + "99 due\n";
  const [f] = scanText(text);
  assert.equal(f.line, 3);
  assert.equal(f.column, 7);
  assert.ok(f.snippet.includes("Total"));
  assert.ok(f.message.length > 0);
});

test("exposes the full list of rule ids", () => {
  assert.deepEqual(
    [...RULE_IDS].sort(),
    ["credential", "dollar-amount", "em-dash", "email-address", "internal-url", "person-name"]
  );
});
