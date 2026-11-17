# Lesson format

A lesson is one Markdown file in `modules/module-NN/lessons/`, named `NN-short-slug.md` so the files sort in reading order. The lesson writer writes only this file. `cpbuild.py` renders it to HTML; nobody edits the HTML.

The full worked example is `examples/fspg-101/modules/module-03/lessons/01-gloves-and-handwashing.md`.

## Front matter

```yaml
---
title: When to wash and why gloves are not enough
minutes: 10
objectives:
  - id: o3.1
    text: decide when a line worker must wash their hands, given a description of their tasks.
    bloom: apply
sources:
  - week3-notes.md slides 4 to 8
draft: ai
---
```

| Key | Required | Meaning |
|---|---|---|
| `title` | yes | Sentence case, no numbering, matches the blueprint. Becomes the page's only `h1`. |
| `objectives` | yes | One to three, ids from the blueprint. `text` completes "By the end of this lesson you will be able to". `bloom` is remember, understand, apply, analyze, evaluate or create. |
| `sources` | yes | One line per faculty file, with slides or pages. R5 fails without it. |
| `minutes` | no | The writer's estimate; the script compares it with its own. |
| `draft` | yes | `ai` until an ID finalizes it. `final` also needs `finalized_by:` (P1). |
| `finalized_by` | with `final` | The finalizing ID's initials. |
| `faculty_voiced` | no | `true` when the page carries faculty-voiced text. Videos count automatically. |
| `faculty_approval` | no | The date faculty approved faculty-voiced text (P2). |
| `id`, `file` | no | Defaults: `<prefix>-mNN-lNN` and `<prefix>-moduleNN-<title-slug>.html`. |
| `header_image`, `header_alt` | no | A photo for the lesson header. Only a real course photo, never stock. |

## Markdown

`##` starts a section and `###` a subsection. Paragraphs, `-` lists, `1.` lists and pipe tables with a `Table: caption` line above them work as usual. Use `**bold**` once for a key term at first use, `*em*` sparingly and `[descriptive text](file.pdf)` for links. A numbered list of more than four steps fails M5; use `:::process`.

`+++` on its own line is a continue divider. It renders as "Continue to <next heading>" and marks a natural pause, the way Rise uses its continue block. Use one or two per lesson, never between every section.

`[GAP: what is missing]` marks anything the source does not supply. It renders visibly so faculty see it, and R5 counts it. Never fill a gap in.

## Blocks

A block opens with `:::type`, optional `key=value` arguments and an optional title, and closes with `:::` on its own line. Blocks do not nest.

### Teaching blocks

| Block | Use it for | Content |
|---|---|---|
| `:::problem Title` | The opening decision, defect or case from the field (A1). Cream band. | Paragraphs. Name who decides and the cost of getting it wrong in the first 150 words (A2). `label="..."` changes the "From the field" label. |
| `:::case Title` | A longer case with facts. Cream band. | Paragraphs, then `Facts:` and `- Name: value` lines. |
| `:::term Word` | Defining a term before it is used (M6). | One or two sentences. |
| `:::caution Title` | A safety or regulatory point the learner must not miss. Cream band. | One short paragraph. Use at most one per section. |
| `:::statement` | One sentence worth stopping on. Large type, gold rule. | One sentence. |
| `:::quote Name, role` | A faculty or practitioner quote, with permission. | The quote. |
| `:::figure` | Every image. | `src:`, `alt:` (125 characters or fewer), `caption:`, `credit:`, `kind:` (photo, diagram, graph, chart, structure, framework, map, process, table, flow). Optional `Text:` section puts the figure beside text in two columns. `Description:` is required for every kind except photo (M3) and renders directly under the figure. `layout: full` makes it wide. |
| `:::compare Title` | Two or three things side by side. Two columns on wide screens. | One `###` heading per column. |
| `:::worked Title` | A worked example. `faded=true`, or a title that starts with "Faded", for a faded one (M9). | `1. step Why: reason` lines. A step that starts with `?` is the learner's turn, followed by `Answer:`. |
| `:::video Title id=V03 minutes=5` | A planned video (M4, M5). | The two-column script: visual and narration. Ships as the transcript. |
| `:::depth Optional: title` | Optional depth. Title must start with "Optional" (A4). Never needed for any item or lab. | Anything. |
| `:::practice Title` | A practice task in the learner's own setting (A6). Cream band. | Instructions. |
| `:::synthesis Title` | A short close that connects the ideas, never a repeat of the lesson. | One or two paragraphs. |
| `:::reflect Title` | A prompt to connect the idea to the learner's work, with a private notes box. | The prompt. |

### Interactions

Every interaction must make the learner retrieve, decide or compare. At most one of each kind per lesson, except checks (D9). Required content never lives only inside an accordion or tab.

| Block | Content |
|---|---|
| `:::accordion Title` | One `###` heading per panel. For optional or reference detail only. |
| `:::tabs Title` | One `###` heading per tab. For parallel views of one idea. |
| `:::flashcards Title` | `Q:` and `A:` lines. The learner answers before turning. |
| `:::process Title` | One `###` heading per step. Steps show one at a time with Previous and Next. |
| `:::labeled-graphic Title` | `src:`, `alt:`, `caption:`, `credit:`, then `1. (x%, y%) **Label**: text` per marker, then `Description:`. Markers sit on the figure; positions round to 5 percent. |

### Items (retrieval and practice)

Every item takes `objective=` (an objective id), `bloom=`, `source="file and slide"` and, after Module 1, at least one item per lesson takes `spaced_from=mNN` (M8). The script puts every item in `build/item-bank.json`.

| Block | Content |
|---|---|
| `:::check` | The stem, then options as `- [x] right` or `- [ ] wrong`, each followed by an indented `Why:` line that explains why it is right or why it falls short (R7). Two or more `[x]` make it choose-all-that-apply. |
| `:::scenario` | The situation, then options with indented `Result:` lines that say what happens next. The best choice is `[x]`. |
| `:::recall Title` | The prompt, then `Model answer:` and `Criteria:` lines. The learner writes before revealing. |
| `:::sorting Title` | The instruction, `categories: A \| B \| C`, then `- item => Category` lines, each with an indented `Why:` line. |

## Shape of a lesson

There is no fixed skeleton, and lessons in one module must not share one (D9). Every lesson does three things:

1. Opens with a `:::problem` or `:::case` from the source, or a `[GAP:]` inside the problem block when the source has none (A1).
2. Teaches in sections of one idea each, 600 to 900 words of core explanation in all, with no more than five paragraphs in a row before a figure, callout or interaction, and at least one two-column block (D4).
3. Ends with `## Check your understanding` and 3 to 5 items, at least one `:::recall`, every objective covered (M7). A short `:::synthesis` may follow.
