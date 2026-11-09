#!/usr/bin/env python3
"""
md_sources.py: the Markdown files IDs read and edit, and the JSON the build
scripts use. IDs never see the JSON; it is written under build/source/ on every
build and thrown away on the next one.

    python3 md_sources.py compile <work-folder>
        Reads course-map.md, media-plan.md and topics/<module|week>-NN/*.md and
        writes build/source/course-map.json, media-plan.json and
        topics/unit-NN/<topic id>.json. Problems are reported with the file
        and line number, and the command exits 1.

    python3 md_sources.py from-json <work-folder>
        One-time conversion of an older work folder that still has
        course-map.json, media-plan.json and topics/unit-NN/*.json. Writes the
        Markdown beside them. The JSON files are left for you to delete.

The formats are described in skills/course-production-standards/references/.
In short: plain headings and "- Field: value" lines for facts, pipe tables
for lists of like things, and a quote block (lines starting with ">") whose
bold first line names the kind of box, for every special block in a topic.
"""

import json
import pathlib
import re
import sys

UNIT_WORDS = ("module", "week", "unit")


class Errors(list):
    base = None

    def add(self, path, line, msg):
        p = pathlib.Path(path)
        if self.base:
            try:
                p = p.resolve().relative_to(self.base)
            except ValueError:
                pass
        p = p.as_posix()
        self.append("%s line %s: %s" % (p, line, msg) if line else "%s: %s" % (p, msg))


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:48].rstrip("-") or "item"


def yes(v):
    return str(v).strip().lower() in ("yes", "y", "true", "1")


def to_int(v, default=None):
    m = re.search(r"-?\d+", str(v))
    return int(m.group()) if m else default


def id_list(v):
    v = str(v).strip()
    if not v or v.lower() in ("none", "-"):
        return []
    return [x.strip() for x in re.split(r"[,;]\s*|\s+and\s+", v) if x.strip()]


# ---------------------------------------------------------------- reading


def lines_of(path):
    return path.read_text(encoding="utf-8-sig").splitlines()


def sections(lines, level):
    """Split into (heading text, heading line number, body lines with numbers)
    at headings of exactly this level. Text before the first heading is the
    section with heading None."""
    mark = "#" * level + " "
    out, cur = [], [None, 0, []]
    for n, line in enumerate(lines, start=1):
        if line.startswith(mark):
            out.append(cur)
            cur = [line[len(mark):].strip(), n, []]
        else:
            cur[2].append((n, line))
    out.append(cur)
    return out


FIELD = re.compile(r"^\s*[-*]\s+\**([A-Za-z][A-Za-z ()/]*?)\**\s*:\s*\**\s*(.*)$")


def fields(body):
    """'- Key: value' lines -> {normalized key: (value, line)}. A line that is
    indented under a field continues it."""
    out, last = {}, None
    for n, line in body:
        m = FIELD.match(line)
        if m and not line.startswith("  "):
            key = re.sub(r"[^a-z]+", " ", m.group(1).lower()).strip()
            out[key] = [m.group(2).strip(), n]
            last = key
        elif last and line.startswith("  ") and line.strip():
            out[last][0] = (out[last][0] + " " + line.strip()).strip()
        elif not line.strip():
            continue
        else:
            last = None
    return {k: (v[0], v[1]) for k, v in out.items()}


def bullets(body):
    items, cur = [], None
    for n, line in body:
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m and not line.startswith("  "):
            if cur:
                items.append(cur)
            cur = [m.group(1).strip(), n]
        elif cur and line.startswith("  ") and line.strip():
            cur[0] += " " + line.strip()
        elif not line.strip():
            continue
        else:
            if cur:
                items.append(cur)
            cur = None
    if cur:
        items.append(cur)
    return [(t, n) for t, n in items]


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells = re.split(r"(?<!\\)\|", line)
    return [c.strip().replace("\\|", "|") for c in cells]


def tables(body):
    """Every pipe table in the body: list of (header list, [(row dict, line)])."""
    out, i, rows = [], 0, [(n, l) for n, l in body]
    while i < len(rows):
        n, line = rows[i]
        if line.strip().startswith("|") and i + 1 < len(rows) and re.match(r"^\s*\|?\s*:?-{2,}", rows[i + 1][1]):
            head = split_row(line)
            data = []
            i += 2
            while i < len(rows) and rows[i][1].strip().startswith("|"):
                cells = split_row(rows[i][1])
                data.append(({head[k].lower(): (cells[k] if k < len(cells) else "") for k in range(len(head))}, rows[i][0]))
                i += 1
            out.append((head, data))
        else:
            i += 1
    return out


