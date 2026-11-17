# Review format

Every reviewer, script or agent, reports results in one shape, so `cpbuild.py score` can merge them into one scorecard.

```json
{
  "reviewer": "cp-rigor-reviewer",
  "module": "module-03",
  "results": [
    {
      "criterion": "R7",
      "target": "fspg-m03-l01",
      "result": "fail",
      "evidence": "The second option of the first check says only 'Not correct.' and gives no reason.",
      "fix": "Say why handwashing after gloves does not reset them.",
      "owner": "cp-lesson-writer"
    }
  ]
}
```

- `result` is `pass`, `fail`, `warn` or `na`. A `fail` blocks the module. Use `warn` for something the ID should see that does not break the criterion.
- `evidence` quotes or points to the exact place (lesson id, section heading, block line). A result with no evidence does not count.
- `fix` says what to change in the Markdown source, never in the HTML.
- `owner` is the agent that owns the source: `cp-lesson-writer` for lesson content, `cp-course-mapper` for objectives, alignment, minutes and lesson boundaries.

The review command saves each reviewer's JSON to `modules/module-NN/reviews/<reviewer>.json`. Reviewers never edit files.

## Fix rounds

`/cp-course-builder:review NN` runs the script checks and the three reviewers, then routes each failure to its owner. The owner fixes the source and the review runs again. After three rounds with a failure still open, the module stops and the ID decides, and the decision goes in `decisions.md`.

## Build log (P3)

`modules/module-NN/build-log.csv` has the columns `date,step,who,id_hours,producer_hours,ai_assisted,review_round`. Agents add a row for each step they run with zero hours; the ID fills in the hours.
