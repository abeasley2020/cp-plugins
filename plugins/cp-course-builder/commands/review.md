---
description: Score one module against the CP Course Quality Standard with the script checks and three read-only reviewers, route fixes, and write the scorecard
argument-hint: <course-folder> <module-number> [--rounds 3]
---

Arguments: `$ARGUMENTS`

1. Plugin root: `${CLAUDE_PLUGIN_ROOT}` (or the folder holding `scripts/cpbuild.py`). Read `skills/cp-build/SKILL.md` and `references/review-format.md`.
2. Run `sh <plugin>/scripts/run-python.sh <plugin>/scripts/cpbuild.py check <module>`. If `<plugin>/scripts/node_modules` exists, also run `node <plugin>/scripts/axe.mjs <module>/build/site --out <module>/build/axe.json`.
3. Run **cp-rigor-reviewer**, **cp-learning-science-reviewer** and **cp-design-reviewer** in parallel on the module. They are read-only and return JSON. Save each answer to `<module>/reviews/<reviewer>.json`. If an answer is not valid JSON in the documented shape, ask that reviewer once more; if it still is not, record the reviewer as not run.
4. Run `sh <plugin>/scripts/run-python.sh <plugin>/scripts/cpbuild.py score <module>`.
5. If the scorecard has fails and the round limit (default 3) is not reached: send each fail to its owner agent with the evidence and the fix, then repeat from step 2. Add a build-log row per round.
6. Report the verdict, the fails still open with their owners, the warns the ID should see, and the person checks still owed (D5 screenshots, D7 spot check, D9 look test, faculty checks for R5 and P2). Never mark a criterion passed that only a person can pass.
7. When the verdict is pass and the ID has signed Gate 2, package with `cpbuild.py package <module> --target scorm`.