def subsection(body, title):
    """Body lines of a '### title' subsection inside a section body."""
    out, inside = [], False
    for n, line in body:
        if line.startswith("### "):
            inside = line[4:].strip().lower().startswith(title.lower())
            continue
        if inside:
            out.append((n, line))
    return out


def unit_heading(text):
    m = re.match(r"^(module|week|unit)\s+0*(\d+)\s*:\s*(.+)$", text or "", re.I)
    return (int(m.group(2)), m.group(3).strip(), m.group(1).lower()) if m else None


# ---------------------------------------------------------------- course map


def parse_course_map(path, err):
    lines = lines_of(path)
    secs = sections(lines, 2)
    top = sections(lines, 1)
    title_line = next((s for s in top if s[0]), None)
    course = {}
    if not title_line:
        err.add(path, 1, "the file must start with '# Course map: <course title>'")
        title = ""
    else:
        title = re.sub(r"^course map\s*:\s*", "", title_line[0], flags=re.I)
    f = fields(secs[0][2])
    need = {"code": "Code", "format": "Format"}
    for k, label in need.items():
        if k not in f:
            err.add(path, None, "missing the '- %s:' line near the top" % label)
    course["code"] = f.get("code", ("", 0))[0]
    course["title"] = title
    for key, name in (("college", "college"), ("audience", "audience"), ("delivery", "delivery"), ("description", "description")):
        if key in f:
            course[name] = f[key][0]
    course["unit_format"] = f.get("format", ("module", 0))[0].strip().lower()
    if "total minutes" in f:
        course["total_minutes"] = to_int(f["total minutes"][0], 0)
    dwell = next((v for k, v in f.items() if k.startswith("completion")), None)
    course["dwell_seconds"] = to_int(dwell[0], 45) if dwell else 45

    cmap = {"course": course, "outcomes": [], "units": [], "conversion_notes": [], "gaps": []}
    for head, hn, body in secs[1:]:
        low = head.lower()
        uh = unit_heading(head)
        if low.startswith("course outcomes") or low == "outcomes":
            for text, n in bullets(body):
                m = re.match(r"^(CLO\s*\d+)\s*\(([A-Za-z]+)\)\s*:\s*(.+)$", text)
                if not m:
                    err.add(path, n, "an outcome line reads '- CLO1 (Understand): statement'")
                    continue
                cmap["outcomes"].append({"id": m.group(1).replace(" ", ""), "bloom": m.group(2).capitalize(), "statement": m.group(3).strip()})
        elif uh:
            cmap["units"].append(parse_unit(path, uh, hn, body, err))
        elif low.startswith("conversion notes"):
            cmap["conversion_notes"] = [t for t, _ in bullets(body)]
        elif low.startswith("gaps"):
            for _, rows in tables(body):
                for r, n in rows:
                    item = r.get("need") or r.get("item") or r.get("what is needed") or ""
                    if item:
                        cmap["gaps"].append({"item": item, "owner": r.get("owner", ""), "needed_for": r.get("needed for", "")})
        else:
            err.add(path, hn, "unrecognized section '## %s'. Sections are Course outcomes, Module NN: title (or Week NN), Conversion notes and Gaps" % head)
    return cmap


def parse_unit(path, uh, hn, body, err):
    number, title, _ = uh
    f = fields(body_before_sub(body))
    unit = {"number": number, "title": title}
    unit["slug"] = f["slug"][0] if "slug" in f else slugify(title)
    unit["minutes"] = to_int(f.get("minutes", ("0", 0))[0], 0)
    unit["build"] = yes(f["build"][0]) if "build" in f else True
    unit["summary"] = f.get("summary", ("", 0))[0]
    unit["objectives"] = []
    for text, n in bullets(subsection(body, "objectives")):
        m = re.match(r"^(\d+\.\d+)\s*\(([A-Za-z]+)\s*;\s*supports\s+([^)]+)\)\s*:\s*(.+)$", text, re.I)
        if not m:
            err.add(path, n, "an objective line reads '- 1.1 (Apply; supports CLO2): statement'")
            continue
        unit["objectives"].append({"id": m.group(1), "bloom": m.group(2).capitalize(),
                                   "supports": [s.replace(" ", "") for s in id_list(m.group(3))], "statement": m.group(4).strip()})
    unit["topics"] = []
    for _, rows in tables(subsection(body, "topics")):
        for r, n in rows:
            if not r.get("id"):
                err.add(path, n, "a topic row needs an ID such as t01")
                continue
            t = {"id": r["id"], "title": r.get("title", ""), "minutes": to_int(r.get("minutes", ""), 0),
                 "objectives": id_list(r.get("objectives", "")), "type": (r.get("type") or "content").lower()}
            if r.get("slug"):
                t["slug"] = r["slug"]
            unit["topics"].append(t)
    for key in ("activities", "assessments"):
        unit[key] = []
        for _, rows in tables(subsection(body, key)):
            for r, n in rows:
                if not r.get("id"):
                    continue
                a = {"id": r["id"], "title": r.get("title", ""), "type": r.get("type", ""), "graded": yes(r.get("graded", "no"))}
                if to_int(r.get("points", "")) is not None:
                    a["points"] = to_int(r["points"])
                a["where"] = r.get("where", "")
                a["objectives"] = id_list(r.get("objectives", ""))
                unit[key].append(a)
    unit["sources"] = [t for t, _ in bullets(subsection(body, "built from"))]
    for need in ("objectives", "topics"):
        if not unit[need]:
            err.add(path, hn, "%s has no %s" % (title, need))
    return unit


