# CP Course Quality Standard v1.0

This file is generated from `standard/cp-quality-standard.json`, which is the only place the standard lives. Edit the JSON, then run `sh scripts/run-python.sh scripts/cpbuild.py standard` to rebuild this page.

Floor: QM Higher Education Rubric, 7th edition. Every criterion is a yes or no. One fail blocks the module.

## Precedence when criteria conflict

1. Accessibility wins. Captions, transcripts and long descriptions always ship, even where the redundancy principle would cut them.
2. Accuracy beats engagement. If faculty material has no real case, the lesson carries a gap marker for faculty. An agent never invents a case to satisfy problem first.
3. Guidance fades with expertise. Novices get complete worked examples; experienced professionals start at faded examples to avoid the expertise reversal effect.
4. Choice lives in depth and context, not in the core path. Required content is never hidden in an accordion or tab.
5. Every interaction must make the learner retrieve, decide or compare. Counts are floors only where the content supports them, and a skipped interaction is recorded with its reason.
6. Segment without fragmenting. One idea per section, but a lesson keeps one conceptual thread of 600 to 900 words rather than splitting below it.
7. Faculty preference yields on accessibility and alignment only. Other design choices are negotiated and recorded in the decisions log.

## Rigor

| ID | Criterion | Checked by | Fix owner | Stage |
|---|---|---|---|---|
| R1 | Every course outcome and module objective uses an observable verb and names its Bloom level. No "understand," "know" or "learn about." | script, cp-rigor-reviewer | cp-course-mapper | blueprint |
| R2 | Every objective supports at least one course outcome, and every outcome is supported. | script | cp-course-mapper | blueprint |
| R3 | Every objective is taught by a lesson, practiced by an ungraded item and measured by a graded assessment. | script | cp-course-mapper | blueprint |
| R4 | Assessment items match or exceed the objective's Bloom level. An apply or analyze objective gets at least one apply or analyze item. | script, cp-rigor-reviewer | cp-lesson-writer | review |
| R5 | Every claim traces to a faculty source (file and slide or page). No invented facts. Claims that can go stale carry a verified date and sit in the gap report. | script, cp-rigor-reviewer, Faculty at Gate 1 | cp-lesson-writer | review |
| R6 | Each module has one graded, authentic task built on a realistic decision from the field, with a rubric tied to the objectives. | cp-rigor-reviewer, ID | cp-course-mapper | review |
| R7 | Feedback on every item explains why the right answer is right and why each distractor falls short. | script, cp-rigor-reviewer | cp-lesson-writer | review |
| R8 | Learner minutes per lesson and module fall inside targets, and the course total matches the credit-hour expectation in the syllabus. | script | cp-course-mapper | review |

## Design and accessibility

| ID | Criterion | Checked by | Fix owner | Stage |
|---|---|---|---|---|
| D1 | Pages use only the shared stylesheet and component library. No inline styles. | script | cp-lesson-writer | review |
| D2 | Purdue tokens only. Small coral text on cream is #964F37. #CC785C is for borders only. Gold is never text. | script | cp-lesson-writer | review |
| D3 | WCAG 2.2 AA strict: zero axe violations, contrast measured in a real browser, 3 px focus ring, 24 px minimum targets (44 px for disclosures), reflow at 320 px, Brightspace limits on alt text and heading length. | script, cp-design-reviewer | cp-lesson-writer | review |
| D4 | Layout rhythm: no more than five paragraphs in a row without a figure, callout or interaction, at least one two-column block where the content supports it, reading width near 68 characters. | script | cp-lesson-writer | review |
| D5 | Visual review: screenshots at 1280, 768 and 320 px are scored against the course's art direction brief and hand-built reference lesson for hierarchy, spacing, imagery and a specific, not generic, look. | cp-design-reviewer, ID at Gate 2 | cp-lesson-writer | review |
| D6 | Images explain something. No photorealistic AI images, no decorative stock. SVG diagrams drawn from source, licensed photos credited, file size budgets met. | script, cp-design-reviewer | cp-lesson-writer | review |
| D7 | Every page works with scripts off, in the Brightspace mobile app and in print, with no outside fonts or CDNs. | script, ID spot check | cp-lesson-writer | review |
| D8 | House style: no em-dashes, no exclamation points in body copy, no "click here" or "see below," sentence-case headings. | script | cp-lesson-writer | review |
| D9 | Does not look AI-made: nothing from the ban list, lesson skeletons vary across a module, a real photo or course-style diagram in place of every placeholder, and pages pass the monthly look test. | script, cp-design-reviewer, Monthly look test panel | cp-lesson-writer | review |

## Multimedia and learning science

| ID | Criterion | Checked by | Fix owner | Stage |
|---|---|---|---|---|
| M1 | Coherence: every figure is referenced in the text by what it shows, and nothing decorative stays. | cp-learning-science-reviewer | cp-lesson-writer | review |
| M2 | Signaling: a lead-in sentence before each figure, headings that state the idea, key terms bolded once at first use. | script, cp-learning-science-reviewer | cp-lesson-writer | review |
| M3 | Spatial contiguity: labels sit on the figure and the long description sits directly under it. | script | cp-lesson-writer | review |
| M4 | Video scripts use two columns (visual and narration) so narration and visuals line up, with on-screen text kept to labels. | cp-learning-science-reviewer, Lead producer | cp-lesson-writer | review |
| M5 | Segmenting: videos target 6 minutes and never exceed 10. Any process over four steps is a step sequence. | script | cp-lesson-writer | review |
| M6 | Pre-training: terms are defined before use, and a term from an earlier lesson is restated with a link. | cp-learning-science-reviewer | cp-lesson-writer | review |
| M7 | Retrieval: every lesson ends with 3 to 5 items, at least one free recall, every objective covered. | script | cp-lesson-writer | review |
| M8 | Spacing and interleaving: one item from an earlier module in each set after Module 1, cumulative quizzes, mixed item types and contexts. | script | cp-lesson-writer | review |
| M9 | Worked examples fade with course position: complete before the midpoint, faded after, problem only in the final third. | cp-learning-science-reviewer | cp-lesson-writer | review |

## Andragogy

| ID | Criterion | Checked by | Fix owner | Stage |
|---|---|---|---|---|
| A1 | Problem before principle: each lesson opens with a real decision, defect or case from the field. | script, cp-learning-science-reviewer | cp-lesson-writer | review |
| A2 | Within the first 150 words, the lesson says who makes this decision and what it costs to get it wrong. | script, cp-learning-science-reviewer | cp-lesson-writer | review |
| A3 | Each module landing page asks learners to connect the module to their own work. | script, cp-learning-science-reviewer | cp-course-mapper | review |
| A4 | Optional depth is labeled Optional and is never required for practice, labs or quizzes. | script | cp-lesson-writer | review |
| A5 | Voice of a colleague: no quiz-show tone, no "in this lesson we will cover." | cp-learning-science-reviewer | cp-lesson-writer | review |
| A6 | Each module ends with a transfer task that applies the work to the learner's own setting. | cp-rigor-reviewer | cp-course-mapper | review |

## Process

| ID | Criterion | Checked by | Fix owner | Stage |
|---|---|---|---|---|
| P1 | AI drafts are marked as drafts until an ID finalizes them, and the finalizing ID is recorded. | script | cp-lesson-writer | package |
| P2 | Faculty-voiced text (narration, welcome messages) is approved by the faculty member before launch. | script, Faculty at Gate 3 | cp-lesson-writer | package |
| P3 | Each build logs ID hours, producer hours, AI-assisted steps and review rounds. | script, ID | cp-course-mapper | review |
