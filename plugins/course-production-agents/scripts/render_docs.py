#!/usr/bin/env python3
"""
render_docs.py: turn course-map.json and media-plan.json into review documents.

    python3 render_docs.py --map course-map.json --media media-plan.json --out docs/

Writes
  docs/course-map.html   alignment matrix, unit-by-unit objectives, topics,
                         activities, assessments and evidence, faculty gaps
  docs/media-plan.html   every planned media item grouped by unit, with type,
                         length, script source, shoot, accessibility needs
  docs/media-plan.csv    the same media plan as a spreadsheet for producers

Both HTML files use the same Purdue styles as the topic pages and meet the
same WCAG 2.2 AA rules, so the accessibility checker covers them too.
"""

import argparse
import csv
import html
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
CSS = (HERE.parent / "templates" / "topic.css").read_text(encoding="utf-8") + \
    ".wrap{max-width:68rem;}\n.small{font-size:.95rem;}\n"


def e(s):
    return html.escape(str(s), quote=True)


def table(caption, cols, rows, row_headers=True):
    head = "".join('<th scope="col">%s</th>' % e(c) for c in cols)
    body = []
    for r in rows:
        cells = []
        for i, c in enumerate(r):
            if i == 0 and row_headers:
                cells.append('<th scope="row">%s</th>' % c)
            else:
                cells.append("<td>%s</td>" % c)
        body.append("<tr>%s</tr>" % "".join(cells))
    return ('<div class="tablewrap" tabindex="0" role="region" aria-label="%s">\n<table>\n<caption>%s</caption>\n'
            "<thead><tr>%s</tr></thead>\n<tbody>\n%s\n</tbody>\n</table>\n</div>") % (e(caption), e(caption), head, "\n".join(body))