def body_before_sub(body):
    out = []
    for n, line in body:
        if line.startswith("### "):
            break
        out.append((n, line))
    return out


# ---------------------------------------------------------------- media plan

MEDIA_FIELDS = [
    ("topic", "topic"), ("type", "type"), ("minutes", "target_minutes"), ("purpose", "purpose"),
    ("script source", "script_source"), ("script status", "script_status"), ("shoot", "shoot"),
    ("on camera", "on_camera"), ("production notes", "production_notes"), ("priority", "priority"),
    ("existing asset", "existing_asset"), ("stream url", "stream_url"), ("transcript url", "transcript_url"),
    ("captions verified", "captions_verified"),
]
ACC_FIELDS = [("captions", "captions"), ("transcript", "transcript"), ("audio description", "audio_description"),
              ("text alternative", "text_alternative")]


def parse_media_plan(path, err):
    lines = lines_of(path)
    secs = sections(lines, 2)
    f = fields(secs[0][2])
    plan = {"course_code": f.get("course code", ("", 0))[0], "notes": [], "items": []}
    for head, hn, body in secs[1:]:
        uh = unit_heading(head)
        if head.lower().startswith("notes"):
            plan["notes"] = [t for t, _ in bullets(body)]
            continue
        if not uh:
            err.add(path, hn, "unrecognized section '## %s'. Sections are Notes and Module NN: title (or Week NN)" % head)
            continue
        for ihead, ihn, ibody in sections([l for _, l in body], 3)[1:]:
            ln = body[0][0] - 1 if body else hn
            m = re.match(r"^([A-Z0-9][A-Za-z0-9-]*)\s*:\s*(.+)$", ihead)
            if not m:
                err.add(path, ln + ihn, "a media item heading reads '### M01-V01: title'")
                continue
            fl = fields([(ln + n, l) for n, l in ibody])
            item = {"id": m.group(1), "unit": uh[0], "title": m.group(2).strip()}
            for key, name in MEDIA_FIELDS:
                v = fl.get(key, ("", 0))[0]
                if name == "topic":
                    item[name] = v.split()[0] if v else ""
                elif name == "target_minutes":
                    item[name] = to_int(v, 0)
                elif name == "captions_verified":
                    if v:
                        item[name] = yes(v)
                elif name in ("transcript_url",):
                    if v:
                        item[name] = v
                else:
                    item[name] = v
            acc = {}
            for key, name in ACC_FIELDS:
                if key in fl:
                    acc[name] = yes(fl[key][0]) if name in ("captions", "transcript") else fl[key][0]
            item["accessibility"] = acc
            plan["items"].append(item)
    return plan


# ---------------------------------------------------------------- topics

BOX_KINDS = ("caution", "check yourself", "description", "expand", "flashcards", "knowledge check", "steps", "video")


