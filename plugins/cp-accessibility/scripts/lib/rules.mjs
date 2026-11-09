// Static HTML accessibility checks for cp-accessibility.
//
// These checks run on the markup only. They catch the structural problems
// that show up most often in course content. Color contrast, reflow, focus
// visibility, and anything that depends on rendering need a browser-based
// tool and a human review.

export const WCAG = {
  "1.1.1": { name: "Non-text Content", level: "A" },
  "1.2.2": { name: "Captions (Prerecorded)", level: "A" },
  "1.3.1": { name: "Info and Relationships", level: "A" },
  "1.4.2": { name: "Audio Control", level: "A" },
  "2.4.2": { name: "Page Titled", level: "A" },
  "2.4.3": { name: "Focus Order", level: "A" },
  "2.4.4": { name: "Link Purpose (In Context)", level: "A" },
  "2.4.6": { name: "Headings and Labels", level: "AA" },
  "3.1.1": { name: "Language of Page", level: "A" },
  "3.3.2": { name: "Labels or Instructions", level: "A" },
  "4.1.2": { name: "Name, Role, Value", level: "A" },
};

export const DEFAULT_GENERIC_LINK_TEXT = [
  "click here",
  "click",
  "here",
  "this",
  "this link",
  "this page",
  "link",
  "read more",
  "more",
  "learn more",
  "more info",
  "more information",
  "details",
  "continue",
  "go",
  "download",
  "website",
  "page",
  "info",
];

const VOID_TAGS = new Set(["img", "input", "br", "hr", "meta", "link", "source", "track", "area", "base", "col", "embed", "wbr"]);

// ---------------------------------------------------------------------------
// Parsing helpers

function blankOut(text, pattern) {
  return text.replace(pattern, (m) => m.replace(/[^\n]/g, " "));
}

function lineStarts(text) {
  const starts = [0];
  for (let i = 0; i < text.length; i += 1) if (text[i] === "\n") starts.push(i + 1);
  return starts;
}

function positionOf(starts, index) {
  let lo = 0;
  let hi = starts.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (starts[mid] <= index) lo = mid;
    else hi = mid - 1;
  }
  return { line: lo + 1, column: index - starts[lo] + 1 };
}

