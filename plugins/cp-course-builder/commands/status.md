---
description: Show where a course build stands, module by module, and the next human action
argument-hint: <course-folder>
---

Arguments: `$ARGUMENTS`

1. Plugin root: `${CLAUDE_PLUGIN_ROOT}` (or the folder holding `scripts/cpbuild.py`).
2. Report the gate the course is at: Gate 0 if `intake/notes.md` is missing or unsigned, Gate 1 if line 1 of `blueprint/blueprint.md` is not `status: APPROVED`.
3. Run `sh <plugin>/scripts/run-python.sh <plugin>/scripts/cpbuild.py status <course>` and show its lines.
4. For each module, add the next human action in one line: approve the blueprint, answer gaps, review screenshots, sign Gate 2, or import the package. Read-only: change nothing.
