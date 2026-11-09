# Accessibility review

Status: **PASS**
Standard: WCAG 2.2 AA, Purdue accessibility standard (strict), Brightspace topic rules
Generated: 2026-11-09
Pages checked: 13

Automated engine: axe-core 4.10.3 via chromium (playwright), rule tags wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa.

## Summary

- Blockers from house and structural checks: 0
- axe-core violations: 0
- Warnings: 0
- Distinct text and background pairs measured: 10, lowest ratio 4.67:1

## Pages

- **PASS** build/content/module-01-why-produce-safety-matters/activity-04-walk-your-farm.html. axe: 21 passed rules, 0 violations, 0 need a browser
- **PASS** build/content/module-01-why-produce-safety-matters/topic-00-overview.html. axe: 18 passed rules, 0 violations, 0 need a browser
- **PASS** build/content/module-01-why-produce-safety-matters/topic-01-no-kill-step.html. axe: 11 passed rules, 0 violations, 0 need a browser
- **PASS** build/content/module-01-why-produce-safety-matters/topic-02-pathogens.html. axe: 21 passed rules, 0 violations, 0 need a browser
- **PASS** build/content/module-01-why-produce-safety-matters/topic-03-five-routes.html. axe: 11 passed rules, 0 violations, 0 need a browser
- **PASS** build/content/module-02-water-soil-amendments-and-animals/activity-05-water-assessment.html. axe: 21 passed rules, 0 violations, 0 need a browser
- **PASS** build/content/module-02-water-soil-amendments-and-animals/topic-00-overview.html. axe: 18 passed rules, 0 violations, 0 need a browser
- **PASS** build/content/module-02-water-soil-amendments-and-animals/topic-01-water-sources.html. axe: 21 passed rules, 0 violations, 0 need a browser
- **PASS** build/content/module-02-water-soil-amendments-and-animals/topic-02-water-testing.html. axe: 11 passed rules, 0 violations, 0 need a browser
- **PASS** build/content/module-02-water-soil-amendments-and-animals/topic-03-manure-compost.html. axe: 11 passed rules, 0 violations, 0 need a browser
- **PASS** build/content/module-02-water-soil-amendments-and-animals/topic-04-animals.html. axe: 8 passed rules, 0 violations, 0 need a browser
- **PASS** docs/course-map.html. axe: 18 passed rules, 0 violations, 0 need a browser
- **PASS** docs/media-plan.html. axe: 18 passed rules, 0 violations, 0 need a browser

## Contrast pairs measured (SC 1.4.3)

| Text | Background | State | Ratio | Needed | Example element | Result |
|---|---|---|---|---|---|---|
| #8E6F3E | #FFFFFF | normal | 4.67:1 | 3.0:1 | h2 | Pass |
| #555960 | #FFFFFF | normal | 7.04:1 | 4.5:1 | p.meta | Pass |
| #CFB991 | #000000 | normal | 11.00:1 | 4.5:1 | header.band | Pass |
| #000000 | #EBD99F | normal | 14.96:1 | 4.5:1 | th | Pass |
| #000000 | #EBD99F | hover | 14.96:1 | 4.5:1 | summary | Pass |
| #000000 | #F0EEE6 | normal | 18.08:1 | 4.5:1 | th | Pass |
| #000000 | #F0EEE6 | hover | 18.08:1 | 4.5:1 | summary | Pass |
| #FFFFFF | #000000 | normal | 21.00:1 | 4.5:1 | span | Pass |
| #000000 | #FFFFFF | normal | 21.00:1 | 3.0:1 | h1 | Pass |
| #000000 | #FFFFFF | normal | 21.00:1 | 4.5:1 | p.purpose | Pass |

## Manual checks still owed before release

- Tab through three pages per package in Brightspace and confirm the focus ring is visible on every summary and link.
- Open one page per package at 320 px in the Brightspace mobile app.
- Confirm captions are accurate (not only present) on every linked video, and transcripts match the final edit.
- Screen reader spot check (NVDA or VoiceOver) on one knowledge check and one table.