function parseAttributes(raw) {
  const attrs = new Map();
  const re = /([^\s"'<>\/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;
  let m;
  while ((m = re.exec(raw)) !== null) {
    attrs.set(m[1].toLowerCase(), m[2] ?? m[3] ?? m[4] ?? "");
  }
  return attrs;
}

function tokenize(html) {
  const tags = [];
  const re = /<(\/)?([a-zA-Z][a-zA-Z0-9-]*)([^>]*)>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const name = m[2].toLowerCase();
    const closing = Boolean(m[1]);
    const rawAttrs = closing ? "" : m[3].replace(/\/\s*$/, "");
    tags.push({
      name,
      closing,
      selfClosing: !closing && (/\/\s*$/.test(m[3]) || VOID_TAGS.has(name)),
      attrs: closing ? new Map() : parseAttributes(rawAttrs),
      start: m.index,
      end: m.index + m[0].length,
      raw: m[0],
    });
  }
  return tags;
}

function innerHtml(html, tags, openIndex) {
  const open = tags[openIndex];
  let depth = 0;
  for (let i = openIndex + 1; i < tags.length; i += 1) {
    const t = tags[i];
    if (t.name !== open.name) continue;
    if (!t.closing && !t.selfClosing) depth += 1;
    else if (t.closing) {
      if (depth === 0) return { text: html.slice(open.end, t.start), closeIndex: i };
      depth -= 1;
    }
  }
  return { text: html.slice(open.end), closeIndex: tags.length };
}

function decodeEntities(text) {
  return text
    .replace(/&nbsp;|&#160;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&[a-z]+;|&#\d+;/gi, " ");
}

function visibleText(fragment) {
  const withoutHidden = fragment.replace(/<[^>]*aria-hidden\s*=\s*["']?true["']?[^>]*>[\s\S]*?<\/[^>]+>/gi, " ");
  return decodeEntities(withoutHidden.replace(/<[^>]+>/g, " ")).replace(/\s+/g, " ").trim();
}

function normalizeLinkText(text) {
  return text
    .toLowerCase()
    .replace(/[\s ]+/g, " ")
    .replace(/^[\s.,:;!?"'()\[\]>»-]+|[\s.,:;!?"'()\[\]>»-]+$/g, "")
    .trim();
}

function snippetOf(raw) {
  const oneLine = raw.replace(/\s+/g, " ").trim();
  return oneLine.length > 120 ? oneLine.slice(0, 117) + "..." : oneLine;
}

// ---------------------------------------------------------------------------
// Rules

export const RULES = [
  {
    id: "img-alt",
    criterion: "1.1.1",
    fix: 'Add an alt attribute. Describe the image\'s purpose, or use alt="" when it is purely decorative.',
  },
  {
    id: "link-text-generic",
    criterion: "2.4.4",
    fix: 'Rewrite the link text so it describes the destination, for example "Download the grading rubric (PDF)".',
  },
  {
    id: "link-empty",
    criterion: "2.4.4",
    fix: "Give the link visible text, an aria-label, or an image with meaningful alt text.",
  },
  {
    id: "html-lang",
    criterion: "3.1.1",
    fix: 'Add a lang attribute to the html element, for example <html lang="en">.',
  },
  {
    id: "page-title",
    criterion: "2.4.2",
    fix: "Add a descriptive <title> inside <head> that names the page and the course.",
  },
  {
    id: "heading-skip",
    criterion: "1.3.1",
    fix: "Use heading levels in order. Do not jump from h2 to h4; change the level or add the missing heading.",
  },
  {
    id: "heading-empty",
    criterion: "2.4.6",
    fix: "Give the heading text that describes the section, or remove the empty heading.",
  },
  {
    id: "iframe-title",
    criterion: "4.1.2",
    fix: "Add a title attribute to the iframe that says what it contains, for example the video name.",
  },
  {
    id: "input-label",
    criterion: "3.3.2",
    fix: "Associate a <label for> with the control's id, wrap the control in a <label>, or add aria-label.",
  },
  {
    id: "tabindex-positive",
    criterion: "2.4.3",
    fix: "Remove the positive tabindex. Use tabindex=\"0\" or rely on the natural document order.",
  },
  {
    id: "table-headers",
    criterion: "1.3.1",
    fix: 'Mark header cells with <th scope="col"> or <th scope="row">. For layout tables, add role="presentation".',
  },
  {
    id: "video-captions",
    criterion: "1.2.2",
    fix: 'Add a <track kind="captions"> with a caption file, or link to a captioned version of the video.',
  },
  {
    id: "media-autoplay",
    criterion: "1.4.2",
    fix: "Remove autoplay, or make sure the media is muted and the user has a visible way to pause or stop it.",
  },
];

const RULE_BY_ID = new Map(RULES.map((r) => [r.id, r]));

/**
 * Check an HTML document or fragment.
 * @param {string} html
 * @param {{ disabledRules?: string[], genericLinkText?: string[] }} [options]
 */
export function checkHtml(html, options = {}) {
  const disabled = new Set(options.disabledRules ?? []);
  const generic = new Set([...DEFAULT_GENERIC_LINK_TEXT, ...(options.genericLinkText ?? []).map((s) => s.toLowerCase())]);

  let text = blankOut(html, /<!--[\s\S]*?-->/g);
  text = blankOut(text, /<script\b[^>]*>[\s\S]*?<\/script>/gi);
  text = blankOut(text, /<style\b[^>]*>[\s\S]*?<\/style>/gi);

  const starts = lineStarts(text);
  const tags = tokenize(text);
  const findings = [];

  function report(ruleId, tag, message, atIndex = tag ? tag.start : 0) {
    if (disabled.has(ruleId)) return;
    const rule = RULE_BY_ID.get(ruleId);
    const pos = positionOf(starts, atIndex);
    findings.push({
      rule: rule.id,
      criterion: rule.criterion,
      criterionName: WCAG[rule.criterion].name,
      level: WCAG[rule.criterion].level,
      line: pos.line,
      column: pos.column,
      message,
      fix: rule.fix,
      snippet: tag ? snippetOf(tag.raw) : "",
    });
  }

  // Document-level checks only when the document has the relevant structure.
  const htmlTag = tags.find((t) => t.name === "html" && !t.closing);
  if (htmlTag && !String(htmlTag.attrs.get("lang") ?? "").trim()) {
    report("html-lang", htmlTag, "The html element has no lang attribute.");
  }
  const headIndex = tags.findIndex((t) => t.name === "head" && !t.closing);
  if (headIndex !== -1) {
    const titleIndex = tags.findIndex((t, i) => i > headIndex && t.name === "title" && !t.closing);
    const titleText = titleIndex === -1 ? "" : visibleText(innerHtml(text, tags, titleIndex).text);
    if (!titleText) report("page-title", tags[headIndex], "The document has no non-empty <title>.");
  }

  // Collect label associations.
  const labelledIds = new Set();
  const labelRegions = [];
  tags.forEach((t, i) => {
    if (t.name !== "label" || t.closing) return;
    const forId = t.attrs.get("for");
    if (forId) labelledIds.add(forId.trim());
    const { closeIndex } = innerHtml(text, tags, i);
    labelRegions.push([t.end, closeIndex < tags.length ? tags[closeIndex].start : text.length]);
  });
  const insideLabel = (index) => labelRegions.some(([s, e]) => index >= s && index <= e);

  let lastHeadingLevel = 0;

  tags.forEach((tag, i) => {
    if (tag.closing) return;
    const a = tag.attrs;

    if (tag.name === "img" && !a.has("alt")) {
      report("img-alt", tag, "Image has no alt attribute.");
    }

    if (tag.name === "a" && a.has("href")) {
      const inner = innerHtml(text, tags, i).text;
      const ariaLabel = (a.get("aria-label") ?? "").trim();
      const labelledBy = (a.get("aria-labelledby") ?? "").trim();
      const imgAlt = [...inner.matchAll(/<img\b[^>]*\balt\s*=\s*(?:"([^"]*)"|'([^']*)')/gi)]
        .map((m) => (m[1] ?? m[2] ?? "").trim())
        .filter(Boolean);
      const visible = visibleText(inner);
      const accessibleName = ariaLabel || visible || imgAlt.join(" ") || (a.get("title") ?? "").trim();
      if (!accessibleName && !labelledBy) {
        report("link-empty", tag, "Link has no text or accessible name.");
      } else if (!ariaLabel && !labelledBy && visible && generic.has(normalizeLinkText(visible))) {
        report("link-text-generic", tag, `Link text "${visible}" does not describe the destination.`);
      }
    }

    const heading = tag.name.match(/^h([1-6])$/);
    if (heading) {
      const level = Number(heading[1]);
      const inner = innerHtml(text, tags, i).text;
      const hasImgAlt = /<img\b[^>]*\balt\s*=\s*["'][^"']+["']/i.test(inner);
      if (!visibleText(inner) && !hasImgAlt && !(a.get("aria-label") ?? "").trim()) {
        report("heading-empty", tag, `Heading <h${level}> is empty.`);
      }
      if (lastHeadingLevel && level > lastHeadingLevel + 1) {
        report("heading-skip", tag, `Heading level jumps from h${lastHeadingLevel} to h${level}.`);
      }
      lastHeadingLevel = level;
    }

    if (tag.name === "iframe" && !(a.get("title") ?? "").trim() && !(a.get("aria-label") ?? "").trim()) {
      report("iframe-title", tag, "Frame has no title.");
    }

    if (tag.name === "input" || tag.name === "select" || tag.name === "textarea") {
      const type = (a.get("type") ?? "text").toLowerCase();
      const skip = tag.name === "input" && ["hidden", "submit", "button", "reset", "image"].includes(type);
      if (!skip) {
        const id = (a.get("id") ?? "").trim();
        const named =
          (id && labelledIds.has(id)) ||
          insideLabel(tag.start) ||
          (a.get("aria-label") ?? "").trim() ||
          (a.get("aria-labelledby") ?? "").trim() ||
          (a.get("title") ?? "").trim();
        if (!named) report("input-label", tag, `Form control <${tag.name}> has no associated label.`);
      }
    }

    if (a.has("tabindex") && Number(a.get("tabindex")) > 0) {
      report("tabindex-positive", tag, `tabindex="${a.get("tabindex")}" overrides the natural focus order.`);
    }

    if (tag.name === "table") {
      const role = (a.get("role") ?? "").toLowerCase();
      if (role !== "presentation" && role !== "none") {
        const inner = innerHtml(text, tags, i).text;
        if (!/<th\b/i.test(inner)) report("table-headers", tag, "Data table has no header cells (<th>).");
      }
    }

    if (tag.name === "video") {
      const inner = innerHtml(text, tags, i).text;
      if (!/<track\b[^>]*\bkind\s*=\s*["']?(captions|subtitles)/i.test(inner)) {
        report("video-captions", tag, "Video has no captions track.");
      }
    }

    if ((tag.name === "video" || tag.name === "audio") && a.has("autoplay")) {
      report("media-autoplay", tag, `<${tag.name}> starts automatically.`);
    }
  });

  findings.sort((x, y) => x.line - y.line || x.column - y.column || x.rule.localeCompare(y.rule));
  return findings;
}
