#!/usr/bin/env python3
"""
validate.py: check the course map, the media plan, and (optionally) the topic
JSON files before anything is rendered or packaged.

    python3 validate.py --map course-map.json --media media-plan.json [--topics topics/]

Course map checks: required fields, unit_format is module or week, unique IDs,
valid Bloom verbs, every course outcome is supported by at least one unit
objective, every unit objective is taught by a topic AND evidenced by an
activity or assessment, minutes present, no term, year or cohort in titles,
no em-dashes.

Media plan checks: every item points at a real unit and topic, known media
type, captions and a transcript required on every item, an explicit audio
description decision, length guidance.

Topic checks: each topic named in the map has a JSON file (for units marked
build), block types are known, video blocks point at real media IDs.

Exit 1 on errors. Warnings do not fail the run.
"""

import argparse
import json
import pathlib
import re
import sys

BLOOM = {"remember", "understand", "apply", "analyze", "evaluate", "create"}
MEDIA_TYPES = {"talking-head", "lightboard", "screencast", "demonstration", "interview", "animation",
               "field-footage", "narrated-slides", "podcast-audio", "existing-reuse", "infographic", "interactive"}
BLOCKS = {"heading", "paragraph", "list", "callout", "caution", "accordion", "flashcards", "knowledge_check",
          "table", "image", "video", "check_yourself", "steps"}
TIME_WORDS = re.compile(r"\b(fall|spring|summer|winter)\s+20\d\d\b|\b20\d\d\b|\bcohort\b|\bthis semester\b", re.I)

errors, warnings = [], []


def snippet(s):
    i = s.find(chr(0x2014))
    return "..." + s[max(0, i - 30):i + 30] + "..."


def walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, "%s.%s" % (path, k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, "%s[%d]" % (path, i))
    elif isinstance(obj, str):
        yield path, obj


def check_map(m):
    c = m.get("course", {})
    for k in ("code", "title", "college", "audience", "unit_format"):
        if not c.get(k):
            errors.append("course-map.md is missing the '- %s:' line at the top" % {"code": "Code", "title": "title (# Course map: <title>)", "college": "College", "audience": "Audience", "unit_format": "Format"}[k])
    if c.get("unit_format") not in ("module", "week"):
        errors.append("course-map.md: Format must be module or week (whole-course packaging is not allowed)")
    clos = {}
    for o in m.get("outcomes", []):
        if o["id"] in clos:
            errors.append("duplicate outcome id %s" % o["id"])
        clos[o["id"]] = o
        if o.get("bloom", "").lower() not in BLOOM:
            errors.append("outcome %s has no valid Bloom level" % o["id"])
    if not clos:
        errors.append("course map has no course outcomes")
    supported = set()
    nums = []
    total = 0
    for u in m.get("units", []):
        n = u.get("number")
        nums.append(n)
        tag = "unit %s" % n
        for k in ("title", "summary", "objectives", "topics"):
            if not u.get(k):
                errors.append("%s is missing %s" % (tag, k))
        if TIME_WORDS.search(u.get("title", "")):
            errors.append("%s title encodes a term, year or cohort: %s" % (tag, u["title"]))
        obj_ids = set()
        for o in u.get("objectives", []):
            obj_ids.add(o["id"])
            if o.get("bloom", "").lower() not in BLOOM:
                errors.append("%s objective %s has no valid Bloom level" % (tag, o["id"]))
            for s in o.get("supports", []):
                if s not in clos:
                    errors.append("%s objective %s supports unknown outcome %s" % (tag, o["id"], s))
                supported.add(s)
            if not o.get("supports"):
                errors.append("%s objective %s does not support any course outcome" % (tag, o["id"]))
        taught, evidenced = set(), set()
        tids = set()
        mins = 0
        for t in u.get("topics", []):
            if t["id"] in tids:
                errors.append("%s duplicate topic id %s" % (tag, t["id"]))
            tids.add(t["id"])
            if not isinstance(t.get("minutes"), (int, float)):
                errors.append("%s topic %s has no minutes" % (tag, t["id"]))
            else:
                mins += t["minutes"]
            if TIME_WORDS.search(t.get("title", "")):
                errors.append("%s topic title encodes a term, year or cohort: %s" % (tag, t["title"]))
            taught.update(t.get("objectives", []))
        for a in u.get("activities", []) + u.get("assessments", []):
            evidenced.update(a.get("objectives", []))
            if a.get("graded") and not a.get("points"):
                warnings.append("%s graded item '%s' has no points" % (tag, a.get("title")))
        for oid in obj_ids:
            if oid not in taught:
                errors.append("%s objective %s is not taught by any topic" % (tag, oid))
            if oid not in evidenced:
                errors.append("%s objective %s has no activity or assessment as evidence" % (tag, oid))
        for oid in taught | evidenced:
            if oid not in obj_ids:
                errors.append("%s references unknown objective %s" % (tag, oid))
        if u.get("minutes") and abs(u["minutes"] - (mins + 5)) > 1:
            warnings.append("%s minutes (%s) do not equal topic minutes plus the 5 minute overview (%s)" % (tag, u["minutes"], mins + 5))
        total += mins + 5
    if nums != list(range(1, len(nums) + 1)):
        errors.append("units must be numbered 1..N in order, found %s" % nums)
    for cid in clos:
        if cid not in supported:
            errors.append("course outcome %s is not supported by any unit objective" % cid)
    if c.get("total_minutes") and abs(c["total_minutes"] - total) > 5:
        warnings.append("course-map.md: Total minutes (%s) differs from the sum of the units (%s)" % (c["total_minutes"], total))
    for p, s in walk_strings(m):
        if chr(0x2014) in s:
            errors.append("em-dash in course-map.md: %s" % snippet(s))