def paragraphs(lines):
    out, cur = [], []
    for line in lines:
        if line.strip():
            cur.append(line.strip())
        elif cur:
            out.append(" ".join(cur)); cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def parse_topic(path, err):
    lines = lines_of(path)
    spec = {"title": "", "purpose": "", "blocks": [], "sources": []}
    i, n = 0, len(lines)
    para = []

    def flush():
        if para:
            text = " ".join(x.strip() for x in para)
            para.clear()
            m = re.match(r"^\*{0,2}purpose\s*:\s*\*{0,2}\s*(.+)$", text, re.I)
            if m and not spec["purpose"] and not spec["blocks"]:
                spec["purpose"] = m.group(1).strip()
                return
            if spec["blocks"] and spec["blocks"][-1]["type"] == "image" and re.match(r"^description\s*:", text, re.I):
                spec["blocks"][-1]["long_description"] = [re.sub(r"^description\s*:\s*", "", text, flags=re.I)]
                return
            last = spec["blocks"][-1] if spec["blocks"] else None
            if last and last["type"] == "paragraph" and last.get("_open"):
                last["text"].append(text)
            else:
                spec["blocks"].append({"type": "paragraph", "text": [text], "_open": True})

    def close_para():
        if spec["blocks"] and spec["blocks"][-1].get("_open"):
            spec["blocks"][-1].pop("_open")

    in_sources = False
    while i < n:
        line = lines[i]
        ln = i + 1
        s = line.strip()
        if not s:
            flush(); i += 1; continue
        if in_sources:
            m = re.match(r"^[-*]\s+(.*)$", s)
            if m:
                text = m.group(1).strip()
                v = re.search(r"\(verified\s+(\d{4}-\d{2}-\d{2})\)\s*$", text, re.I)
                src = {"text": text[:v.start()].strip() if v else text}
                if v:
                    src["verified"] = v.group(1)
                spec["sources"].append(src)
            elif spec["sources"] and line.startswith("  "):
                spec["sources"][-1]["text"] += " " + s
            else:
                err.add(path, ln, "only '- source' lines may follow '## Sources'")
            i += 1; continue
        if s.startswith("# ") and not s.startswith("## "):
            flush(); close_para()
            spec["title"] = s[2:].strip(); i += 1; continue
        m = re.match(r"^(#{2,6})\s+(.+)$", s)
        if m:
            flush(); close_para()
            if m.group(2).strip().lower() == "sources":
                in_sources = True; i += 1; continue
            lvl = len(m.group(1))
            if lvl > 3:
                err.add(path, ln, "use ## or ### headings only; the page title is the # heading")
                lvl = 3
            spec["blocks"].append({"type": "heading", "level": lvl, "text": m.group(2).strip()})
            i += 1; continue
        if s.startswith(">"):
            flush(); close_para()
            j = i
            inner = []
            while j < n and lines[j].strip().startswith(">"):
                inner.append(re.sub(r"^\s*>\s?", "", lines[j]))
                j += 1
            box(path, ln, inner, spec, err)
            i = j; continue
        tm = re.match(r"^table(\s*\(no row headers\))?\s*:\s*(.+)$", s, re.I)
        nxt = i + 1
        while tm and nxt < n and not lines[nxt].strip() and nxt <= i + 1:
            nxt += 1
        if tm and nxt < n and lines[nxt].strip().startswith("|"):
            flush(); close_para()
            j = nxt
            rows = []
            while j < n and lines[j].strip().startswith("|"):
                rows.append((j + 1, lines[j])); j += 1
            found = tables(rows)
            if not found:
                err.add(path, ln, "a table needs a header row and a |---| line under it")
            else:
                head, data = found[0]
                blk = {"type": "table", "caption": tm.group(2).strip(), "columns": head,
                       "rows": [[r.get(h.lower(), "") for h in head] for r, _ in data]}
                if tm.group(1):
                    blk["row_headers"] = False
                spec["blocks"].append(blk)
            i = j; continue
        if s.startswith("|"):
            err.add(path, ln, "put a 'Table: caption' line right above every table")
            while i < n and lines[i].strip().startswith("|"):
                i += 1
            continue
        im = re.match(r'^!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+"([^"]*)")?\s*\)$', s)
        if im:
            flush(); close_para()
            blk = {"type": "image", "src": im.group(2), "alt": im.group(1)}
            if im.group(3):
                blk["caption"] = im.group(3)
            spec["blocks"].append(blk)
            i += 1; continue
        lm = re.match(r"^([-*]|\d+[.)])\s+(.*)$", s)
        if lm and not line.startswith("  "):
            flush(); close_para()
            ordered = lm.group(1)[0].isdigit()
            items = []
            while i < n:
                cur = lines[i]
                mm = re.match(r"^([-*]|\d+[.)])\s+(.*)$", cur.strip())
                if mm and not cur.startswith("  ") and (mm.group(1)[0].isdigit()) == ordered:
                    items.append(mm.group(2).strip())
                elif cur.startswith("  ") and cur.strip() and items:
                    items[-1] += " " + cur.strip()
                else:
                    break
                i += 1
            blk = {"type": "list", "items": items}
            if ordered:
                blk["ordered"] = True
            spec["blocks"].append(blk)
            continue
        vm = re.match(r"^\[video\s*:\s*([^\]]+)\]$", s, re.I)
        if vm:
            flush(); close_para()
            spec["blocks"].append({"type": "video", "media_id": vm.group(1).split()[0]})
            i += 1; continue
        para.append(line)
        i += 1
    flush(); close_para()
    if not spec["title"]:
        err.add(path, 1, "the file must start with '# <topic title>'")
    if not spec["purpose"]:
        err.add(path, None, "add a 'Purpose: ...' line under the title")
    return spec


