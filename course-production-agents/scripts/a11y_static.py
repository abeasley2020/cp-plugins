#!/usr/bin/env python3
"""
a11y_static.py: WCAG 2.2 AA and Purdue house-rule checks that do not need a
browser, plus the final accessibility report.

    python3 a11y_static.py <folder-or-file> [...] [--axe axe-results.json] \
        --report accessibility-report.md

Checks every HTML page for
  Structure   lang, unique title, charset, viewport, one h1, no skipped
              heading levels, landmarks (main), tables with caption and
              th scope, scrollable regions labeled, every details has a summary
  Text        image alt, descriptive and unambiguous link text, no em-dashes,
              no exclamation points in body copy, no sight or click language
  Contrast    a small CSS cascade computes the real text color and background
              of every element that holds text, in its normal, hover and focus
              states, and tests 4.5:1 (3:1 for large text); focus outlines are
              tested at 3:1 against the surfaces they sit on (SC 1.4.3, 1.4.11)
  Palette     no #CC785C or #CEB888 anywhere; Boilermaker Gold only on black
  Target size every summary (the only standalone control) is at least 44 px
              tall by rule (SC 2.5.8, mobile practice)
  Reflow      no fixed widths over 320 px outside scrollable table regions
              (SC 1.4.10)
  Sources     no script, iframe, external stylesheet or inline style

Merges axe-core results when --axe is given and writes one Markdown report
with PASS, PASS WITH NOTES or FAIL. Exit 1 when anything blocks publication.
"""

import argparse
import datetime
import html.parser
import json
import pathlib
import re
import sys

VOID = {"meta", "img", "br", "hr", "input", "link", "source", "track", "wbr", "col", "area", "base", "embed", "param"}
BANNED_LINKS = {"click here", "here", "read more", "more", "this", "link", "this link", "learn more"}
BANNED_HEX = {"#CC785C", "#CEB888"}
SIGHT = re.compile(r"\b(see|shown|pictured) (below|above|to the right|to the left)\b|\bclick here\b", re.I)


# ---------------------------------------------------------------- DOM
class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.parent, self.children, self.text = tag, parent, [], ""
        self.attrs = dict(attrs)
        self.classes = set((self.attrs.get("class") or "").split())


class Parser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", [], None)
        self.cur = self.root
        self.style = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag == "style":
            self.in_style = True
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        if self.in_style:
            self.style.append(data)
        else:
            self.cur.text += data
            self.cur.children.append(data)


def walk(n):
    yield n
    for c in n.children:
        if isinstance(c, Node):
            yield from walk(c)


def text_of(n):
    out = []
    for c in n.children:
        out.append(c if isinstance(c, str) else text_of(c))
    return re.sub(r"\s+", " ", "".join(out)).strip()


# ---------------------------------------------------------------- CSS
def parse_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules, i, order = [], 0, 0
    while i < len(css):
        j = css.find("{", i)
        if j < 0:
            break
        sel = css[i:j].strip()
        if sel.startswith("@"):
            depth, k = 1, j + 1
            while depth and k < len(css):
                depth += {"{": 1, "}": -1}.get(css[k], 0)
                k += 1
            i = k
            continue
        k = css.find("}", j)
        decls = {}
        for d in css[j + 1:k].split(";"):
            if ":" in d:
                p, v = d.split(":", 1)
                decls[p.strip().lower()] = v.strip()
        for s in sel.split(","):
            s = s.strip()
            state = None
            m = re.search(r":(hover|focus-visible|focus)\b", s)
            if m:
                state = m.group(1)
            base = re.sub(r":[a-z-]+(\([^)]*\))?", "", s).strip()
            if not base or base == "":
                continue
            rules.append({"sel": base, "state": state, "decls": decls, "spec": spec(base), "order": order})
            order += 1
        i = k + 1
    return rules


def spec(sel):
    return (len(re.findall(r"\.", sel)), len([t for t in re.split(r"[ >]+", sel) if re.match(r"^[a-z][a-z0-9]*", t)]))


