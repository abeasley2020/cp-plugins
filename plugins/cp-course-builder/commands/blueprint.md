---
description: Build and check the course blueprint (outcomes, objectives, lessons, assessments) and stop at Gate 1
argument-hint: <course-folder>
---

Arguments: `$ARGUMENTS`

1. Plugin root: `${CLAUDE_PLUGIN_ROOT}` (or the folder holding `scripts/cpbuild.py`). Read `skills/cp-build/SKILL.md`.
2. Check that `<course>/intake/notes.md` exists. If not, tell the user to run `/cp-course-builder:start` first and stop.
3. Run the **cp-course-mapper** agent with the plugin root and course folder.
4. Run `sh <plugin>/scripts/run-python.sh <plugin>/scripts/cpbuild.py blueprint <course>/blueprint/blueprint.json`. If it fails, send the failures back to cp-course-mapper, at most three rounds.
5. Remind the user what Gate 1 needs besides the blueprint: a one-page `blueprint/art-direction.md` (mood, shot list, illustration style, one signature visual, two reference pages) and one reference lesson built by hand to it in `blueprint/reference-lesson/`.
6. Report the outcome count, module and lesson counts, learner minutes against credit hours, and the gaps. Stop. The ID sets line 1 of `blueprint.md` to `status: APPROVED`; then `/cp-course-builder:build-module <course> <NN>`.
