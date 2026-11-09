#!/usr/bin/env python3
"""
build.py: the deterministic half of the pipeline, in one command that works
the same in PowerShell, Command Prompt, macOS and Linux. Run it after the
agents have written the Markdown sources, or any time an ID edits them.

    python build.py <work-folder> [--format module|week] [--units 1,2]

Reads    course-map.md, media-plan.md, topics/<module|week>-NN/*.md
Writes   docs/        course map and media plan for review (HTML and CSV)
         build/       rendered pages, plus build/source/, the JSON the
                      scripts use (generated each run; never edit it)
         dist/        one SCORM 1.2 zip and one HTML zip per module or week
         accessibility-report.md and axe-results.json

Steps: read the Markdown, validate, render review docs, render topic pages,
package, accessibility gate. Stops at the first step that fails and says why.
"""

import argparse
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PY = sys.executable


def run(step, total, label, cmd, cwd=None, allow_fail=False):
    print("== %d/%d %s" % (step, total, label), flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=cwd)
    if r.returncode and not allow_fail:
        print("Stopped at step %d (%s). Fix what is listed above, save, and run the build again." % (step, label))
        sys.exit(r.returncode)
    return r.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work")
    ap.add_argument("--format", choices=["module", "week"])
    ap.add_argument("--units", help="comma list of unit numbers to package, default all")
    ap.add_argument("--check", action="store_true", help="only read and validate the Markdown; build nothing")
    a = ap.parse_args()
    w = pathlib.Path(a.work).resolve()
    src = w / "build" / "source"
    total = 7

    for d in (("build",) if a.check else ("build", "dist")):
        shutil.rmtree(w / d, ignore_errors=True)
    read = run(1, total, "read the Markdown sources", [PY, HERE / "md_sources.py", "compile", w], allow_fail=True)
    if not (src / "course-map.json").exists():
        sys.exit(read or 1)
    checked = run(2, total, "validate", [PY, HERE / "validate.py", "--map", src / "course-map.json", "--media", src / "media-plan.json",
                                         "--topics", src / "topics"], allow_fail=True)
    if read or checked:
        print("Stopped after step 2. Fix what is listed above, save, and run the build again.")
        sys.exit(1)
    if a.check:
        print("Check passed. The Markdown sources read cleanly and the alignment holds.")
        return
    run(3, total, "review docs", [PY, HERE / "render_docs.py", "--map", src / "course-map.json", "--media", src / "media-plan.json",
                                  "--out", w / "docs"])
    fmt = ["--format", a.format] if a.format else []
    run(4, total, "topic pages", [PY, HERE / "render_topics.py", "--map", src / "course-map.json", "--media", src / "media-plan.json",
                                  "--topics", src / "topics", "--out", w / "build"] + fmt)
    units = ["--units", a.units] if a.units else []
    run(5, total, "packages", [PY, HERE / "build_packages.py", w / "build" / "course.json", "--out", w / "dist"] + units)

    node = shutil.which("node")
    npm = shutil.which("npm")
    if node and not (HERE / "node_modules" / "axe-core").is_dir() and npm:
        print("Installing axe-core once (npm install) ...", flush=True)
        subprocess.run([npm, "install", "--silent", "--no-fund", "--no-audit"], cwd=HERE, shell=sys.platform == "win32")
    axe = w / "axe-results.json"
    if node and (HERE / "node_modules" / "axe-core").is_dir():
        run(6, total, "accessibility: axe-core", [node, HERE / "a11y_check.mjs", w / "build" / "content", w / "docs", "--out", axe],
            allow_fail=True)
        axe_arg = ["--axe", axe]
    else:
        print("== 6/%d accessibility: axe-core skipped (install Node.js, then run npm install in %s)" % (total, HERE))
        axe_arg = []
    code = run(7, total, "accessibility: Purdue and WCAG 2.2 AA checks",
               [PY, HERE / "a11y_static.py", w / "build" / "content", w / "docs", "--report", w / "accessibility-report.md",
                "--base", str(w) + "/"] + axe_arg, allow_fail=True)
    print("Done. Packages in %s, accessibility report in %s" % (w / "dist", w / "accessibility-report.md"))
    if not axe_arg:
        print("The axe-core check did not run, so the build is not cleared for release until it does.")
    sys.exit(code)


if __name__ == "__main__":
    main()
