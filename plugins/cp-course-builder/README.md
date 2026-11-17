# cp-course-builder

Builds Brightspace lessons that look and behave like a well-made Rise 360 course, in code, from faculty source. Every module is scored against the CP Course Quality Standard by the script checks and three read-only review agents, and nothing packages while a single criterion fails.

Status: 0.1.0, first draft for team review. Not yet used on a live course.

## What is in it

| Part | What it does |
|---|---|
| `standard/cp-quality-standard.json` | The CP Course Quality Standard v1: 35 yes or no criteria in five areas (rigor, design and accessibility, multimedia and learning science, andragogy, process) and 7 precedence rules for when criteria conflict. Each criterion names who checks it (script, agent, person) and who fixes it. |
| `skills/cp-build/` | The build skill: course folder layout, gates, the lesson Markdown format, the design system and ban list, the blueprint and review formats, and college profiles. |
| `agents/cp-course-mapper.md` | Writes the blueprint: outcomes, objectives with Bloom levels, lessons, minutes, graded authentic tasks. |
| `agents/cp-lesson-writer.md` | Writes lesson Markdown and the module landing page, then checks it. |
| `agents/cp-rigor-reviewer.md` | Read-only. Scores R1, R4, R5, R6, R7 and A6. |
| `agents/cp-learning-science-reviewer.md` | Read-only. Scores M1, M2, M4, M6, M9, A1, A2, A3 and A5. |
| `agents/cp-design-reviewer.md` | Read-only. Scores D3, D5, D6 and D9. |
| `scripts/cpbuild.py` | The engine (Python standard library only): render, check, score, package, blueprint, status, survey. |
| `assets/` | `cp-lesson.css` and `cp-lesson.js`, the only stylesheet and script a page uses. |
| `examples/fspg-101/` | One fictional lesson that passes every script check. |

The three reviewers have only Read, Glob and Grep. They cannot write or run anything; they return JSON and the review command saves it.

## Commands

| Command | Use it to |
|---|---|
| `/cp-course-builder:start <faculty-folder>` | Survey the faculty folder (read only) and write intake notes. Stops at Gate 0. |
| `/cp-course-builder:blueprint <course-folder>` | Build and check the blueprint. Stops at Gate 1. |
| `/cp-course-builder:build-module <course-folder> <NN>` | Write, render and script-check one module. |
| `/cp-course-builder:review <course-folder> <NN>` | Run the script checks and the three reviewers, route fixes (up to three rounds), and write the scorecard. |
| `/cp-course-builder:status <course-folder>` | Show where each module stands and the next human action. |

## The look

One lesson per page, a sidebar outline with progress, a header with the lesson title and minutes, one reading column, flat full-width blocks with cream bands for cases and practice, and continue dividers at natural pauses. No shadows, rounded cards or gradients. Every component (accordion, tabs, process, flashcards, labeled graphic, knowledge check, scenario, sorting, recall) works with scripts off, in print and in the Brightspace mobile app; `cp-lesson.js` only adds behavior.

## Who checks what

- **Script** (`cpbuild.py check` and `cpbuild.py blueprint`): 27 of the 35 criteria in part or whole, for example inline styles, tokens, heading order, alt text length, long descriptions, paragraph runs, interaction mix, retrieval set size, spaced items, minutes, house style, draft status and the build log.
- **Agents**: the judgment half, for example whether a source supports a claim, whether feedback explains, whether a figure explains something, whether the module looks AI-made.
- **People**: D5 screenshots against the art direction brief, the D7 spot check in the mobile app, the D9 monthly look test, faculty accuracy (R5) and faculty-voiced text (P2).

## Install

```
/plugin install cp-course-builder --marketplace abeasley2020/cp-plugins
```

Or add the marketplace once with `/plugin marketplace add abeasley2020/cp-plugins`, then `/plugin install cp-course-builder@cp-plugins`.

## Requirements and setup

Claude Code, Python 3.8 or later. For the accessibility run, Node.js 20 or later and, once, `npm install` in `scripts/` (axe-core and jsdom, pinned). The commands call Python through `scripts/run-python.sh`, which finds `python3` or `python`.

## Known limits in 0.1.0

- axe runs under jsdom, which cannot measure color contrast, target size or reflow. The stylesheet's contrast was computed by hand (every text pair is 4.5:1 or better), but D3 stays open until a browser check runs. Playwright is listed as optional.
- No screenshot step yet, so D5 is always a person's check.
- The Source Sans 3 font file is not shipped; pages fall back to the system sans.
- SCORM 1.2 is the only package format. The strategy calls for Common Cartridge on credit courses; that is still to decide.

## Privacy

See [PRIVACY.md](PRIVACY.md).
