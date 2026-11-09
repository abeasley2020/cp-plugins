# Course Production Agents

A Claude Code plugin for Purdue University Online's Course Production team. Point it at a folder of faculty content, scanned handouts included, and it produces:

1. **A course map**: outcomes, modules or weeks, objectives with Bloom levels, topics with minutes, activities and assessments, and the alignment between them, plus the gaps faculty still owe.
2. **A media plan**: every video, animation, screencast, and graphic, with type, length, script source, shoot plan, production notes, and captions, transcript and audio description requirements. Also a CSV for producers.
3. **Brightspace packages, one per module or week**: a SCORM 1.2 zip and a plain HTML zip for each unit. It never builds a whole-course package; the scripts refuse to.

Every page is Purdue branded and checked against WCAG 2.2 AA before the run is called done.

Everything an ID reads or edits is Markdown: `course-map.md`, `media-plan.md`, and one `.md` file per topic. Open them in any text editor, VS Code, Typora, or a Markdown preview. Nobody edits JSON.

## How it is built

| Piece | What it does |
|---|---|
| `commands/build-course.md` | The orchestrator, run as `/build-course <folder>`. Calls the agents in order and checks each step. It is a command rather than an agent because Claude Code subagents cannot start other subagents. |
| `agents/content-inventory.md` | Extracts text from the folder once (scanned PDFs and photos of handouts through OCR), transcribes anything OCR could not read from the page image, and summarizes what is there, what must be converted from live delivery, and what is missing. |
| `agents/course-mapper.md` | Writes `course-map.md` and checks the alignment. |
| `agents/media-planner.md` | Writes `media-plan.md`. |
| `agents/topic-writer.md` | Writes each topic as a Markdown file from the faculty's own material. Agents never write HTML. |
| `agents/package-builder.md` | Renders pages and builds and validates the packages. |
| `agents/accessibility-checker.md` | Runs the WCAG 2.2 AA gate and routes failures to the agent that owns the source. |
| `skills/course-production-standards/` | The rules every agent follows, plus the three Markdown formats (`references/*-format.md`), written so IDs can learn them in a few minutes. |
| `scripts/` | Deterministic Python and Node tools. The agents decide; the scripts read the Markdown, render, package, and check, so output is the same every time. `build.py` runs the whole build in one command on Windows, macOS or Linux. |
| `templates/topic.css` | The one Purdue stylesheet used by every page. |

The split matters: content judgment (what to teach, what to film) is the agents' job, and everything that has to be exact (HTML, manifests, contrast, structure) is a script's job. The scripts turn the Markdown into JSON under `build/source/` on every build; that JSON is generated, never edited, and never handed to anyone.

## Setup (once)

```
python -m pip install python-docx python-pptx pypdf pypdfium2 rapidocr_onnxruntime
```
```
cd scripts
```
```
npm install
```
```
npx playwright install chromium
```

`pypdfium2` and `rapidocr_onnxruntime` read scanned PDFs and photos of handouts with no system install. If Tesseract is installed and on PATH (with `pip install pytesseract`), intake uses it instead. With no OCR engine at all, intake saves each scanned page as a picture and the content-inventory agent reads it directly, so scanned material is never skipped.

The last command is optional but recommended. With Chromium installed, axe-core measures contrast, target size, and 320 px reflow in a real browser. Without it, axe runs in jsdom and the Python checker covers those three from the CSS.

Python 3.8 or later is required. The agents run every script through `scripts/run-python.sh`, which uses the first of `python3`, `python` or `py -3` that really runs Python 3. That matters on Windows, where `python3` is often a Microsoft Store placeholder that runs nothing.

### Install the plugin

From GitHub, in a Claude Code session:

```
/plugin marketplace add abeasley2020/cp-plugins
/plugin install course-production-agents@cp-plugins
```

Restart the session afterward. Run `/plugin marketplace update cp-plugins` to pick up new versions.

- From the Claude plugin directory, once it is listed: add **Course Production Agents** from the directory on claude.ai. It then appears in Claude Code through account sync.
- From a clone of this repository, for testing: `claude --plugin-dir <path-to>/cp-plugins/plugins/course-production-agents`.

### What the plugin runs, reads and sends

