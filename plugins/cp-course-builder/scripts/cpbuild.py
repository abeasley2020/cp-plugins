"""cpbuild.py: render, check, score and package cp-course-builder modules.

    sh run-python.sh cpbuild.py render   <module-dir> [--target html|scorm]
    sh run-python.sh cpbuild.py check    <module-dir> [--stage review|package]
    sh run-python.sh cpbuild.py score    <module-dir>
    sh run-python.sh cpbuild.py package  <module-dir> [--target scorm|html] [--preview]
    sh run-python.sh cpbuild.py blueprint <blueprint.json>
    sh run-python.sh cpbuild.py status   <course-dir>
    sh run-python.sh cpbuild.py survey   <source-folder> --out <intake-dir>
    sh run-python.sh cpbuild.py standard

A module folder holds module.md (front matter: course, prefix, module, title),
lessons/*.md in reading order, optional landing.md, images/, reviews/*.json
from the three reviewer agents and build-log.csv. Output goes to
<module-dir>/build/. Nothing outside the module folder is written, except by
survey, which writes only to --out. Standard library only.
"""

import argparse
import glob
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from cpb import checks, scorm  # noqa: E402
from cpb.lessonmd import parse_front_matter, parse_lesson  # noqa: E402
from cpb.render import render_page, slug  # noqa: E402

ASSETS = os.path.join(HERE, "..", "assets")
STANDARD = os.path.join(HERE, "..", "standard", "cp-quality-standard.json")


def load_module(mdir):
    mfile = os.path.join(mdir, "module.md")
    meta = {}
    if os.path.isfile(mfile):
        meta, _ = parse_front_matter(open(mfile, encoding="utf-8").read())
    files = sorted(glob.glob(os.path.join(mdir, "lessons", "*.md")))
    if not files:
        sys.exit(f"No lessons found in {os.path.join(mdir, 'lessons')}")
    lessons = []
    for f in files:
        try:
            lessons.append(parse_lesson(open(f, encoding="utf-8").read(), f))
        except ValueError as e:
            sys.exit(f"{os.path.basename(f)}: {e}")
    num = int(meta.get("module") or lessons[0]["meta"].get("module") or 1)
    prefix = meta.get("prefix") or "cp"
    for i, l in enumerate(lessons, 1):
        m = l["meta"]
        m.setdefault("module", num)
        lead = re.match(r"^(\d+)[-_]", os.path.basename(l["path"]))
        m.setdefault("id", f"{prefix}-m{num:02d}-l{int(lead.group(1)) if lead else i:02d}")
        m.setdefault("file", f"{prefix}-module{num:02d}-{slug(m.get('title', 'lesson'))}.html")
    return meta, num, prefix, lessons


def render_module(mdir, target="html", out=None):
    meta, num, prefix, lessons = load_module(mdir)
    site = out or os.path.join(mdir, "build", "site")
    if os.path.isdir(site):
        shutil.rmtree(site)
    os.makedirs(site)
    for name in ("cp-lesson.css", "cp-lesson.js"):
        shutil.copy(os.path.join(ASSETS, name), site)
    fonts = os.path.join(ASSETS, "fonts")
    if os.path.isdir(fonts):
        shutil.copytree(fonts, os.path.join(site, "fonts"))
    imgs = os.path.join(mdir, "images")
    if os.path.isdir(imgs):
        shutil.copytree(imgs, os.path.join(site, "images"))
    outline = [(l["meta"]["id"], l["meta"].get("title", "Lesson"), l["meta"]["file"]) for l in lessons]
    pages, items = {}, []
    mtitle = meta.get("title") or f"Module {num:02d}"
    for i, l in enumerate(lessons):
        ctx = {"course": meta.get("course", ""), "module_title": f"Module {num:02d}: {mtitle}" if not str(mtitle).startswith("Module") else mtitle,
               "lessons": outline, "index": i, "target": target, "theme": meta.get("theme", "")}
        page, its = render_page(l, ctx)
        with open(os.path.join(site, l["meta"]["file"]), "w", encoding="utf-8") as fh:
            fh.write(page)
        pages[l["meta"]["id"]] = page
        items.extend(its)
    with open(os.path.join(mdir, "build", "item-bank.json"), "w", encoding="utf-8") as fh:
        json.dump(items, fh, indent=2)
    return meta, num, prefix, lessons, pages, site


