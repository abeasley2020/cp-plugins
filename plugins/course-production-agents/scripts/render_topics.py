#!/usr/bin/env python3
"""
render_topics.py: turn topic JSON files into standalone, accessible, Purdue
branded HTML topic pages, one folder per module or week.

    python3 render_topics.py --map course-map.json --media media-plan.json \
        --topics topics/ --out build/

What it does
- Reads the course map for the unit order, unit titles, and topic order.
- Writes an overview page for every unit straight from the course map, so the
  objectives and the graded items shown to learners always match the map.
- Renders every authored topic JSON (see skills/.../topic-schema.md) into HTML
  using templates/topic.css. Agents never hand-write HTML.
- Drops any video block whose media item has no streaming URL yet, and lists
  it in render-report.json so nobody ships a dead link.
- Writes build/course.json, the input for build_packages.py.

Only the Python standard library is needed. Exit code 1 on any error.
"""

import argparse
import html
import json
import pathlib
import re
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
CSS = (HERE.parent / "templates" / "topic.css").read_text(encoding="utf-8")

errors, warnings, omitted_media = [], [], []

BANNED_LINK_TEXT = {"click here", "here", "read more", "this", "link", "more", "this link"}


def esc(s):
    return html.escape(str(s), quote=True)


def inline(text, where):
    """Minimal inline markup: **bold**, *italic*, [text](https://url)."""
    s = esc(text)

    def link(m):
        label, url = m.group(1), m.group(2)
        if label.strip().lower() in BANNED_LINK_TEXT:
            errors.append("non-descriptive link text '%s' in %s" % (label, where))
        ext = url.startswith("http") and "purdue.edu" not in url
        suffix = " (external site)" if ext and "external" not in label.lower() else ""
        return '<a href="%s">%s%s</a>' % (url, label, suffix)

    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|[^)\s]+\.html)\)", link, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", s)
    return s


def paras(items, where):
    if isinstance(items, str):
        items = [items]
    return "\n".join("<p>%s</p>" % inline(p, where) for p in items)


