---
description: Write, render and script-check every lesson in one module from the approved blueprint
argument-hint: <course-folder> <module-number>
---

Arguments: `$ARGUMENTS`

1. Plugin root: `${CLAUDE_PLUGIN_ROOT}` (or the folder holding `scripts/cpbuild.py`). Read `skills/cp-build/SKILL.md`.
2. Gate 1: line 1 of `<course>/blueprint/blueprint.md` must read `status: APPROVED`. If not, say so and stop. Never set it yourself.
3. Module folder: `<course>/modules/module-NN/`. It must hold `module.md`.
4. Run the **cp-lesson-writer** agent for the module. Lessons in one module are independent, so when there are several the writer may draft them in parallel; it writes `landing.md` last.
5. Run `sh <plugin>/scripts/run-python.sh <plugin>/scripts/cpbuild.py check <module>`. Send each fail to its owner (cp-lesson-writer or cp-course-mapper), then check again. Stop after three rounds and report what still fails.
6. Report the lessons built, their words and minutes, the check verdict, and the gaps. Next: `/cp-course-builder:review <course> <NN>`.
