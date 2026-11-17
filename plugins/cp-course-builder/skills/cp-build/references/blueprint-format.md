# Blueprint format

The course mapper writes `blueprint/blueprint.json` and a readable `blueprint/blueprint.md` beside it. The first line of `blueprint.md` is `status: DRAFT` or `status: APPROVED`. No lesson is written until it reads `status: APPROVED` (Gate 1).

```json
{
  "course": "FSPG 101 Food safety principles",
  "prefix": "fspg",
  "credit_hours": 3,
  "profile": "agriculture-food-science",
  "outcomes": [
    {"id": "CO1", "text": "evaluate a plant's hygiene controls against its hazard analysis.", "bloom": "evaluate"}
  ],
  "objectives": [
    {"id": "o3.1", "module": 3, "text": "decide when a line worker must wash their hands, given their tasks.", "bloom": "apply", "supports": ["CO1"]}
  ],
  "lessons": [
    {"module": 3, "file": "01-gloves-and-handwashing.md", "title": "When to wash and why gloves are not enough",
     "objectives": ["o3.1", "o3.2"], "sources": ["week3-notes.md slides 4 to 8"], "minutes": 12}
  ],
  "assessments": [
    {"id": "A3", "module": 3, "title": "Line hygiene audit", "kind": "authentic task", "graded": true,
     "objectives": ["o3.1", "o3.2"], "minutes": 90}
  ]
}
```

Rules the script checks (`cpbuild.py blueprint blueprint/blueprint.json`):

- R1: every outcome and objective opens with an observable verb and names its Bloom level. No "understand", "know" or "learn about" as the verb.
- R2: every objective supports at least one outcome, and every outcome is supported.
- R3: every objective is taught by a lesson and measured by a graded assessment. Lessons carry the ungraded practice.
- R8: planned learner minutes against the credit hours (45 learner hours per credit hour by default; record a different college expectation in `decisions.md`).

Lesson boundaries come from the outcomes and objectives, never from deck boundaries. There is no target number of lessons per module.