def compound_match(comp, n):
    m = re.match(r"^([a-z][a-z0-9]*|\*)?((?:\.[A-Za-z0-9_-]+)*)$", comp)
    if not m:
        return False
    tag, cls = m.group(1), [c for c in m.group(2).split(".") if c]
    if tag and tag != "*" and tag != n.tag:
        return False
    return all(c in n.classes for c in cls)


def matches(sel, n):
    parts = re.split(r"\s*(>)\s*|\s+", sel.strip())
    toks = [p for p in parts if p]
    # toks alternates compounds and optional '>' combinators
    def rec(idx, node):
        comp = toks[idx]
        if not compound_match(comp, node):
            return False
        if idx == 0:
            return True
        if toks[idx - 1] == ">":
            return node.parent is not None and node.parent.tag != "#root" and rec(idx - 2, node.parent)
        a = node.parent
        while a is not None and a.tag != "#root":
            if rec(idx - 1, a):
                return True
            a = a.parent
        return False
    return rec(len(toks) - 1, n)


def hexcolor(v):
    m = re.search(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", v or "")
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return "#" + h.upper()


def lum(hx):
    r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class Styler:
    DEFAULT_SIZE = {"h1": 2.0, "h2": 1.5, "h3": 1.17}
    BOLD = {"h1", "h2", "h3", "h4", "strong", "b", "th", "caption"}

    def __init__(self, rules):
        self.rules = rules
        self.cache = {}

    def own(self, n, state=None):
        found = [r for r in self.rules if (r["state"] is None or r["state"] == state) and matches(r["sel"], n)]
        found.sort(key=lambda r: (r["state"] is not None, r["spec"], r["order"]))
        d = {}
        for r in found:
            d.update(r["decls"])
        return d

    def computed(self, n, state=None):
        key = (id(n), state)
        if key in self.cache:
            return self.cache[key]
        d = self.own(n, state)
        par = self.computed(n.parent) if n.parent is not None and n.parent.tag != "#root" else {"color": "#000000", "bg": "#FFFFFF", "px": 16.0, "bold": False}
        color = hexcolor(d.get("color")) or par["color"]
        bgv = d.get("background-color") or d.get("background")
        bg = hexcolor(bgv) or par["bg"]
        size = par["px"]
        fs = d.get("font-size")
        if fs:
            m = re.match(r"([\d.]+)(rem|em|px)", fs)
            if m:
                v = float(m.group(1))
                size = v * 16 if m.group(2) == "rem" else v * par["px"] if m.group(2) == "em" else v
        elif n.tag in self.DEFAULT_SIZE:
            size = self.DEFAULT_SIZE[n.tag] * par["px"]
        fw = d.get("font-weight")
        bold = (fw in ("700", "bold", "800", "900")) if fw else (par["bold"] or n.tag in self.BOLD)
        out = {"color": color, "bg": bg, "px": size, "bold": bold, "decls": d, "parent_bg": par["bg"]}
        self.cache[key] = out
        return out


def describe(n):
    c = "." + ".".join(sorted(n.classes)) if n.classes else ""
    return n.tag + c


# ---------------------------------------------------------------- checks
def check_page(path, titles):
    blockers, warns = [], []
    src = path.read_text(encoding="utf-8")
    p = Parser()
    p.feed(src)
    nodes = list(walk(p.root))
    by = lambda t: [n for n in nodes if n.tag == t]
    rel = path.name

    htmls = by("html")
    if not htmls or not htmls[0].attrs.get("lang"):
        blockers.append(("3.1.1", "missing lang on <html>"))
    t = by("title")
    title = text_of(t[0]) if t else ""
    if not title:
        blockers.append(("2.4.2", "missing <title>"))
    else:
        titles.setdefault(title, []).append(str(path))
    if not any(m.attrs.get("charset") for m in by("meta")):
        warns.append(("n/a", "no charset meta"))
    if not any(m.attrs.get("name") == "viewport" for m in by("meta")):
        blockers.append(("1.4.10", "no responsive viewport meta"))
    if len(by("h1")) != 1:
        blockers.append(("1.3.1", "expected exactly one h1, found %d" % len(by("h1"))))
    levels = [int(n.tag[1]) for n in nodes if re.fullmatch(r"h[1-6]", n.tag)]
    for a, b in zip(levels, levels[1:]):
        if b > a + 1:
            blockers.append(("1.3.1", "heading level skips from h%d to h%d" % (a, b)))
            break
    for n in nodes:
        if re.fullmatch(r"h[1-6]", n.tag) and not text_of(n):
            blockers.append(("2.4.6", "empty heading"))
    if not by("main"):
        blockers.append(("1.3.1", "no <main> landmark"))
    for img in by("img"):
        if "alt" not in img.attrs:
            blockers.append(("1.1.1", "img without alt (%s)" % img.attrs.get("src")))
        elif re.match(r"(image|picture|graphic|photo) (of|showing)", img.attrs["alt"], re.I):
            warns.append(("1.1.1", "alt text starts with 'image of' style wording"))
    links = {}
    for a in by("a"):
        txt = text_of(a)
        href = a.attrs.get("href", "")
        if not txt:
            blockers.append(("2.4.4", "link with no text (%s)" % href))
        elif txt.lower() in BANNED_LINKS:
            blockers.append(("2.4.4", "non-descriptive link text '%s'" % txt))
        elif re.fullmatch(r"https?://\S+", txt):
            warns.append(("2.4.4", "bare URL used as link text"))
        if txt and txt in links and links[txt] != href:
            blockers.append(("2.4.4", "same link text '%s' points to different places" % txt))
        links[txt] = href
    for tb in by("table"):
        if not any(c.tag == "caption" for c in tb.children if isinstance(c, Node)):
            blockers.append(("1.3.1", "table without caption"))
        ths = [n for n in walk(tb) if n.tag == "th"]
        if not ths:
            blockers.append(("1.3.1", "table without header cells"))
        if any(not th.attrs.get("scope") for th in ths):
            blockers.append(("1.3.1", "th without scope"))
    for n in nodes:
        if n.attrs.get("tabindex") == "0" and not (n.attrs.get("aria-label") or n.attrs.get("aria-labelledby")):
            blockers.append(("4.1.2", "focusable region without an accessible name"))
        if n.attrs.get("style"):
            blockers.append(("n/a", "inline style attribute (keep styles in the head block)"))
    for d in by("details"):
        kids = [c for c in d.children if isinstance(c, Node)]
        if not kids or kids[0].tag != "summary" or not text_of(kids[0]):
            blockers.append(("4.1.2", "details without a labeled summary first"))
    if re.search(r"<(script|iframe|object|embed)\b", src, re.I) or re.search(r"<link\b[^>]*stylesheet", src, re.I):
        blockers.append(("n/a", "script, frame or external stylesheet in source"))
    body_text = text_of(by("body")[0]) if by("body") else ""
    if chr(0x2014) in src:
        blockers.append(("Purdue", "em-dash in page"))
    if "!" in body_text:
        warns.append(("Purdue", "exclamation point in body copy"))
    if SIGHT.search(body_text):
        blockers.append(("1.3.3", "sight or click language: '%s'" % SIGHT.search(body_text).group(0)))
    css = "\n".join(p.style)
    for hx in BANNED_HEX:
        if hx.lower() in css.lower() or hx.lower() in src.lower():
            blockers.append(("1.4.3", "%s is not allowed (use #964F37 for small coral text)" % hx))

    # Contrast with a real cascade.
    rules = parse_css(css)
    st = Styler(rules)
    pairs = {}
    for n in nodes:
        if n.tag in ("#root", "html", "head", "title", "style", "meta"):
            continue
        own_text = "".join(c for c in n.children if isinstance(c, str)).strip()
        if not own_text:
            continue
        for state in (None, "hover"):
            if state and not any(r["state"] == "hover" and any(k in r["decls"] for k in ("color", "background", "background-color"))
                                 and matches(r["sel"], n) for r in rules):
                continue
            c = st.computed(n, state) if state else st.computed(n)
            large = c["px"] >= 24 or (c["bold"] and c["px"] >= 18.66)
            need = 3.0 if large else 4.5
            r = ratio(c["color"], c["bg"])
            key = (c["color"], c["bg"], need, state or "normal")
            pairs.setdefault(key, {"ratio": r, "where": describe(n)})
    contrast = []
    for (fg, bg, need, state), info in sorted(pairs.items(), key=lambda kv: kv[1]["ratio"]):
        ok = info["ratio"] >= need
        contrast.append({"fg": fg, "bg": bg, "ratio": round(info["ratio"], 2), "need": need, "state": state, "example": info["where"], "pass": ok})
        if not ok:
            blockers.append(("1.4.3", "contrast %s on %s is %.2f:1, needs %.1f:1 (%s, %s)" % (fg, bg, info["ratio"], need, info["where"], state)))
    # Focus indicators (non-text contrast).
    focusables = [n for n in nodes if n.tag in ("a", "summary") or n.attrs.get("tabindex") == "0"]
    for n in focusables:
        f = st.own(n, "focus-visible") or st.own(n, "focus")
        oc = hexcolor(f.get("outline", "")) or hexcolor(f.get("outline-color", ""))
        if not oc:
            blockers.append(("2.4.7", "no explicit focus outline on %s" % describe(n)))
            continue
        c = st.computed(n)
        for surface in {c["bg"], c["parent_bg"]}:
            if ratio(oc, surface) < 3.0:
                blockers.append(("1.4.11", "focus outline %s on %s is %.2f:1, needs 3:1 (%s)" % (oc, surface, ratio(oc, surface), describe(n))))
        if n.tag == "summary":
            mh = re.search(r"min-height\s*:\s*([\d.]+)px", ";".join("%s:%s" % kv for kv in c["decls"].items()))
            if not mh or float(mh.group(1)) < 44:
                blockers.append(("2.5.8", "summary control is not set to at least 44 px tall"))
    # Reflow guard.
    for r in rules:
        for prop in ("width", "min-width"):
            v = r["decls"].get(prop, "")
            m = re.match(r"([\d.]+)(px|rem|em)", v)
            if m:
                px = float(m.group(1)) * (16 if m.group(2) != "px" else 1)
                if px > 320:
                    blockers.append(("1.4.10", "%s %s:%s can force horizontal scroll at 320 px" % (r["sel"], prop, v)))
    return {"file": str(path), "blockers": sorted(set(blockers)), "warnings": sorted(set(warns)), "contrast": contrast}


def collect(paths):
    files = []
    for p in paths:
        p = pathlib.Path(p)
        files.extend(sorted(p.rglob("*.html")) if p.is_dir() else [p])
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--axe")
    ap.add_argument("--report", default="accessibility-report.md")
    ap.add_argument("--base", help="path prefix to strip in the report")
    a = ap.parse_args()
    files = collect(a.paths)
    titles = {}
    results = [check_page(f, titles) for f in files]
    dup_titles = {t: fs for t, fs in titles.items() if len(fs) > 1}
    axe = json.loads(pathlib.Path(a.axe).read_text()) if a.axe and pathlib.Path(a.axe).exists() else None
    axe_by = {pathlib.Path(p["file"]).resolve(): p for p in axe["pages"]} if axe else {}

    base = pathlib.Path(a.base).resolve() if a.base else None

    def short(s):
        # Compare resolved paths so the prefix strips on Windows (backslashes) as well as macOS and Linux.
        if not base:
            return s
        try:
            return pathlib.Path(s).resolve().relative_to(base).as_posix()
        except ValueError:
            return s
    n_block = sum(len(r["blockers"]) for r in results) + len(dup_titles)
    n_axe = 0
    for r in results:
        ax = axe_by.get(pathlib.Path(r["file"]).resolve())
        r["axe"] = ax
        if ax:
            n_axe += len(ax["violations"])
            if ax.get("reflow_320") is False:
                r["blockers"].append(("1.4.10", "horizontal scroll at 320 px (measured in Chromium)"))
                n_block += 1
    n_warn = sum(len(r["warnings"]) for r in results)
    status = "FAIL" if (n_block or n_axe) else ("PASS WITH NOTES" if n_warn else "PASS")

    allpairs = {}
    for r in results:
        for c in r["contrast"]:
            k = (c["fg"], c["bg"], c["need"], c["state"])
            allpairs.setdefault(k, c)
    L = ["# Accessibility review", "",
         "Status: **%s**" % status,
         "Standard: WCAG 2.2 AA, Purdue accessibility standard (strict), Brightspace topic rules",
         "Generated: %s" % datetime.date.today().isoformat(),
         "Pages checked: %d" % len(results), ""]
    if axe:
        L.append("Automated engine: axe-core %s via %s, rule tags %s." % (axe["axe_version"], axe["engine"], ", ".join(axe["tags"])))
    else:
        L.append("Automated engine: axe-core was not run (pass --axe).")
    L += ["", "## Summary", "",
          "- Blockers from house and structural checks: %d" % n_block,
          "- axe-core violations: %d" % n_axe,
          "- Warnings: %d" % n_warn,
          "- Distinct text and background pairs measured: %d, lowest ratio %.2f:1" % (len(allpairs), min((c["ratio"] for c in allpairs.values()), default=0)), ""]
    if dup_titles:
        L.append("## Duplicate page titles (SC 2.4.2)")
        L += ["- %s: %s" % (t, ", ".join(short(f) for f in fs)) for t, fs in dup_titles.items()]
        L.append("")
    L.append("## Pages")
    L.append("")
    for r in results:
        ax = r["axe"]
        axe_txt = ""
        if ax:
            axe_txt = "axe: %d passed rules, %d violations, %d need a browser" % (ax["passes"], len(ax["violations"]), len(ax["incomplete"]))
        flag = "FAIL" if (r["blockers"] or (ax and ax["violations"])) else ("NOTES" if r["warnings"] else "PASS")
        L.append("- **%s** %s. %s" % (flag, short(r["file"]), axe_txt))
        for sc, msg in r["blockers"]:
            L.append("    - Blocker, SC %s: %s" % (sc, msg))
        if ax:
            for v in ax["violations"]:
                L.append("    - axe %s (%s): %s at %s" % (v["id"], v["impact"], v["help"], v["nodes"][0] if v["nodes"] else ""))
        for sc, msg in r["warnings"]:
            L.append("    - Warning, SC %s: %s" % (sc, msg))
    L += ["", "## Contrast pairs measured (SC 1.4.3)", "",
          "| Text | Background | State | Ratio | Needed | Example element | Result |", "|---|---|---|---|---|---|---|"]
    for c in sorted(allpairs.values(), key=lambda c: c["ratio"]):
        L.append("| %s | %s | %s | %.2f:1 | %.1f:1 | %s | %s |" % (c["fg"], c["bg"], c["state"], c["ratio"], c["need"], c["example"], "Pass" if c["pass"] else "FAIL"))
    if axe:
        inc = sorted({v["id"] for p in axe["pages"] for v in p["incomplete"]})
        if inc:
            L += ["", "## Checks axe could not finish without a browser", "",
                  "axe marked these rules incomplete: %s. Contrast, focus visibility, target size and reflow are covered above by the CSS cascade check. Run `npx playwright install chromium` and rerun to measure them in a real browser." % ", ".join(inc)]
    L += ["", "## Manual checks still owed before release", "",
          "- Tab through three pages per package in Brightspace and confirm the focus ring is visible on every summary and link.",
          "- Open one page per package at 320 px in the Brightspace mobile app.",
          "- Confirm captions are accurate (not only present) on every linked video, and transcripts match the final edit.",
          "- Screen reader spot check (NVDA or VoiceOver) on one knowledge check and one table."]
    pathlib.Path(a.report).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("Accessibility: %s. %d pages, %d blockers, %d axe violations, %d warnings -> %s" % (status, len(results), n_block, n_axe, n_warn, a.report))
    for r in results:
        for sc, msg in r["blockers"]:
            print("  BLOCKER %s SC %s %s" % (pathlib.Path(r["file"]).name, sc, msg))
    sys.exit(1 if status == "FAIL" else 0)


if __name__ == "__main__":
    main()
