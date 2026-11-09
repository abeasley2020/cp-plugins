---
name: course-production-standards
description: Course Production standards for turning faculty content into a course map, a media plan, and Brightspace packages. Load before any course-agents step: intake, mapping, media planning, topic writing, packaging, or the accessibility check. Holds the Markdown source formats, the Purdue style rules, the packaging rules (one package per module or week, never a whole course), and the WCAG 2.2 AA gate.
---

# Course Production standards

These rules bind every agent in this plugin. Where a rule here conflicts with a faculty request, the rule wins and the agent says so in its report.

## The pipeline

1. **Inventory** (content-inventory): `scripts/intake.py` extracts text from the faculty folder, reading scanned PDFs and photos of handouts with OCR (`scripts/ocr.py`). The agent transcribes anything OCR could not read, then writes `inventory-summary.md`: what is there, what each file covers, live-course language that must be converted, existing media, and gaps.
2. **Course map** (course-mapper): writes `course-map.md` (format: `references/course-map-format.md`).
3. **Media plan** (media-planner): writes `media-plan.md` (format: `references/media-plan-format.md`).
4. **Topics** (topic-writer): writes one Markdown file per topic under `topics/module-NN/` or `topics/week-NN/` (format: `references/topic-format.md`). Agents never write HTML by hand; the build renders it.
5. **Packages** (package-builder): `scripts/build.py` reads the Markdown, validates it, and renders and packages it.

Everything an ID reads or edits is Markdown. The build turns the Markdown into JSON under `build/source/` for the scripts on every run; that JSON is never edited and never handed to anyone. When an ID edits a Markdown file, `python <plugin>/scripts/build.py <work>` rebuilds everything from it.
6. **Accessibility gate** (accessibility-checker): `a11y_check.mjs` (axe-core) plus `a11y_static.py` (house rules, CSS cascade contrast, target size, reflow). Nothing is called done while the report says FAIL.

All work for one course lives in one work folder, by default `<faculty-folder>-cp/`, with this layout:

```
<work>/
  intake/inventory.json, intake/text/*.txt, intake/pages/*.png (scanned pages to read by eye)
  inventory-summary.md
  course-map.md                      ID-editable source
  media-plan.md                      ID-editable source
  topics/module-01/t01-short-name.md ID-editable source, one per topic
  docs/course-map.html, docs/media-plan.html, docs/media-plan.csv
  build/source/*.json (generated), build/content/<module-or-week-folder>/*.html, build/course.json
  dist/<code>-module-01-scorm12.zip, dist/<code>-module-01-html.zip, ...
  axe-results.json, accessibility-report.md
  run-report.md
```

## Packaging rules (non-negotiable)

- The course map's Format is `module` or `week`. One package per unit. A whole-course package is never built; the scripts refuse it.
- Each SCORM 1.2 package has one organization, one unit item, and one nested item per topic page. Brightspace shows the unit as its own module with one page per topic and supplies the navigation.
- Every unit starts with a generated overview page (objectives, topics with minutes, what is graded) built from the course map, so learners and the map never disagree.
- Topic sources contain no JavaScript. The completion wrapper is injected into the packaged copy only. Completion is end of page plus 45 seconds. No score is reported; graded work lives in Brightspace quizzes and assignment folders.
- Videos are streamed (Kaltura) and linked, never bundled. A video box renders only when its media plan entry has a Stream URL and Captions verified is yes. Until then the page ships without it and the render report lists it.
- Two builds from one source: the SCORM zip, and a plain HTML zip of the same pages for Brightspace Manage Files on Purdue courses.
- Titles in the Brightspace tree are numbered "1.1", "1.2"; activities are prefixed "Activity:". No term, year, cohort, or due date in any title.

## Course design rules

- Two levels only: course outcomes (CLO1...) and unit objectives (1.1, 1.2...). Every objective has a Bloom level and supports at least one course outcome. Every course outcome is supported by at least one unit objective.
- Every unit objective is taught by at least one topic and evidenced by at least one activity or assessment. The validator enforces both.
- Target 8 to 15 minutes per topic and 45 to 75 minutes per unit. A short course is 180 to 240 minutes in total.
- Convert live-course material for on-demand delivery: strip dates, day and week references, Zoom or Teams language, and cohort language ("your classmates", "the discussion board"). Replace a live discussion with a self-check that has a model answer, or a graded Brightspace assignment, and record what was lost under Conversion notes in the course map so faculty can weigh in.
- Never invent facts the faculty did not supply. Where a claim can go stale (a regulation, a price, a statistic), add `(verified YYYY-MM-DD)` to the source line and list it under Gaps for faculty review.
- Every gap goes under Gaps with an owner. The course map is a draft for ID and faculty review, not a final.

## Writing rules

- No em-dashes. No exclamation points in body copy. Active voice. Plain words, short paragraphs.
- No sight or click language: never "see below", "as shown to the right", "click here". Name the section instead.
- Link text describes the destination. External links get "(external site)" automatically.
- Each topic opens with "What this topic is for" (the `Purpose:` line) and closes with a "Check yourself" box. The renderer writes the "Next topic" line.
- Knowledge checks are practice: options marked `[ ]` and `[x]` in the source and shown lettered, the answer behind a disclosure, one sentence of rationale that also says why the others fall short.

## Purdue style (applied by the renderer; listed so agents never fight it)

- Header band: Purdue Black `#000000` with Boilermaker Gold `#CFB991` text (11.0:1).
- Body text `#000000` on `#FFFFFF`. Secondary text Steel `#555960` (7.0:1).
- `h2` in Bold Gold `#8E6F3E` on white only (4.7:1). Bold Gold is never used on cream.
- Links `#964F37`, underlined. This is also the only coral allowed for small text on cream (5.2:1). `#CC785C` and the old gold `#CEB888` are banned.
- Callouts on cream `#F0EEE6` with black text; table headers `#EBD99F` with black text; functional borders Steel.
- Boilermaker Gold is a decorative rule or a background behind black text. It is never text on white or cream.
- Focus ring: 3 px `#964F37`, at least 3:1 on every surface. Every disclosure control is at least 44 px tall.
- Font stack: Acumin Pro and United Sans when installed, then system sans. No web fonts, no external stylesheets.

## The accessibility gate

Run both checkers on `build/content` and `docs`. The report must say PASS or PASS WITH NOTES before the orchestrator calls the run done. A FAIL goes back to the agent that owns the Markdown source (topic-writer for content, course-mapper for structure, package-builder for rendering), never patched in the built HTML. The manual checks listed at the end of the report (keyboard pass in Brightspace, 320 px in the mobile app, caption accuracy, screen reader spot check) are owned by the ID and named in the run report.
