# Design system

Every CP lesson looks and feels like a well-made Rise 360 course, built in code. The stylesheet is `assets/cp-lesson.css` and the behavior is `assets/cp-lesson.js`. Pages use nothing else: no inline styles, no outside fonts, scripts or images (D1, D7).

## The frame

- A sidebar outline lists the module's lessons with "Lesson n of N" and a progress bar. It stacks above the lesson on narrow screens. In a SCORM package the outline is plain text, because the LMS moves between lessons.
- One lesson per page. The header carries the module name, the lesson title as the only `h1` and the minutes.
- One reading column of about 34rem. Figures and comparisons can go wide (52rem).
- Blocks are flat and full width. No cards, rounded corners, drop shadows or gradients. A cream band that runs edge to edge sets apart a problem, case, caution, scenario or practice block, and nothing else.
- Continue dividers (`+++`) mark one or two natural pauses per lesson.

## Tokens

| Token | Value | Use |
|---|---|---|
| Black | #000000 | Headings, links, buttons on hover |
| Ink | #1F1F1F | Body text |
| Steel | #555960 | Secondary text, captions |
| Boilermaker Gold | #CFB991 | Rules, bars, buttons, markers. Never text. |
| Aged gold | #8E6F3E | Borders and focus marks only |
| Dust | #EBD99F | Pale fill behind black text |
| Cream | #F7F5F0 | Set-apart bands |
| Coral text | #964F37 | Small coral text (block labels) on cream or white |
| Coral line | #CC785C | Borders only. Never text. |

Type is Source Sans 3, self-hosted from `assets/fonts/` when the font file is added there (it is not shipped yet, so pages use the system sans fallback), never loaded from a font service. Body text is 18 px and nothing is smaller than 16 px. Focus rings are 3 px. Targets are at least 24 px, and 44 px for disclosures, buttons and the outline.

## Every component works without scripts

With scripts off, in print and in the Brightspace mobile app, every panel shows, every answer sits in a "Show the answer" disclosure and every step of a process is listed. `cp-lesson.js` adds the accordion and tab keyboard patterns, the step-by-step process, answer checking and SCORM completion. It stores nothing.

## Ban list (D9)

A page fails if it has any of these:

- Drop shadows, rounded cards or gradient fills on content blocks
- Every section in a box
- Stacked identical labeled callouts, or more than four labeled callouts on one page
- More than one of the same interaction kind on a page, other than knowledge checks
- The same section skeleton on every lesson in a module
- Placeholder graphics in anything that reaches Gate 2
- Generic box-and-arrow diagrams, decorative icons, emoji, stock photos or photorealistic AI images
- Centered body text
- Stock AI phrasing, for example "it is important to note", "in this lesson we will", "delve", "key takeaways", "plays a crucial role" (the full list is `BANNED_PHRASES` in `scripts/cpb/checks.py`)
- Parallel triplets and headings that all follow one sentence pattern (the design reviewer judges these)

## Art direction per course

At Gate 1 the ID and the lead producer write a one-page art direction brief for the course: the mood in a sentence, the photo shot list, the illustration style, one signature visual and two reference pages. A designer then builds one reference lesson by hand to that brief. The lesson writer builds to match it and the design reviewer compares every page against it. Keep the brief at `blueprint/art-direction.md` and the reference lesson at `blueprint/reference-lesson/`.