def check_media(media, m):
    units = {u["number"]: {t["id"] for t in u["topics"]} for u in m.get("units", [])}
    seen = set()
    for it in media.get("items", []):
        tag = "media %s" % it.get("id")
        if it.get("id") in seen:
            errors.append("duplicate %s" % tag)
        seen.add(it.get("id"))
        if it.get("unit") not in units:
            errors.append("%s points at unknown unit %s" % (tag, it.get("unit")))
        elif it.get("topic") and it["topic"] not in units[it["unit"]]:
            errors.append("%s points at unknown topic %s" % (tag, it["topic"]))
        if it.get("type") not in MEDIA_TYPES:
            errors.append("%s has unknown type %s (allowed: %s)" % (tag, it.get("type"), ", ".join(sorted(MEDIA_TYPES))))
        acc = it.get("accessibility", {})
        if it.get("type") not in ("infographic", "interactive"):
            if acc.get("captions") is not True:
                errors.append("%s must require captions (WCAG 1.2.2)" % tag)
            if acc.get("transcript") is not True:
                errors.append("%s must require a transcript" % tag)
            if not acc.get("audio_description"):
                errors.append("%s needs an explicit audio description decision (WCAG 1.2.5)" % tag)
        else:
            if not acc.get("text_alternative"):
                errors.append("%s needs a text alternative plan" % tag)
        tm = it.get("target_minutes")
        if isinstance(tm, (int, float)) and tm > 12:
            warnings.append("%s runs %s minutes; consider splitting (CP guidance is 3 to 8 minutes)" % (tag, tm))
        for k in ("title", "purpose", "production_notes"):
            if not it.get(k):
                errors.append("%s is missing its %s line" % (tag, {"title": "title", "purpose": "Purpose", "production_notes": "Production notes"}[k]))
    for p, s in walk_strings(media):
        if chr(0x2014) in s:
            errors.append("em-dash in media-plan.md: %s" % snippet(s))
    return seen


def check_topics(tdir, m, media_ids):
    pattern = m.get("_sources", {}).get("topic_pattern", "topics/unit-NN/<topic id>.json")
    for u in m.get("units", []):
        if not u.get("build", True):
            continue
        for t in u["topics"]:
            jf = tdir / ("unit-%02d" % u["number"]) / ("%s.json" % t["id"])
            if not jf.exists():
                errors.append("unit %d topic %s (%s) is marked to build but has no topic file. Expected %s"
                              % (u["number"], t["id"], t["title"], pattern.replace("NN", "%02d" % u["number"]).replace("<topic id>", t["id"])))
                continue
            try:
                spec = json.loads(jf.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append("%s is not valid JSON: %s" % (jf, exc))
                continue
            f = pathlib.Path(spec.get("_source", str(jf)))
            if not spec.get("purpose"):
                warnings.append("%s has no purpose statement" % f)
            for b in spec.get("blocks", []):
                if b.get("type") not in BLOCKS:
                    errors.append("%s unknown block type %s" % (f, b.get("type")))
                if b.get("type") == "video" and b.get("media_id") not in media_ids:
                    errors.append("%s video block points at unknown media id %s" % (f, b.get("media_id")))
            kc = [b for b in spec.get("blocks", []) if b.get("type") == "knowledge_check"]
            for b in kc:
                for q in b["questions"]:
                    if not (0 <= q["answer"] < len(q["options"])):
                        errors.append("%s knowledge check answer index out of range" % f)
            for p, s in walk_strings(spec):
                if chr(0x2014) in s:
                    errors.append("em-dash in %s: %s" % (f, snippet(s)))
                if re.search(r"\bclick here\b|\bsee (below|above)\b|\bas shown (below|above|to the right)\b", s, re.I):
                    errors.append("sight or click language in %s: %s" % (f, s[:60]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--media")
    ap.add_argument("--topics")
    a = ap.parse_args()
    m = json.loads(pathlib.Path(a.map).read_text(encoding="utf-8"))
    check_map(m)
    ids = set()
    if a.media:
        ids = check_media(json.loads(pathlib.Path(a.media).read_text(encoding="utf-8")), m)
    if a.topics:
        check_topics(pathlib.Path(a.topics), m, ids)
    for w in warnings:
        print("WARNING " + w)
    for e in errors:
        print("ERROR " + e)
    print("Validation: %d error(s), %d warning(s)." % (len(errors), len(warnings)))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
