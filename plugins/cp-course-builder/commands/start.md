---
description: Start a course build from a faculty folder; survey it read-only, write intake notes, and stop at Gate 0
argument-hint: <faculty-folder> [--course <course-folder>] [--profile <profile>]
---

You run intake for the CP course builder. You read the faculty folder and never change it.

Arguments: `$ARGUMENTS`

1. Plugin root: `${CLAUDE_PLUGIN_ROOT}`. If that did not expand, find the folder that holds `scripts/cpbuild.py` and `skills/cp-build/SKILL.md`. Read `skills/cp-build/SKILL.md`.
2. Course folder: the `--course` value, or `<faculty-folder>-cpb/` beside the faculty folder. Never write into the faculty folder.
3. Run `sh <plugin>/scripts/run-python.sh <plugin>/scripts/cpbuild.py survey <faculty-folder> --out <course>/intake`.
4. Read the syllabus, outcomes and decks the survey lists. Write `<course>/intake/notes.md`: each file and what it covers, which module it belongs to, current versus superseded versions, existing images and media, live-course language that needs an asynchronous replacement, and every gap with an owner.
5. Pick the college profile (`--profile`, or the closest one in `skills/cp-build/profiles/`). If none fits, copy `_template.md` to a new profile in the course folder and fill in what the files show.
6. Create `<course>/decisions.md` with a dated first line.
7. Tell the user what was found in a few lines, list the gaps, and stop. Gate 0 is the ID's sign-off on the notes. The next step is `/cp-course-builder:blueprint <course>`.