def run_checks(mdir, stage="review", quiet=False):
    meta, num, prefix, lessons, pages, site = render_module(mdir)
    results = []
    for l in lessons:
        results += checks.check_lesson(l, pages[l["meta"]["id"]], {"module": num, "stage": stage, "asset_root": mdir})
    results += checks.check_module(lessons, mdir)
    results += checks.check_css(open(os.path.join(ASSETS, "cp-lesson.css"), encoding="utf-8").read())
    bdir = os.path.join(mdir, "build")
    with open(os.path.join(bdir, "checks.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    with open(os.path.join(bdir, "checks.md"), "w", encoding="utf-8") as fh:
        fh.write(checks.to_markdown(results, f"Script checks: module {num:02d}"))
    s = checks.summarize(results)
    if not quiet:
        print(f"Module {num:02d}: {s['verdict']} ({s['fail']} fail, {s['warn']} warn, {s['pass']} pass). "
              f"Report: {os.path.join(bdir, 'checks.md')}")
    return results, s


def cmd_score(mdir):
    results, _ = run_checks(mdir, quiet=True)
    for f in sorted(glob.glob(os.path.join(mdir, "reviews", "*.json"))):
        try:
            data = json.load(open(f, encoding="utf-8"))
        except ValueError as e:
            sys.exit(f"{f} is not valid JSON: {e}")
        for r in data.get("results", data if isinstance(data, list) else []):
            r.setdefault("checker", os.path.splitext(os.path.basename(f))[0])
            results.append(r)
    std = json.load(open(STANDARD, encoding="utf-8"))
    lines = ["# Module scorecard", "", f"Standard: {std['name']} v{std['version']}.", ""]
    s = checks.summarize(results)
    lines.append(f"Verdict: **{s['verdict']}**. A single fail blocks the module.")
    lines += ["", "| Criterion | Area | Result | Checkers |", "|---|---|---|---|"]
    rank = {"fail": 0, "warn": 1, "pass": 2, "na": 3}
    for c in std["criteria"]:
        rs = [r for r in results if r["criterion"] == c["id"]]
        if not rs:
            worst = "not run"
        else:
            worst = min((r["result"] for r in rs), key=lambda x: rank.get(x, 9))
        who = ", ".join(sorted({r.get("checker", "?") for r in rs})) or ("person" if c.get("person") else "")
        lines.append(f"| {c['id']} | {c['area']} | {worst} | {who} |")
    lines += ["", "## Failures and fixes, by owner", ""]
    for r in sorted([r for r in results if r["result"] == "fail"], key=lambda r: (r["owner"], r["criterion"])):
        lines.append(f"- **{r['criterion']}** ({r['target']}, {r['owner']}): {r['evidence']} Fix: {r.get('fix', '')}")
    path = os.path.join(mdir, "build", "scorecard.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"Scorecard: {s['verdict']} ({s['fail']} fail, {s['warn']} warn). {path}")
    return 1 if s["verdict"] == "fail" else 0


def cmd_package(mdir, target, preview):
    results, s = run_checks(mdir, stage="package", quiet=True)
    if s["verdict"] == "fail" and not preview:
        print(f"Not packaged: {s['fail']} blocking check(s). See build/checks.md, or use --preview for a sandbox build.")
        return 1
    meta, num, prefix, lessons, pages, site = render_module(mdir, target="scorm" if target == "scorm" else "html")
    tag = "-preview" if preview else ""
    if target == "scorm":
        zpath = os.path.join(mdir, "build", f"{prefix}-module{num:02d}-scorm{tag}.zip")
        scorm.build_zip(site, zpath, f"{prefix}-module{num:02d}", meta.get("title") or f"Module {num:02d}",
                        [(l["meta"]["id"], l["meta"].get("title", "Lesson"), l["meta"]["file"]) for l in lessons])
    else:
        zpath = shutil.make_archive(os.path.join(mdir, "build", f"{prefix}-module{num:02d}-html{tag}"), "zip", site)
    print(f"Packaged {len(lessons)} lesson(s): {zpath}")
    return 0


def cmd_blueprint(path):
    bp = json.load(open(path, encoding="utf-8"))
    results = checks.check_blueprint(bp, os.path.basename(path))
    out = os.path.splitext(path)[0] + "-checks.md"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(checks.to_markdown(results, "Blueprint checks"))
    s = checks.summarize(results)
    print(f"Blueprint: {s['verdict']} ({s['fail']} fail, {s['warn']} warn). {out}")
    return 1 if s["verdict"] == "fail" else 0


def cmd_status(cdir):
    mods = sorted(glob.glob(os.path.join(cdir, "modules", "module-*")))
    if not mods:
        print("No modules yet. Run /cp-course-builder:blueprint first.")
        return 0
    for m in mods:
        cj = os.path.join(m, "build", "checks.json")
        n = len(glob.glob(os.path.join(m, "lessons", "*.md")))
        if os.path.isfile(cj):
            s = checks.summarize(json.load(open(cj, encoding="utf-8")))
            state = f"checks {s['verdict']} ({s['fail']} fail, {s['warn']} warn)"
        else:
            state = "not checked"
        rv = len(glob.glob(os.path.join(m, "reviews", "*.json")))
        print(f"{os.path.basename(m)}: {n} lesson(s), {state}, {rv} of 3 reviews in")
    return 0


KINDS = {".pptx": "deck", ".ppt": "deck", ".pdf": "pdf", ".docx": "document", ".doc": "document", ".txt": "text",
         ".md": "text", ".csv": "table", ".xlsx": "table", ".png": "image", ".jpg": "image", ".jpeg": "image",
         ".svg": "image", ".gif": "image", ".mp4": "video", ".mov": "video", ".vtt": "captions", ".srt": "captions",
         ".zip": "archive", ".html": "web", ".json": "data", ".cptx": "captivate"}


def cmd_survey(src, out):
    """Read-only listing of a source folder for intake. Writes only to out."""
    rows = []
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.startswith("."):
                continue
            p = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            rows.append({"path": os.path.relpath(p, src).replace(os.sep, "/"), "kind": KINDS.get(ext, "other"),
                         "bytes": os.path.getsize(p)})
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "survey.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
    counts = {}
    for r in rows:
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    print(f"{len(rows)} file(s): " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    return 0


AREAS = {"R": "Rigor", "D": "Design and accessibility", "M": "Multimedia and learning science", "A": "Andragogy", "P": "Process"}


def cmd_standard():
    """Rebuild skills/cp-build/references/quality-standard.md from the JSON."""
    d = json.load(open(STANDARD, encoding="utf-8"))
    out = [f"# CP Course Quality Standard v{d['version']}", "",
           "This file is generated from `standard/cp-quality-standard.json`, which is the only place the standard lives. "
           "Edit the JSON, then run `sh scripts/run-python.sh scripts/cpbuild.py standard` to rebuild this page.", "",
           f"Floor: {d['floor']}. Every criterion is a yes or no. One fail blocks the module.", "",
           "## Precedence when criteria conflict", ""]
    out += [f"{i}. {p}" for i, p in enumerate(d["precedence"], 1)]
    cur = None
    for c in d["criteria"]:
        if c["id"][0] != cur:
            cur = c["id"][0]
            out += ["", f"## {AREAS[cur]}", "", "| ID | Criterion | Checked by | Fix owner | Stage |", "|---|---|---|---|---|"]
        who = (["script"] if c["script"] else []) + ([c["agent"]] if c["agent"] else []) + ([c["person"]] if c.get("person") else [])
        out.append(f"| {c['id']} | {c['criterion']} | {', '.join(who)} | {c['owner']} | {c['stage']} |")
    path = os.path.join(HERE, "..", "skills", "cp-build", "references", "quality-standard.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"Wrote {os.path.normpath(path)}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cpbuild.py", description="cp-course-builder engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render"); r.add_argument("module"); r.add_argument("--target", default="html", choices=["html", "scorm"])
    c = sub.add_parser("check"); c.add_argument("module"); c.add_argument("--stage", default="review", choices=["review", "package"])
    s = sub.add_parser("score"); s.add_argument("module")
    p = sub.add_parser("package"); p.add_argument("module"); p.add_argument("--target", default="scorm", choices=["scorm", "html"])
    p.add_argument("--preview", action="store_true", help="build even with blocking checks, named -preview, for a sandbox")
    b = sub.add_parser("blueprint"); b.add_argument("path")
    st = sub.add_parser("status"); st.add_argument("course")
    sv = sub.add_parser("survey"); sv.add_argument("source"); sv.add_argument("--out", required=True)
    sub.add_parser("standard", help="rebuild references/quality-standard.md from the JSON")
    a = ap.parse_args(argv)
    if a.cmd == "render":
        *_, site = render_module(a.module, a.target)
        print(f"Rendered to {site}")
        return 0
    if a.cmd == "check":
        _, s = run_checks(a.module, a.stage)
        return 1 if s["verdict"] == "fail" else 0
    if a.cmd == "score":
        return cmd_score(a.module)
    if a.cmd == "package":
        return cmd_package(a.module, a.target, a.preview)
    if a.cmd == "blueprint":
        return cmd_blueprint(a.path)
    if a.cmd == "status":
        return cmd_status(a.course)
    if a.cmd == "standard":
        return cmd_standard()
    if a.cmd == "survey":
        return cmd_survey(a.source, a.out)


if __name__ == "__main__":
    sys.exit(main())
