# Run report: FSPG 101 sample

Course map, media plan, and two module packages built. Accessibility gate: PASS.

## Built
- Course map: `course-map.md`, the file an ID edits, plus a review copy at `docs/course-map.html`. 5 outcomes, 4 modules, 13 objectives, 16 topics, 232 minutes. Every outcome supported, every objective taught and evidenced.
- Media plan: `media-plan.md`, plus `docs/media-plan.html` and `docs/media-plan.csv` for producers. 10 items, about 38 finished minutes, two field shoots grouped into one trip.
- Packages, one per module:
  - `dist/fspg-101-module-01-scorm12.zip`: 5 pages (overview plus 4 topics), manifest OK
  - `dist/fspg-101-module-02-scorm12.zip`: 6 pages (overview plus 5 topics), manifest OK
  - Matching `-html.zip` for each, for Brightspace Manage Files.
- Topic files: nine Markdown files under `topics/module-01/` and `topics/module-02/`.
- Modules 03 and 04 are mapped and planned but not authored this run.

## Scanned material
- `scanned-handout-sanitation-log.pdf`: 2 scanned pages with no text layer, both read by OCR (confidence 0.91) and checked against the page images. Used for Module 04, topic 4.2.
- `photo-visitor-rules-sign.jpg`: phone photo read by OCR; one run-together line corrected against the photo. Used for Module 03, topic 3.3.
- No page needed a read from the image alone.

## Rebuild after an ID edit
`python <plugin>/scripts/build.py <work>` reads the Markdown again and rebuilds the docs, pages and packages.

## Accessibility
PASS on 13 pages (11 topic and overview pages, course map, media plan). axe-core 4.10.3 found 0 violations. Lowest contrast measured 4.67:1 (Bold Gold h2 on white). axe ran in jsdom, so contrast, target size and reflow were measured from the CSS cascade; rerun with Chromium installed before release. Manual checks owed: keyboard pass in Brightspace, 320 px in the mobile app, caption accuracy, a screen reader spot check.

## Videos left out until produced
M01-V01, M01-V02, M01-V03, M02-V01, M02-V02, M02-V03. Each page ships without the video block until the item has a Kaltura URL and verified captions; then rebuild.

## Live to on-demand conversion
- The Week 3 Zoom discussion becomes a self-check with a model answer (Module 03). Lost: peer feedback on each station.
- Peer review of the final plan becomes a rubric and worked example. Faculty to decide whether instructor review is still offered.

## Faculty gaps
- Real farm walk diagram (faculty).
- Review of the water rule and manure interval references (faculty).
- Water source assessment worksheet template (faculty).
- Farm plan rubric (faculty with ID).
- Quiz item banks (faculty with ID).
- A blank copy of the harvest sanitation log; the scanned handout explains it but the form is not in the folder (faculty).

## Style note
The "taste" and "impeccable" skills were not available in this environment. Styling follows the Purdue standard in `templates/topic.css`.
