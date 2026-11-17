---
name: cp-build
description: "Course Production build standard for Rise 360 style lessons built in code. Load before any cp-course-builder step: intake, blueprint, lesson writing, review, packaging or status. Holds the course folder layout, the gates, the lesson Markdown format, the design system, the CP Course Quality Standard every reviewer scores against, and the commands that render, check and package."
---

# CP course build

One engine, every course. Agents write Markdown; `scripts/cpbuild.py` renders it into lessons that look and behave like Rise 360, checks them against the CP Course Quality Standard, and packages them for Brightspace. Nobody hand-edits the HTML.

Read these before you start, in this order:

1. `references/quality-standard.md`: the 35 criteria and the 7 precedence rules. This is the checklist. Every reviewer scores against it and nothing else.
2. `references/lesson-format.md`: the lesson Markdown and its blocks.
3. `references/design-system.md`: the Rise look, the tokens and the ban list.
4. `references/blueprint-format.md`: outcomes, objectives, lessons and assessments.
5. `references/review-format.md`: the review JSON, fix rounds and the build log.
6. The college profile named in the blueprint, under `profiles/`.

## The course folder

All work for one course lives in one folder the ID names, by default `<course>-cpb/` beside the faculty folder. The faculty folder is never changed.

```
<course>-cpb/
  intake/survey.json, intake/notes.md      what the faculty sent and what it covers
  blueprint/blueprint.json, blueprint.md   outcomes, objectives, lessons, assessments (Gate 1)
  blueprint/art-direction.md               the one-page brief (Gate 1)
  blueprint/reference-lesson/              the hand-built reference lesson
  decisions.md                             every negotiated choice and every waiver, dated
  modules/module-NN/
    module.md                              front matter: course, prefix, module, title
    landing.md                             the module landing page (problem, reflect)
    lessons/NN-slug.md                     one file per lesson
    images/                                faculty images, SVG diagrams, licensed photos
    reviews/<reviewer>.json                review results, saved by the review command
    build-log.csv                          P3
    build/                                 generated: site/, checks.md, scorecard.md, zips
```

## Gates

| Gate | What must be true | Who signs |
|---|---|---|
| 0 Intake | `intake/notes.md` lists every file, what it covers and what is missing | ID |
| 1 Blueprint | `blueprint.md` line 1 reads `status: APPROVED`; blueprint checks pass; art direction brief and reference lesson exist | ID, faculty for accuracy |
| 2 Module | Scorecard verdict is pass: zero fails across the script checks and the three reviewers; screenshots scored (D5) | ID |
| 3 Launch | P1 and P2 pass at the package stage; faculty approved faculty-voiced text | ID, faculty |

One fail blocks the module. A waiver is the ID's call, never an agent's, and goes in `decisions.md` with the reason.

## Commands the agents run

Use `sh <plugin>/scripts/run-python.sh <plugin>/scripts/cpbuild.py ...` (it finds python3 or python). Standard library only.

| Command | Does |
|---|---|
| `survey <faculty-folder> --out <course>/intake` | Read-only file listing |
| `blueprint <course>/blueprint/blueprint.json` | R1, R2, R3, R8 at the course level |
| `render <module>` | Builds `build/site/` |
| `check <module>` | Renders, then runs every script check; writes `build/checks.md` and `build/item-bank.json` |
| `score <module>` | Merges script checks and `reviews/*.json` into `build/scorecard.md` |
| `package <module> [--target scorm\|html] [--preview]` | Refuses on any fail unless `--preview` |
| `status <course>` | One line per module |

Accessibility: `node <plugin>/scripts/axe.mjs <module>/build/site --out <module>/build/axe.json` after `npm install` in `<plugin>/scripts`. Under jsdom, axe cannot measure contrast, target size or reflow; those need a real browser (`playwright` is optional in `package.json`) or the ID's check, and D3 stays open until one of them runs.

## Rules for every agent

- Never invent subject matter, a case, a number or a quote. Mark it `[GAP: what is missing]` and move on. Rule 2 beats every engagement criterion.
- Write in sentence case, as a colleague, with no em-dashes and no exclamation points.
- Fix the Markdown source, never the rendered HTML.
- Record every skipped interaction or criterion with its reason in `decisions.md`.
- This repository is public. Commit only fictional examples; never commit real course content, people's names, prices or internal links.