- It reads the faculty folder you name and writes only to a `<folder>-cp/` work folder beside it. The faculty folder is never written to.
- It runs the bundled Python and Node scripts locally. The scripts send no course content to any outside service.
- The first build runs `npm install` in `scripts/` if `axe-core` is missing. That downloads the pinned packages in `scripts/package.json` (axe-core, jsdom, and optionally Playwright) from the npm registry. `npx playwright install chromium` downloads a browser for the accessibility checks.
- It never uploads to Brightspace, Kaltura, SharePoint or any other system, and never emails or messages anyone. You import the zips yourself.

## Example prompts

- `/build-course "C:\Courses\FNR 210 faculty files"` builds the course map, media plan, topics and one package per module.
- `/build-course "C:\Courses\FNR 210 faculty files" --review` stops after the course map and media plan so an ID can approve them first.
- `/build-course "C:\Courses\FNR 210 faculty files" --format week` packages by week instead of by module.
- After a build, "Add one or two infographics to each topic in Week 01, each with a full description" adds SVG figures with a description accordion under each.
- "Rebuild the packages after my edits to topics/week-02" re-renders and rechecks without rewriting content.

## Run it on a real folder

```
/build-course "C:\Courses\FNR 210 faculty files"
```

Options:

- `--format week` to package by week instead of by module.
- `--units 1,2` to package only some units this run (the map still covers the whole course).
- `--review` to stop after the course map and media plan so an ID can approve them before any topics are written. Recommended for a new faculty partner.

Output goes to a work folder beside the faculty folder (`<folder>-cp/`). The faculty folder is never written to.

After an ID edits `course-map.md`, `media-plan.md`, or any topic file, rebuild without the agents. On Windows (PowerShell or Command Prompt):

```
python scripts\build.py "C:\Courses\FNR 210 faculty files-cp"
```

On macOS or Linux:

```
python3 scripts/build.py "/Courses/FNR 210 faculty files-cp"
```

Add `--format week` or `--units 1,2` as needed, or `--check` to only check the Markdown without building. If something is wrong, the build stops and names the file and line, for example `topics/module-02/t03-manure-compost.md line 23: knowledge check question 1 has no correct answer marked [x]`. Fix it in the Markdown and run it again.

## Editing the Markdown

The three formats are in `skills/course-production-standards/references/`. The short version:

- **Course map**: `- Field: value` lines at the top, `## Module 01: Title` for each unit, objectives as `- 1.1 (Apply; supports CLO2): statement`, and tables for topics, activities, assessments, and gaps.
- **Media plan**: `### M01-V01: Title` for each item, with `- Field: value` lines under it. Producers fill in Stream URL and Captions verified after Kaltura; the video then appears on its page at the next build.
- **Topics**: ordinary Markdown for headings, paragraphs, lists, links, and tables. Every special block is a quote whose bold first line names it: `> **Why this matters**`, `> **Caution: label**`, `> **Expand: label**`, `> **Video: M01-V01 (title)**`, `> **Flashcards: heading**`, `> **Knowledge check**` (mark the right answer `[x]`), `> **Steps: heading**`, and `> **Check yourself**`.
- **Images and infographics**: `![alt text](images/file.svg "Figure 1. Caption")` with a `> **Description**` box right after it. The description renders as a "Full description" accordion under the image, and the build fails if an informative image has none. Image files sit in an `images/` folder beside the topic and are packed into both zips.

An older work folder that still has JSON sources converts once with `python scripts/md_sources.py from-json <work-folder>`.

## What the example shows

The example lives outside the plugin, in [`examples/fspg-101`](../../examples/fspg-101) at the root of this repository, so the plugin itself stays small.

`examples/fspg-101/faculty-content/` is a fictional four-week course (FSPG 101, Food Safety for Small-Scale Produce Growers) written as a live cohort course: a Word syllabus, two slide decks with speaker notes, Markdown lecture notes, a PDF reading, an existing video with captions, and a placeholder image.

`examples/fspg-101/output/` is the full run:

- `inventory-summary.md` and `intake/`: what intake found, including a two-page scanned handout and a phone photo of a sign, both read by OCR.
- `course-map.md` (the editable source) and `docs/course-map.html` (review copy): 5 outcomes, 4 modules, 13 objectives, 16 topics, 232 minutes, full alignment.
- `media-plan.md`, `docs/media-plan.html`, `docs/media-plan.csv`: 10 items, about 38 finished minutes.
- `topics/module-01/` and `topics/module-02/`: the authored topic files in Markdown.
- `build/`: generated pages and the generated JSON (rebuilt every run).
- `dist/`: `fspg-101-module-01-scorm12.zip`, `fspg-101-module-02-scorm12.zip`, and the matching HTML zips.
- `accessibility-report.md` and `axe-results.json`: the gate.
- `run-report.md`: what the orchestrator hands back.

Modules 03 and 04 are mapped and media-planned but not authored, to show partial builds.

## Brightspace import

- **SCORM zip** (licensing outside Purdue, or when SCORM is asked for): Course Admin, Import/Export/Copy Components, Import Course Package. Import one zip per module or week. Each becomes its own module, with no submodule, and one page per topic. Completion is tracked per page: end of page plus 45 seconds. No scores are sent; graded work stays in Brightspace quizzes and assignment folders.
- **HTML zip** (Purdue courses): upload to Manage Files, unzip, then add the pages to the module as topics. Brightspace tracks completion natively.
- Add release conditions in Brightspace after import, not in the package.

## Design and accessibility

- Purdue Black header band with Boilermaker Gold text; Bold Gold `#8E6F3E` h2 on white only; links and focus rings in `#964F37`; cream `#F0EEE6` callouts with black text; `#EBD99F` table headers. `#CC785C` and `#CEB888` are banned and the checker fails any page that uses them.
- Native HTML only: accordions, flashcards, and knowledge checks are `details` and `summary`. No JavaScript in sources. Every control is at least 44 px tall with a 3 px focus ring.
- Every page: `lang`, unique title, one h1, no skipped headings, `main` landmark, captioned tables with header scope, labeled scroll regions, descriptive links, no em-dashes, no sight or click language.
- Videos are linked only after they are streamed with verified captions and a transcript. Until then the page ships without the video and the render report lists it.

## Defaults you may want to change

| Default | Where to change it |
|---|---|
| Package format SCORM 1.2 plus HTML zip. IMS Common Cartridge is not built. | `scripts/build_packages.py` |
| Each unit gets a generated "Overview and objectives" page as item N.0 | `scripts/render_topics.py`, `overview_body` |
| Completion dwell of 45 seconds | `dwell_seconds` in the course map |
| Runs straight through unless `--review` is passed | `commands/build-course.md` |
| A PDF page with fewer than 25 words of text is treated as scanned and sent to OCR | `MIN_PAGE_WORDS` in `scripts/intake.py` |
| OCR text under 0.80 confidence is saved as a picture for the agent to read; the agent rechecks anything under 0.90 | `LOW_CONFIDENCE` in `scripts/ocr.py`, and `agents/content-inventory.md` |
| Work folder is `<faculty-folder>-cp/` | `commands/build-course.md` |
| Topic tree titles are numbered "1.1", "1.2" | `scripts/render_topics.py` |
| External links get "(external site)" appended | `scripts/render_topics.py`, `inline` |
| Fonts: Acumin Pro and United Sans when installed, else system sans | `templates/topic.css` |

## Known limits

- Intake reads .docx, .pptx, .pdf (text and scanned), .md, .txt, .html, .csv, .vtt and .srt, plus photos and scans of handouts (.png, .jpg, .tif and similar). OCR is good on printed text and weak on handwriting; the agent rechecks low-confidence pages against the picture, and anything it cannot make out comes back as a gap. Video and audio are listed but not transcribed.
- The manifest check is structural (root placement, identifiers, references, nesting, files present, wrapper injected). It does not validate against the SCORM XSD files.
- The "taste" and "impeccable" styling skills were not available when this was built. The visual design follows the Purdue brand and accessibility standards directly; if those skills are installed later, point the package-builder at them and revise `templates/topic.css`.
- Automated checks do not replace a keyboard pass in Brightspace, a look in the mobile app, a caption accuracy check, and a screen reader spot check. The report lists them every time.
