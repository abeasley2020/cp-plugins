# Topic files

One Markdown file per topic: `topics/module-01/t01-short-name.md` (or `topics/week-01/...` for weekly courses). The file name starts with the topic ID from the course map; the rest of the name becomes the page's file name in the package. Full examples: `sample/output/topics/`.

The build adds everything around the content: the Purdue band, the meta line ("Module 01, Topic 2 of 4. Estimated time: 12 minutes."), the "What this topic is for" section, the "Next topic" line and the sources footer. Write only the content.

## The basics

```markdown
# Why produce eaten raw is different

Purpose: Explain why produce eaten raw carries more risk than cooked food, so every practice in this course has a reason behind it.

## No kill step between the field and the plate

A paragraph. Blank lines separate paragraphs. **Bold**, *italic* and [descriptive link text](https://example.org) work as usual.

### A smaller heading

- A bulleted list
- Another item

1. A numbered list
2. Another item

## Sources

- Instructor slides, Week 1, slide 1 and speaker notes.
- Example rule summary (verified 2026-11-06)
```

- The `#` title must match the topic title in the course map.
- The `Purpose:` line comes right under the title.
- Use `##` and `###` only, and never skip from `##` to a lower level and back without a `##`.
- `## Sources` is always last. Add `(verified YYYY-MM-DD)` to anything that can go stale, such as a regulation or a statistic.

## Boxes

Every special block is a quote block (lines that start with `>`) whose first line is a bold label. The label says what kind of box it is.

| You write | Learners get |
|---|---|
| `> **Why this matters**` then the text | Cream callout with that label. Any label that is not one of the words below makes a callout. |
| `> **Caution: Raw manure is not compost**` | Cream box with a coral rule, for a risk or a rule change |
| `> **Check yourself**` | The reflective close at the end of the topic |
| `> **Expand: Optional depth: why wash water can make things worse**` | A disclosure the learner can open. Two expand boxes separated by one blank line become one group. Optional depth only; nothing required may hide inside. |
| `> **Video: M01-V01 (Why one outbreak can close a small farm)**` | The streamed video and its transcript link, once the media plan has a Stream URL and Captions verified is yes. Text under the label becomes a note under the video. |
| `> **Steps: Set up a handwashing station**` with a numbered list | A numbered procedure with its own heading |
| `> **Flashcards: Retrieval practice**` with `**Q:**` and `**A:**` lines | A retrieval practice deck; each card opens to show the answer |
| `> **Knowledge check**` with numbered questions | Practice questions with the answer behind a disclosure |

Flashcards:

```markdown
> **Flashcards: Retrieval practice**
>
> **Q:** What is a kill step?
>
> **A:** A treatment, such as cooking, that destroys harmful microbes before food is eaten.
```

Knowledge check: mark the right answer `[x]` and the others `[ ]`, and give one `Why:` line that also says why the others fall short.

```markdown
> **Knowledge check**
>
> 1. A neighbor gives you compost with no temperature records. How should you treat it?
>    - [ ] As treated compost, ready to use
>    - [x] As raw manure, with the same intervals and care
>    - [ ] As safe for leafy greens if you water it in
>
>    Why: Without documented time and temperature you cannot show the pathogens were killed.
```

## Tables and images

Every table has a caption line right above it (a blank line between the two is fine). The first column is read as row headers; write `Table (no row headers): caption` when it should not be.

```markdown
Table: Common water sources and their risk

| Source | Risk | Why |
|---|---|---|
| Municipal | Lowest | Treated and tested by the utility |
```

Images give alt text in the brackets and an optional caption in quotes. Every informative image (an infographic, diagram, chart or photo that carries content) needs a `> **Description**` box right after it, or the check fails. The description renders as a "Full description" accordion directly under the image. Write it in depth: everything the image shows, in reading order, including every label, number and relationship, so a learner who cannot see the image gets the same content. It can run several paragraphs. A one-paragraph `Description:` line still works. Use empty brackets `![](...)` only for decorative images, which need no description. Never use a picture of text.

```markdown
![Farm layout with the well uphill of the field](images/farm-layout.png "The sample farm")

> **Description**
> The layout is a plan view of a small farm. The well sits at the top, uphill of the field.
>
> The compost pile is downhill, near the road, so runoff flows away from the well. The packing shed is beside the parking area.
```

## Rules

- No em-dashes, no exclamation points in body copy, no "click here", "see below" or "as shown above". Name the section instead.
- Completion never depends on opening an Expand box.
- Nothing that only makes sense visually.
- The build reports any problem with the file name and line number. Fix it in the Markdown and build again; never edit the generated HTML.