def box(path, ln, inner, spec, err):
    while inner and not inner[0].strip():
        inner.pop(0)
    first = inner[0].strip() if inner else ""
    m = re.match(r"^\*\*(.+?)\*\*\s*$", first)
    if not m:
        err.add(path, ln, "a box (lines starting with >) must open with a bold label line, such as > **Why this matters**")
        return
    label = m.group(1).strip().rstrip(":")
    rest = inner[1:]
    kind, _, arg = label.partition(":")
    k = kind.strip().lower()
    arg = arg.strip()
    blocks = spec["blocks"]
    if k == "caution":
        blocks.append({"type": "caution", "label": arg or "Caution", "text": paragraphs(rest)})
    elif k == "check yourself":
        blocks.append({"type": "check_yourself", "text": paragraphs(rest)})
    elif k == "description":
        if blocks and blocks[-1]["type"] == "image":
            blocks[-1]["long_description"] = paragraphs(rest)
        else:
            err.add(path, ln, "a > **Description** box must come right after the image it describes")
    elif k == "expand":
        item = {"summary": arg, "body": paragraphs(rest)}
        if not arg:
            err.add(path, ln, "write the expand label as **Expand: what the learner will find inside**")
        if blocks and blocks[-1]["type"] == "accordion" and blocks[-1].get("_ln_end") == ln - 1:
            blocks[-1]["items"].append(item)
        else:
            blocks.append({"type": "accordion", "items": [item]})
        blocks[-1]["_ln_end"] = ln + len(inner)
    elif k == "video":
        blk = {"type": "video", "media_id": arg.split()[0] if arg else ""}
        note = paragraphs(rest)
        if note:
            blk["note"] = note
        if not arg:
            err.add(path, ln, "write the video as **Video: M01-V01** using the media plan id")
        blocks.append(blk)
    elif k == "steps":
        items = list_items(rest)
        blk = {"type": "steps", "items": items}
        if arg:
            blk["heading"] = arg
        if not items:
            err.add(path, ln, "a Steps box holds a numbered list")
        blocks.append(blk)
    elif k == "flashcards":
        blk = {"type": "flashcards", "cards": []}
        if arg:
            blk["heading"] = arg
        cur, buf = None, []
        for line in rest + [""]:
            s = line.strip()
            q = re.match(r"^\**Q\s*:\**\s*(.*)$", s)
            a = re.match(r"^\**A\s*:\**\s*(.*)$", s)
            intro = re.match(r"^\**intro\s*:\**\s*(.*)$", s, re.I)
            if intro and cur is None and not blk["cards"]:
                blk["intro"] = intro.group(1).strip()
            elif q:
                if cur:
                    cur["back"] = paragraphs(buf); blk["cards"].append(cur)
                cur, buf = {"front": q.group(1).strip(), "back": []}, []
            elif a and cur:
                buf = [a.group(1)]
            elif cur is not None:
                buf.append(line)
        if cur:
            cur["back"] = paragraphs(buf); blk["cards"].append(cur)
        if not blk["cards"] or any(not c["back"] for c in blk["cards"]):
            err.add(path, ln, "flashcards need 'Q:' and 'A:' lines for every card")
        blocks.append(blk)
    elif k == "knowledge check":
        blk = {"type": "knowledge_check", "questions": []}
        if arg:
            blk["heading"] = arg
        q = None
        for off, line in enumerate(rest, start=1):
            s = line.strip()
            if not s:
                continue
            qm = re.match(r"^\d+[.)]\s+(.+)$", s)
            om = re.match(r"^(?:[-*]\s+\[([ xX])\]\s+|([a-hA-H])[.)]\s+)(.+)$", s)
            wm = re.match(r"^\**why\s*:\**\s*(.+)$", s, re.I)
            if om and q is not None:
                text = om.group(3).strip()
                correct = (om.group(1) or "").lower() == "x"
                if re.search(r"\(correct\)\s*$", text, re.I):
                    correct, text = True, re.sub(r"\s*\(correct\)\s*$", "", text, flags=re.I)
                if correct:
                    q["answer"] = len(q["options"])
                q["options"].append(text)
            elif wm and q is not None:
                q["rationale"] = wm.group(1).strip()
            elif qm:
                q = {"stem": qm.group(1).strip(), "options": [], "answer": None, "rationale": ""}
                blk["questions"].append(q)
            elif q is not None and q["rationale"]:
                q["rationale"] += " " + s
            elif q is not None and not q["options"]:
                q["stem"] += " " + s
            else:
                err.add(path, ln + off, "unexpected line in a knowledge check: %s" % s[:50])
        for qi, qq in enumerate(blk["questions"], start=1):
            if qq["answer"] is None:
                err.add(path, ln, "knowledge check question %d has no correct answer marked [x]" % qi)
                qq["answer"] = 0
            if not qq["rationale"]:
                err.add(path, ln, "knowledge check question %d needs a 'Why:' line" % qi)
        if not blk["questions"]:
            err.add(path, ln, "a knowledge check holds numbered questions")
        blocks.append(blk)
    else:
        blocks.append({"type": "callout", "label": label, "text": paragraphs(rest)})