def render_block(b, ctx):
    t = b.get("type")
    w = ctx["where"]
    if t == "heading":
        lvl = int(b.get("level", 2))
        if lvl not in (2, 3):
            errors.append("heading level must be 2 or 3 in %s" % w)
        return "<h%d>%s</h%d>" % (lvl, inline(b["text"], w), lvl)
    if t == "paragraph":
        return paras(b["text"], w)
    if t == "list":
        tag = "ol" if b.get("ordered") else "ul"
        lis = "\n".join("<li>%s</li>" % inline(i, w) for i in b["items"])
        return "<%s>\n%s\n</%s>" % (tag, lis, tag)
    if t in ("callout", "caution"):
        label = b.get("label", "Why this matters" if t == "callout" else "Caution")
        return '<div class="%s">\n<span class="label">%s</span>\n%s\n</div>' % (t, esc(label), paras(b["text"], w))
    if t == "accordion":
        out = []
        for it in b["items"]:
            out.append('<details class="acc">\n<summary>%s</summary>\n<div class="accbody">\n%s\n</div>\n</details>'
                       % (inline(it["summary"], w), paras(it["body"], w)))
        return "\n".join(out)
    if t == "flashcards":
        intro = b.get("intro", "Commit to an answer before opening each card.")
        cards = "\n".join('<details class="card">\n<summary>%s</summary>\n<div class="cardbody">\n%s\n</div>\n</details>'
                          % (inline(c["front"], w), paras(c["back"], w)) for c in b["cards"])
        head = "<h2>%s</h2>\n" % esc(b["heading"]) if b.get("heading") else ""
        return '%s<p>%s</p>\n<div class="deck">\n%s\n</div>' % (head, inline(intro, w), cards)
    if t == "knowledge_check":
        qs = []
        for i, q in enumerate(b["questions"], start=1):
            opts = "\n".join("<li>%s</li>" % inline(o, w) for o in q["options"])
            letter = "ABCDEFGH"[q["answer"]]
            qs.append('<h3>%d. %s</h3>\n<ol class="kcopts">\n%s\n</ol>\n<details class="acc">\n<summary>Show the answer to question %d</summary>\n<div class="accbody"><p>%s. %s</p></div>\n</details>'
                      % (i, inline(q["stem"], w), opts, i, letter, inline(q["rationale"], w)))
        return '<div class="kc">\n<h2>%s</h2>\n%s\n</div>' % (esc(b.get("heading", "Knowledge check")), "\n".join(qs))
    if t == "table":
        cols = "".join('<th scope="col">%s</th>' % inline(c, w) for c in b["columns"])
        rows = []
        for r in b["rows"]:
            cells = []
            for ci, c in enumerate(r):
                if ci == 0 and b.get("row_headers", True):
                    cells.append('<th scope="row">%s</th>' % inline(c, w))
                else:
                    cells.append("<td>%s</td>" % inline(c, w))
            rows.append("<tr>%s</tr>" % "".join(cells))
        cap = esc(b["caption"])
        return ('<div class="tablewrap" tabindex="0" role="region" aria-label="%s">\n<table>\n<caption>%s</caption>\n'
                '<thead><tr>%s</tr></thead>\n<tbody>\n%s\n</tbody>\n</table>\n</div>') % (cap, cap, cols, "\n".join(rows))
    if t == "image":
        if "alt" not in b:
            errors.append("image without alt in %s" % w)
        cap = "<figcaption>%s</figcaption>" % inline(b["caption"], w) if b.get("caption") else ""
        if b.get("alt") and not b.get("long_description"):
            errors.append("informative image %s needs a Description in %s" % (b["src"], w))
        longd = ""
        if b.get("long_description"):
            label = b.get("caption") or b.get("alt") or "this image"
            longd = ('<details class="acc imgdesc">\n<summary>Full description: %s</summary>\n<div class="accbody">\n%s\n</div>\n</details>'
                     % (inline(label, w), paras(b["long_description"], w)))
        return '<figure>\n<img src="%s" alt="%s">\n%s\n</figure>\n%s' % (esc(b["src"]), esc(b.get("alt", "")), cap, longd)
    if t == "video":
        item = ctx["media"].get(b["media_id"])
        if not item:
            errors.append("video block points at unknown media id %s in %s" % (b["media_id"], w))
            return ""
        url = item.get("stream_url")
        if not url:
            omitted_media.append({"media_id": b["media_id"], "title": item.get("title"), "topic": w})
            return ""
        if not item.get("captions_verified"):
            errors.append("video %s has a URL but captions_verified is not true (%s)" % (b["media_id"], w))
        mins = item.get("target_minutes")
        tr = item.get("transcript_url")
        tr_html = ' <a href="%s">Read the transcript for %s</a>' % (esc(tr), esc(item["title"])) if tr else ""
        return ('<div class="video">\n<span class="label">Video</span>\n<p><a href="%s">Watch %s</a> (about %s minutes, captioned).%s</p>\n%s\n</div>'
                % (esc(url), esc(item["title"]), mins, tr_html, paras(b.get("note", []), w) if b.get("note") else ""))
    if t == "check_yourself":
        return '<div class="check">\n<span class="label">Check yourself</span>\n%s\n</div>' % paras(b["text"], w)
    if t == "steps":
        lis = "\n".join("<li>%s</li>" % inline(i, w) for i in b["items"])
        head = "<h2>%s</h2>\n" % esc(b["heading"]) if b.get("heading") else ""
        return "%s<ol>\n%s\n</ol>" % (head, lis)
    errors.append("unknown block type '%s' in %s" % (t, w))
    return ""