def doc(title, band, body):
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
%s
</main>
</body>
</html>
""" % (e(title), CSS, e(band), body)


def course_map_html(m):
    c = m["course"]
    word = "Week" if c["unit_format"] == "week" else "Module"
    out = ["<h1>Course map: %s</h1>" % e(c["title"]),
           '<p class="meta">%s. %s. Draft for instructional designer and faculty review.</p>' % (e(c["code"]), e(c["college"]))]
    facts = [["Audience", e(c["audience"])], ["Delivery", e(c.get("delivery", "Online, asynchronous"))],
             ["Packaging", "One Brightspace package per %s" % word.lower()],
             ["Learner time", "%s minutes across %d %ss" % (c.get("total_minutes", "TBD"), len(m["units"]), word.lower())]]
    if c.get("credit"):
        facts.append(["Credit", e(c["credit"])])
    out.append(table("Course at a glance", ["Item", "Detail"], facts))
    out.append("<h2>Course outcomes</h2>")
    out.append("<ol>%s</ol>" % "".join("<li><strong>%s</strong> (%s). %s</li>" % (e(o["id"]), e(o["bloom"]), e(o["statement"])) for o in m["outcomes"]))

    cols = ["Outcome"] + ["%s %02d" % (word, u["number"]) for u in m["units"]]
    rows = []
    for o in m["outcomes"]:
        r = [e(o["id"])]
        for u in m["units"]:
            hits = [ob["id"] for ob in u["objectives"] if o["id"] in ob.get("supports", [])]
            r.append("Objectives %s" % ", ".join(hits) if hits else "Not addressed")
        rows.append(r)
    out.append("<h2>Alignment matrix</h2>\n<p>Each cell names the %s objectives that build toward the outcome.</p>" % word.lower())
    out.append(table("Course outcomes by %s" % word.lower(), cols, rows))

    for u in m["units"]:
        out.append("<h2>%s %02d: %s</h2>" % (word, u["number"], e(u["title"])))
        status = "" if u.get("build", True) else " Mapped only; topics are not authored or packaged in this run."
        out.append('<p>%s <span class="small">(%s minutes.%s)</span></p>' % (e(u["summary"]), u.get("minutes", "TBD"), status))
        obj_rows = [[e(o["id"]), e(o["statement"]), e(o["bloom"]), e(", ".join(o.get("supports", [])))] for o in u["objectives"]]
        out.append(table("%s %02d objectives" % (word, u["number"]), ["ID", "Objective", "Bloom level", "Supports"], obj_rows))
        t_rows = [["%d.%d" % (u["number"], i), e(t["title"]), e(t.get("type", "content")), "%s min" % t["minutes"], e(", ".join(t.get("objectives", [])))]
                  for i, t in enumerate(u["topics"], start=1)]
        out.append(table("%s %02d topics" % (word, u["number"]), ["No.", "Topic", "Type", "Time", "Objectives"], t_rows))
        ev = []
        for a in u.get("activities", []) + u.get("assessments", []):
            ev.append([e(a["title"]), e(a.get("type", "")), "Yes, %s points" % a["points"] if a.get("graded") else "No",
                       e(a.get("where", "")), e(", ".join(a.get("objectives", [])))])
        out.append(table("%s %02d activities and assessments" % (word, u["number"]), ["Item", "Type", "Graded", "Where it lives", "Evidence for"], ev))
        if u.get("sources"):
            out.append("<h3>Built from</h3>\n<ul>%s</ul>" % "".join("<li>%s</li>" % e(s) for s in u["sources"]))
    if m.get("gaps"):
        out.append("<h2>What we still need from faculty</h2>")
        out.append(table("Open content gaps", ["Need", "Owner", "Needed for"], [[e(g["item"]), e(g.get("owner", "Faculty")), e(g.get("needed_for", ""))] for g in m["gaps"]]))
    return doc("Course map: %s" % c["title"], c["code"], "\n\n".join(out))


def media_plan_html(media, m):
    c = m["course"]
    word = "Week" if c["unit_format"] == "week" else "Module"
    items = media["items"]
    total = sum(i.get("target_minutes", 0) or 0 for i in items)
    new = [i for i in items if i["type"] != "existing-reuse"]
    out = ["<h1>Media plan: %s</h1>" % e(c["title"]),
           '<p class="meta">%s. Draft for video producer review. Every video is captioned and has a transcript before it is linked in a topic.</p>' % e(c["code"])]
    out.append(table("Media at a glance", ["Measure", "Value"], [
        ["Planned items", str(len(items))], ["New productions", str(len(new))],
        ["Existing faculty media to reuse", str(len(items) - len(new))], ["Finished runtime", "about %s minutes" % total]]))
    if media.get("notes"):
        out.append("<h2>Producer notes</h2>\n<ul>%s</ul>" % "".join("<li>%s</li>" % e(n) for n in media["notes"]))
    topic_titles = {(u["number"], t["id"]): "%d.%d %s" % (u["number"], i, t["title"]) for u in m["units"] for i, t in enumerate(u["topics"], start=1)}
    for u in m["units"]:
        ui = [i for i in items if i["unit"] == u["number"]]
        if not ui:
            continue
        out.append("<h2>%s %02d: %s</h2>" % (word, u["number"], e(u["title"])))
        rows = []
        for i in ui:
            acc = i.get("accessibility", {})
            acc_txt = "Captions, transcript. Audio description: %s" % e(acc.get("audio_description", "decide")) if acc.get("captions") else e(acc.get("text_alternative", ""))
            rows.append([e(i["id"]), "<strong>%s</strong><br>%s" % (e(i["title"]), e(i["purpose"])),
                         e(topic_titles.get((u["number"], i.get("topic")), "")), e(i["type"]),
                         "%s min" % i.get("target_minutes", "TBD"), e(i.get("script_source", "")),
                         e(i["production_notes"]), acc_txt, e(i.get("priority", ""))])
        out.append(table("%s %02d media" % (word, u["number"]),
                         ["ID", "Item and purpose", "Topic", "Type", "Length", "Script source", "Production notes", "Accessibility", "Priority"], rows))
    return doc("Media plan: %s" % c["title"], c["code"], "\n\n".join(out))


def media_csv(media, path):
    cols = ["id", "unit", "topic", "title", "type", "target_minutes", "purpose", "script_source", "script_status",
            "shoot", "on_camera", "production_notes", "captions", "transcript", "audio_description", "priority", "existing_asset", "stream_url"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i in media["items"]:
            acc = i.get("accessibility", {})
            row = dict(i, captions=acc.get("captions"), transcript=acc.get("transcript"), audio_description=acc.get("audio_description"))
            w.writerow([row.get(k, "") for k in cols])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--media", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = json.loads(pathlib.Path(a.map).read_text(encoding="utf-8"))
    media = json.loads(pathlib.Path(a.media).read_text(encoding="utf-8"))
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "course-map.html").write_text(course_map_html(m), encoding="utf-8")
    (out / "media-plan.html").write_text(media_plan_html(media, m), encoding="utf-8")
    media_csv(media, out / "media-plan.csv")
    print("Wrote %s, %s, %s" % (out / "course-map.html", out / "media-plan.html", out / "media-plan.csv"))


if __name__ == "__main__":
    main()