def list_items(lines):
    items = []
    for line in lines:
        m = re.match(r"^\s*(?:\d+[.)]|[-*])\s+(.+)$", line)
        if m and not line.startswith("    "):
            items.append(m.group(1).strip())
        elif items and line.strip():
            items[-1] += " " + line.strip()
    return items


def topic_file(work, unit, tid):
    for word in UNIT_WORDS:
        d = work / "topics" / ("%s-%02d" % (word, unit))
        if d.is_dir():
            for f in sorted(d.glob("*.md")):
                if f.stem == tid or f.stem.startswith(tid + "-"):
                    return f
    return None


# ---------------------------------------------------------------- compile


def compile_work(work):
    work = pathlib.Path(work).resolve()
    err = Errors()
    err.base = work
    rel = lambda p: p.relative_to(work).as_posix()
    cm_path, mp_path = work / "course-map.md", work / "media-plan.md"
    if not cm_path.exists():
        print("ERROR %s not found. The course map is written as Markdown (course-map.md)." % cm_path)
        return 1
    cmap = parse_course_map(cm_path, err)
    plan = parse_media_plan(mp_path, err) if mp_path.exists() else {"course_code": cmap["course"]["code"], "notes": [], "items": []}
    if not mp_path.exists():
        print("NOTE media-plan.md not written yet; checking the course map only.")
    out = work / "build" / "source"
    tout = out / "topics"
    topic_sources = {}
    for u in cmap["units"]:
        for t in u["topics"]:
            f = topic_file(work, u["number"], t["id"])
            if not f:
                continue
            if "slug" not in t:
                tail = f.stem[len(t["id"]):].lstrip("-")
                if tail:
                    t["slug"] = tail
            spec = parse_topic(f, err)
            if spec["title"] and spec["title"] != t["title"]:
                err.add(rel(f), 1, "the title '%s' does not match the course map, which says '%s'. Change one so they match." % (spec["title"], t["title"]))
            for b in spec["blocks"]:
                b.pop("_open", None); b.pop("_ln_end", None)
            spec.pop("title")
            spec["_source"] = rel(f)
            d = tout / ("unit-%02d" % u["number"])
            d.mkdir(parents=True, exist_ok=True)
            for b in spec["blocks"]:
                if b["type"] == "image" and not re.match(r"^[a-z]+:", b["src"], re.I):
                    img = (f.parent / b["src"]).resolve()
                    if not img.is_file() or ".." in b["src"]:
                        err.add(rel(f), None, "image file not found next to the topic: %s" % b["src"])
                    else:
                        (d / b["src"]).parent.mkdir(parents=True, exist_ok=True)
                        (d / b["src"]).write_bytes(img.read_bytes())
            (d / ("%s.json" % t["id"])).write_text(json.dumps(spec, indent=2), encoding="utf-8")
            topic_sources["%d:%s" % (u["number"], t["id"])] = rel(f)
        for t in u["topics"]:
            t.setdefault("slug", slugify(t["title"]))
    word = cmap["course"].get("unit_format", "module")
    cmap["_sources"] = {"map": "course-map.md", "media": "media-plan.md", "topics": topic_sources,
                        "topic_pattern": "topics/%s-NN/<topic id>-<short-name>.md" % (word if word in UNIT_WORDS else "module")}
    out.mkdir(parents=True, exist_ok=True)
    (out / "course-map.json").write_text(json.dumps(cmap, indent=2), encoding="utf-8")
    (out / "media-plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    for e in err:
        print("ERROR " + e)
    print("Read course-map.md, media-plan.md and %d topic file(s): %d problem(s)." % (len(topic_sources), len(err)))
    return 1 if err else 0


# ---------------------------------------------------------------- from JSON


def md_cell(v):
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(md_cell(c) for c in r) + " |" for r in rows]
    return out


def yn(v):
    return "yes" if v else "no"


