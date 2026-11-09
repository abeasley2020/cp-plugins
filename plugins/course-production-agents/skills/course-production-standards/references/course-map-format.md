# course-map.md

The course map is the source of truth, written in Markdown so IDs and faculty can read and edit it in any editor, in Word (open the file), or in a Markdown preview. The overview pages, the Brightspace tree titles, the review docs and the packages are all generated from it. Full working example: `sample/output/course-map.md`.

Write it exactly in this shape. Headings, the `- Field: value` lines and the table columns are what the build reads; anything else is ignored or reported with its line number.

```markdown
# Course map: Food Safety for Small-Scale Produce Growers

- Code: FSPG 101
- College: College of Agriculture
- Audience: Small farm owners and extension volunteers; no science background assumed
- Delivery: Online, self-paced, on-demand
- Format: module
- Total minutes: 232
- Completion time per page (seconds): 45
- Description: One or two sentences on what learners can do at the end.

## Course outcomes

- CLO1 (Understand): Explain how pathogens reach fresh produce.
- CLO2 (Evaluate): Assess agricultural water sources and choose a testing approach.

## Module 01: Why produce safety matters

- Minutes: 54
- Build: yes
- Summary: One sentence learners would recognize.

### Objectives

- 1.1 (Understand; supports CLO1): Explain why fresh produce has no kill step.
- 1.3 (Analyze; supports CLO1, CLO5): Trace the five routes of contamination on your own farm.

### Topics

| ID | Title | Minutes | Objectives | Type |
|---|---|---|---|---|
| t01 | Why produce eaten raw is different | 10 | 1.1 | content |
| t04 | Walk your farm | 15 | 1.3 | activity |

### Activities

| ID | Title | Type | Graded | Points | Where | Objectives |
|---|---|---|---|---|---|---|
| A1 | Walk your farm | guided field observation with model answer | no |  | In the package | 1.3 |

### Assessments

| ID | Title | Type | Graded | Points | Where | Objectives |
|---|---|---|---|---|---|---|
| Q1 | Module 01 quiz | auto-graded quiz, 10 items | yes | 20 | Brightspace Quizzes, outside the package | 1.1, 1.3 |

### Built from

- FSPG101-syllabus.docx, outcomes and Week 1 row

## Conversion notes

- What changed from live delivery, what was lost, and what faculty should confirm.

## Gaps

| Need | Owner | Needed for |
|---|---|---|
| Rubric for the farm plan (40 points) | Faculty with ID | Module 04 activity |
```

Rules for each part:

- **Format** is `module` or `week`. Unit headings match it: `## Module 01: Title` or `## Week 01: Title`, numbered 01 to N in order. A whole-course format is refused.
- **Build**: `yes` means the topics are written and the unit is packaged this run; `no` keeps the unit mapped and planned but unpackaged.
- **Objectives** read `- 1.1 (Bloom level; supports CLO1, CLO2): statement`. Bloom levels: Remember, Understand, Apply, Analyze, Evaluate, Create.
- **Topics**: ID `t01`, `t02` ... within each unit. Type is `content` or `activity` (activities get "Activity:" in the tree). Unit minutes are the topic minutes plus 5 for the generated overview page.
- **Activities** and **Assessments**: Graded is yes or no; Points only for graded work; Where says whether it lives in the package or in a Brightspace tool. Write `None.` under a heading with nothing in it.
- Separate several IDs with commas. Pipes inside a cell are written `\|`.
- No term, year, cohort or due date in any title. No em-dashes anywhere.

Checked by `scripts/validate.py` after the Markdown is read: unique IDs; valid Bloom levels; every objective supports a real outcome; every outcome is supported; every objective is taught by a topic and evidenced by an activity or assessment; minutes add up; units numbered 1 to N.
