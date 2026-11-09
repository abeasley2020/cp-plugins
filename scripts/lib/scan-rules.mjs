// Content scan rules for the cp-plugins repository.
//
// Every rule is a plain regular expression plus an optional filter. Rules run
// line by line so findings carry a line and column. Keep this file free of
// literal examples of the things it detects: the scan runs on itself.

const PUBLIC_HOSTS = new Set([
  "purdue.edu",
  "www.purdue.edu",
  "online.purdue.edu",
]);

// Hosts or host suffixes that point at systems only the team can reach.
const INTERNAL_HOST_SUFFIXES = [
  ".sharepoint.com",
  ".sharepoint-df.com",
  ".brightspace.com",
  ".purdue.edu",
  ".local",
  ".internal",
  ".intranet",
  ".corp",
  ".lan",
];

// Built from parts so this file passes its own scan.
const INTERNAL_HOST_EXACT = new Set([["local", "host"].join(""), ["teams", "microsoft", "com"].join(".")]);

const ORG_WORDS =
  /\b(team|production|university|online|purdue|office|group|department|course|college|school|center|centre|services?|unit|program|committee|staff|support)\b/i;

function isPrivateIp(host) {
  const m = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (!m) return false;
  const a = Number(m[1]);
  const b = Number(m[2]);
  if (a === 10 || a === 127) return true;
  if (a === 192 && b === 168) return true;
  if (a === 172 && b >= 16 && b <= 31) return true;
  if (a === 169 && b === 254) return true;
  return false;
}

function isInternalHost(rawHost) {
  const host = rawHost.toLowerCase().replace(/:\d+$/, "");
  if (PUBLIC_HOSTS.has(host)) return false;
  if (INTERNAL_HOST_EXACT.has(host)) return true;
  if (isPrivateIp(host)) return true;
  return INTERNAL_HOST_SUFFIXES.some((suffix) => host.endsWith(suffix));
}

function looksLikePersonName(name) {
  const trimmed = name.trim();
  if (ORG_WORDS.test(trimmed)) return false;
  const words = trimmed.split(/\s+/);
  if (words.length < 2 || words.length > 3) return false;
  return words.every((w) => /^[A-Z][a-z'-]+\.?$/.test(w));
}

const HOST_PATTERN = "(?:[a-z0-9-]+\\.)+[a-z]{2,}|localhost|\\d{1,3}(?:\\.\\d{1,3}){3}";

export const RULES = [
  {
    id: "dollar-amount",
    message: "Dollar amount. Budgets, quotes, and rates stay out of this public repository.",
    pattern: /\$\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?(?:USD|dollars)\b/gi,
  },
  {
    id: "email-address",
    message: "Email address. Use a role description instead of a personal or team address.",
    pattern: /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}/g,
  },
  {
    id: "internal-url",
    message: "Internal URL or host. Only public documentation links belong in this repository.",
    pattern: new RegExp("(?:https?://)?(" + HOST_PATTERN + ")(?::\\d+)?(?=[/\\s'\"<>)\\]]|$)", "gi"),
    accept: (match) => isInternalHost(match[1]),
  },
  {
    id: "credential",
    message: "Credential-like value. Secrets never belong in the repository.",
    pattern: new RegExp(
      [
        "sk-ant-[A-Za-z0-9_-]{10,}",
        "AKIA[0-9A-Z]{16}",
        "gh[pousr]_[A-Za-z0-9]{20,}",
        "github_pat_[A-Za-z0-9_]{20,}",
        "xox[baprs]-[A-Za-z0-9-]{10,}",
        "-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "\\bBearer\\s+[A-Za-z0-9._-]{20,}",
        "\\beyJ[A-Za-z0-9_-]{10,}\\.[A-Za-z0-9_-]{10,}",
        "\\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?key[_-]?id|secret[_-]?access[_-]?key|token)\\s*[:=]\\s*['\"]?[^\\s'\",;]{8,}",
      ].join("|"),
      "gi"
    ),
  },
  {
    id: "person-name",
    message: "Looks like a real person's name. Credit teams and roles, not individuals.",
    pattern: new RegExp(
      [
        // Bylines: a label such as author or contact, followed by a capitalized full name or an honorific and surname
        "\\b(?:[Aa]uthor|[Cc]ontact|[Oo]wner|[Mm]aintainer|[Ww]ritten [Bb]y|[Cc]reated [Bb]y|[Rr]eviewed [Bb]y|[Aa]pproved [Bb]y|[Pp]repared [Bb]y)\\s*:?\\s+((?:(?:Dr|Prof|Mr|Mrs|Ms|Mx)\\.\\s+)?[A-Z][a-z'-]+(?:\\s+[A-Z][a-z'-]+){0,2})",
        // JSON author name fields
        "\"author\"\\s*:\\s*\\{\\s*\"name\"\\s*:\\s*\"([^\"]+)\"",
      ].join("|"),
      "g"
    ),
    accept: (match) => {
      const candidate = match[1] ?? match[2] ?? "";
      const stripped = candidate.replace(/^(?:Dr|Prof|Mr|Mrs|Ms|Mx)\.\s+/, "");
      if (/^(?:Dr|Prof|Mr|Mrs|Ms|Mx)\./.test(candidate)) return !ORG_WORDS.test(stripped);
      return looksLikePersonName(stripped);
    },
  },
  {
    id: "em-dash",
    message: "Em-dash. Rewrite with a comma, a period, or a colon.",
    pattern: new RegExp([String.fromCharCode(0x2014), "&" + "mdash;", "&#" + "8212;", "&#" + "x2014;"].join("|"), "gi"),
  },
];

export const RULE_IDS = RULES.map((r) => r.id);

function redact(line, column, length) {
  const start = Math.max(0, column - 20);
  const end = Math.min(line.length, column + length + 20);
  const before = line.slice(start, column);
  const after = line.slice(column + length, end);
  const hidden = length <= 4 ? "*".repeat(length) : line.slice(column, column + 2) + "*".repeat(length - 2);
  return (start > 0 ? "..." : "") + before + hidden + after + (end < line.length ? "..." : "");
}

/**
 * Scan a block of text and return findings.
 * @param {string} text
 * @param {{ path?: string }} [options]
 * @returns {Array<{ rule: string, message: string, line: number, column: number, snippet: string, path?: string }>}
 */
export function scanText(text, options = {}) {
  const findings = [];
  const lines = text.split(/\r?\n/);
  lines.forEach((lineText, index) => {
    for (const rule of RULES) {
      rule.pattern.lastIndex = 0;
      let match;
      while ((match = rule.pattern.exec(lineText)) !== null) {
        if (match[0].length === 0) {
          rule.pattern.lastIndex += 1;
          continue;
        }
        if (rule.accept && !rule.accept(match)) continue;
        findings.push({
          rule: rule.id,
          message: rule.message,
          line: index + 1,
          column: match.index + 1,
          snippet: redact(lineText, match.index, match[0].length),
          ...(options.path ? { path: options.path } : {}),
        });
      }
    }
  });
  return findings;
}