def course_map_md(m):
    c = m["course"]
    word = "Week" if c.get("unit_format") == "week" else "Module"
    L = ["# Course map: %s" % c["title"], "",
         "- Code: %s" % c["code"]]
    for k, label in (("college", "College"), ("audience", "Audience"), ("delivery", "Delivery")):
        if c.get(k):
            L.append("- %s: %s" % (label, c[k]))
    L += ["- Format: %s" % c.get("unit_format", "module"),
          "- Total minutes: %s" % c.get("total_minutes", ""),
          "- Completion time per page (seconds): %s" % c.get("dwell_seconds", 45)]
    if c.get("description"):
        L.append("- Description: %s" % c["description"])
    L += ["", "## Course outcomes", ""]
    L += ["- %s (%s): %s" % (o["id"], o["bloom"], o["statement"]) for o in m["outcomes"]]
    for u in m["units"]:
        L += ["", "## %s %02d: %s" % (word, u["number"], u["title"]), "",
              "- Minutes: %s" % u.get("minutes", ""), "- Build: %s" % yn(u.get("build", True)),
              "- Summary: %s" % u.get("summary", ""), "", "### Objectives", ""]
        L += ["- %s (%s; supports %s): %s" % (o["id"], o["bloom"], ", ".join(o["supports"]), o["statement"]) for o in u["objectives"]]
        L += ["", "### Topics", ""]
        L += md_table(["ID", "Title", "Minutes", "Objectives", "Type"],
                      [[t["id"], t["title"], t["minutes"], ", ".join(t["objectives"]), t.get("type", "content")] for t in u["topics"]])
        for key, label in (("activities", "Activities"), ("assessments", "Assessments")):
            L += ["", "### %s" % label, ""]
            if u.get(key):
                L += md_table(["ID", "Title", "Type", "Graded", "Points", "Where", "Objectives"],
                              [[a["id"], a["title"], a.get("type", ""), yn(a.get("graded")), a.get("points", ""), a.get("where", ""),
                                ", ".join(a.get("objectives", []))] for a in u[key]])
            else:
                L.append("None.")
        if u.get("sources"):
            L += ["", "### Built from", ""] + ["- %s" % s for s in u["sources"]]
    if m.get("conversion_notes"):
        L += ["", "## Conversion notes", ""] + ["- %s" % s for s in m["conversion_notes"]]
    if m.get("gaps"):
        L += ["", "## Gaps", ""] + md_table(["Need", "Owner", "Needed for"],
                                            [[g["item"], g.get("owner", ""), g.get("needed_for", "")] for g in m["gaps"]])
    return "\n".join(L) + "\n"


def media_plan_md(p, m):
    word = "Week" if m["course"].get("unit_format") == "week" else "Module"
    titles = {u["number"]: u["title"] for u in m["units"]}
    L = ["# Media plan: %s" % m["course"]["title"], "", "- Course code: %s" % p.get("course_code", m["course"]["code"])]
    if p.get("notes"):
        L += ["", "## Notes", ""] + ["- %s" % s for s in p["notes"]]
    for n in sorted({i["unit"] for i in p["items"]}):
        L += ["", "## %s %02d: %s" % (word, n, titles.get(n, ""))]
        for it in [i for i in p["items"] if i["unit"] == n]:
            L += ["", "### %s: %s" % (it["id"], it["title"]), ""]
            acc = it.get("accessibility", {})
            ttl = next((t["title"] for u in m["units"] if u["number"] == n for t in u["topics"] if t["id"] == it.get("topic")), "")
            rows = [("Topic", ("%s (%s)" % (it["topic"], ttl)) if ttl else it.get("topic", "")), ("Type", it.get("type", "")), ("Minutes", it.get("target_minutes", "")),
                    ("Purpose", it.get("purpose", "")), ("Script source", it.get("script_source", "")),
                    ("Script status", it.get("script_status", "")), ("Shoot", it.get("shoot", "")),
                    ("On camera", it.get("on_camera", "")), ("Production notes", it.get("production_notes", ""))]
            if "captions" in acc:
                rows.append(("Captions", yn(acc["captions"])))
            if "transcript" in acc:
                rows.append(("Transcript", yn(acc["transcript"])))
            for k, label in (("audio_description", "Audio description"), ("text_alternative", "Text alternative")):
                if k in acc:
                    rows.append((label, acc[k]))
            rows += [("Priority", it.get("priority", "")), ("Existing asset", it.get("existing_asset", "")),
                     ("Stream URL", it.get("stream_url", "")), ("Transcript URL", it.get("transcript_url", "")),
                     ("Captions verified", yn(it.get("captions_verified")))]
            L += [("- %s: %s" % (k, v)).rstrip() for k, v in rows]
    return "\n".join(L) + "\n"