def page(title, band, meta, purpose, body, next_line, sources):
    src_html = ""
    if sources:
        lis = []
        for s in sources:
            chip = ' <span class="chip">Verified %s</span>' % esc(s["verified"]) if s.get("verified") else ""
            lis.append("<li>%s%s</li>" % (inline(s["text"], title), chip))
        src_html = '<footer class="src">\n<h2>Sources</h2>\n<ul>\n%s\n</ul>\n</footer>\n' % "\n".join(lis)
    purpose_html = ('<h2>What this topic is for</h2>\n<p class="purpose">%s</p>\n' % inline(purpose, title)) if purpose else ""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s</title>
<style>
%s</style>
</head>
<body>
<header class="band">Purdue University Online <span>%s</span></header>
<main class="wrap">

<h1>%s</h1>
<p class="meta">%s</p>

%s%s

<p class="next">%s</p>
%s
</main>
</body>
</html>
""" % (esc(title + " | " + band), CSS, esc(band), esc(title), esc(meta), purpose_html, body, esc(next_line), src_html)


def unit_word(fmt):
    return "Week" if fmt == "week" else "Module"


def overview_body(unit, cmap):
    clo = {o["id"]: o["statement"] for o in cmap["outcomes"]}
    out = ["<h2>In this %s</h2>" % unit_word(cmap["course"]["unit_format"]).lower(), paras(unit["summary"], "overview")]
    out.append("<h2>Objectives</h2>\n<p>By the end of this %s you will be able to:</p>" % unit_word(cmap["course"]["unit_format"]).lower())
    out.append("<ol>\n%s\n</ol>" % "\n".join("<li>%s</li>" % inline(o["statement"], "overview") for o in unit["objectives"]))
    rows = []
    for i, tp in enumerate(unit["topics"], start=1):
        rows.append('<tr><th scope="row">%d.%d %s</th><td>%s minutes</td></tr>' % (unit["number"], i, esc(tp["title"]), tp["minutes"]))
    out.append('<div class="tablewrap" tabindex="0" role="region" aria-label="Topics and estimated time">\n<table>\n<caption>Topics and estimated time</caption>\n'
               '<thead><tr><th scope="col">Topic</th><th scope="col">Time</th></tr></thead>\n<tbody>\n%s\n</tbody>\n</table>\n</div>' % "\n".join(rows))
    graded = [a for a in unit.get("assessments", []) + unit.get("activities", []) if a.get("graded")]
    if graded:
        lis = "\n".join("<li><strong>%s</strong> (%s points). %s</li>" % (esc(a["title"]), a.get("points", 0), esc(a.get("where", "Submit in Brightspace."))) for a in graded)
        out.append('<div class="callout">\n<span class="label">What is graded</span>\n<ul>\n%s\n</ul>\n</div>' % lis)
    links = sorted({c for o in unit["objectives"] for c in o.get("supports", [])})
    if links:
        out.append("<h2>How this connects to the course</h2>\n<p>This %s builds toward these course outcomes:</p>\n<ul>\n%s\n</ul>"
                   % (unit_word(cmap["course"]["unit_format"]).lower(), "\n".join("<li>%s</li>" % esc(clo.get(c, c)) for c in links)))
    return "\n\n".join(out)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--media", required=True)
    ap.add_argument("--topics", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--format", choices=["module", "week"], help="override unit_format in the course map")
    a = ap.parse_args()

    cmap = json.loads(pathlib.Path(a.map).read_text(encoding="utf-8"))
    if a.format:
        cmap["course"]["unit_format"] = a.format
    fmt = cmap["course"].get("unit_format", "module")
    if fmt not in ("module", "week"):
        print("ERROR unit_format must be 'module' or 'week'. Whole-course packages are not built.")
        sys.exit(1)
    media = {m["id"]: m for m in json.loads(pathlib.Path(a.media).read_text(encoding="utf-8"))["items"]}
    tdir = pathlib.Path(a.topics)
    out = pathlib.Path(a.out)
    content = out / "content"
    content.mkdir(parents=True, exist_ok=True)

    code = cmap["course"]["code"]
    word = unit_word(fmt)
    course_cfg = {"title": cmap["course"]["title"], "code": code, "unit_format": fmt,
                  "dwell_seconds": cmap["course"].get("dwell_seconds", 45), "units": []}

    for unit in cmap["units"]:
        n = unit["number"]
        folder = "%s-%02d-%s" % (word.lower(), n, unit.get("slug") or slugify(unit["title"]))
        udir = content / folder
        udir.mkdir(parents=True, exist_ok=True)
        unit_title = "%s %02d: %s" % (word, n, unit["title"])
        band = "%s %s" % (code, unit_title)
        authored = [tp for tp in unit["topics"]]
        files = []
        # Overview page, generated from the map.
        first_next = "%d.1 %s" % (n, authored[0]["title"]) if authored else "the next %s" % word.lower()
        ov_html = page("%s overview" % unit_title, band,
                       "%s %02d. Estimated time: 5 minutes." % (word, n), None,
                       overview_body(unit, cmap), "Next topic: %s. Select it from the course menu." % first_next, None)
        (udir / "topic-00-overview.html").write_text(ov_html, encoding="utf-8")
        files.append({"file": "topic-00-overview.html", "title": "%d.0 Overview and objectives" % n})

        for i, tp in enumerate(authored, start=1):
            src = tdir / ("unit-%02d" % n) / ("%s.json" % tp["id"])
            if not src.exists():
                if unit.get("build", True):
                    errors.append("missing topic JSON %s" % src)
                continue
            spec = json.loads(src.read_text(encoding="utf-8"))
            where = "%s/%s" % (folder, tp["id"])
            ctx = {"where": where, "media": media}
            body = "\n\n".join(filter(None, (render_block(b, ctx) for b in spec["blocks"])))
            if i < len(authored):
                nxt = "Next topic: %d.%d %s. Select it from the course menu." % (n, i + 1, authored[i]["title"])
            else:
                nxt = "This is the last topic in %s %02d. Select the next %s from the course menu when you are ready." % (word, n, word.lower())
            kind = "Activity" if tp.get("type") == "activity" else "Topic"
            meta = "%s %02d, %s %d of %d. Estimated time: %s minutes." % (word, n, kind, i, len(authored), tp["minutes"])
            fname = "%s-%02d-%s.html" % ("activity" if kind == "Activity" else "topic", i, tp.get("slug") or slugify(tp["title"]))
            heading = ("Activity: " + tp["title"]) if kind == "Activity" else tp["title"]
            doc = page(heading, band, meta, spec.get("purpose"), body, nxt, spec.get("sources"))
            (udir / fname).write_text(doc, encoding="utf-8")
            files.append({"file": fname, "title": "%d.%d %s%s" % (n, i, "Activity: " if kind == "Activity" else "", tp["title"])})

        imgs = tdir / ("unit-%02d" % n) / "images"
        if imgs.is_dir():
            shutil.copytree(imgs, udir / "images", dirs_exist_ok=True)
        if len(files) > 1:
            course_cfg["units"].append({"folder": folder, "title": unit_title, "number": n, "topics": files})
        else:
            warnings.append("%s has no authored topics yet; no package will be built for it" % unit_title)
            (udir / "topic-00-overview.html").unlink()
            udir.rmdir()

    (out / "course.json").write_text(json.dumps(course_cfg, indent=2), encoding="utf-8")
    (out / "render-report.json").write_text(json.dumps({"omitted_media": omitted_media, "warnings": warnings, "errors": errors}, indent=2), encoding="utf-8")
    print("Rendered %d unit(s) as %ss into %s" % (len(course_cfg["units"]), fmt, content))
    for m in omitted_media:
        print("  pending video left out until it has a URL: %s (%s)" % (m["media_id"], m["title"]))
    for w in warnings:
        print("WARNING " + w)
    for e in errors:
        print("ERROR " + e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