def topic_md(title, spec, media_titles=None):
    media_titles = media_titles or {}
    L = ["# %s" % title, "", "Purpose: %s" % spec.get("purpose", "")]

    def textlist(t):
        return [t] if isinstance(t, str) else list(t)

    def quoted(label, paras_):
        out = ["", "> **%s**" % label]
        for p in paras_:
            out += [">", "> %s" % p]
        return out

    prev = None
    for b in spec["blocks"]:
        t = b["type"]
        if t == "heading":
            L += ["", "%s %s" % ("#" * int(b.get("level", 2)), b["text"])]
        elif t == "paragraph":
            for p in textlist(b["text"]):
                L += ["", p]
        elif t == "list":
            L.append("")
            L += [("%d. %s" % (i, x)) if b.get("ordered") else "- %s" % x for i, x in enumerate(b["items"], start=1)]
        elif t == "callout":
            L += quoted(b.get("label", "Why this matters"), textlist(b["text"]))
        elif t == "caution":
            L += quoted("Caution: %s" % b.get("label", "Caution"), textlist(b["text"]))
        elif t == "check_yourself":
            L += quoted("Check yourself", textlist(b["text"]))
        elif t == "accordion":
            for it in b["items"]:
                L += quoted("Expand: %s" % it["summary"], textlist(it["body"]))
        elif t == "video":
            vt = media_titles.get(b["media_id"])
            L += quoted("Video: %s%s" % (b["media_id"], " (%s)" % vt if vt else ""), textlist(b.get("note", [])))
        elif t == "steps":
            L += ["", "> **Steps%s**" % (": " + b["heading"] if b.get("heading") else ""), ">"]
            L += ["> %d. %s" % (i, x) for i, x in enumerate(b["items"], start=1)]
        elif t == "flashcards":
            L += ["", "> **Flashcards%s**" % (": " + b["heading"] if b.get("heading") else "")]
            if b.get("intro"):
                L += [">", "> Intro: %s" % b["intro"]]
            for c in b["cards"]:
                back = textlist(c["back"])
                L += [">", "> **Q:** %s" % c["front"], ">", "> **A:** %s" % back[0]]
                for p in back[1:]:
                    L += [">", "> %s" % p]
        elif t == "knowledge_check":
            L += ["", "> **Knowledge check%s**" % (": " + b["heading"] if b.get("heading") else "")]
            for qi, q in enumerate(b["questions"], start=1):
                L += [">", "> %d. %s" % (qi, q["stem"])]
                L += [">    - [%s] %s" % ("x" if oi == q["answer"] else " ", o) for oi, o in enumerate(q["options"])]
                L += [">", ">    Why: %s" % q.get("rationale", "")]
        elif t == "table":
            L += ["", "Table%s: %s" % ("" if b.get("row_headers", True) else " (no row headers)", b["caption"]), ""]
            L += md_table(b["columns"], b["rows"])
        elif t == "image":
            cap = ' "%s"' % b["caption"] if b.get("caption") else ""
            L += ["", "![%s](%s%s)" % (b.get("alt", ""), b["src"], cap)]
            if b.get("long_description"):
                L += ["", "> **Description**"]
                for pi, p in enumerate(textlist(b["long_description"])):
                    L += ([">"] if pi else []) + ["> %s" % p]
        prev = t
    if spec.get("sources"):
        L += ["", "## Sources", ""]
        L += ["- %s%s" % (s["text"], " (verified %s)" % s["verified"] if s.get("verified") else "") for s in spec["sources"]]
    return "\n".join(L) + "\n"


def from_json(work):
    work = pathlib.Path(work).resolve()
    m = json.loads((work / "course-map.json").read_text(encoding="utf-8"))
    (work / "course-map.md").write_text(course_map_md(m), encoding="utf-8")
    titles = {}
    if (work / "media-plan.json").exists():
        p = json.loads((work / "media-plan.json").read_text(encoding="utf-8"))
        (work / "media-plan.md").write_text(media_plan_md(p, m), encoding="utf-8")
        titles = {i["id"]: i["title"] for i in p["items"]}
    word = "week" if m["course"].get("unit_format") == "week" else "module"
    count = 0
    for u in m["units"]:
        for t in u["topics"]:
            src = work / "topics" / ("unit-%02d" % u["number"]) / ("%s.json" % t["id"])
            if not src.exists():
                continue
            spec = json.loads(src.read_text(encoding="utf-8"))
            d = work / "topics" / ("%s-%02d" % (word, u["number"]))
            d.mkdir(parents=True, exist_ok=True)
            (d / ("%s-%s.md" % (t["id"], t.get("slug") or slugify(t["title"])))).write_text(topic_md(t["title"], spec, titles), encoding="utf-8")
            count += 1
    print("Wrote course-map.md, media-plan.md and %d topic file(s). Check them, then delete the old JSON files." % count)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("compile", "from-json"):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == "compile":
        sys.exit(compile_work(sys.argv[2]))
    from_json(sys.argv[2])
