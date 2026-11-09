# cp-accessibility

Static WCAG 2.2 AA checks for HTML course content, packaged as a Claude Code plugin.

## What it does

`/cp-accessibility:check <file-or-folder>` runs a zero-dependency Node.js script over your HTML and reports every finding with:

- the line number
- the WCAG 2.2 success criterion number and name
- the conformance level (A or AA)
- a one-line fix

Claude then summarizes the report, tells you what the static check cannot see, and offers to apply the fixes.

## Install

From a Claude Code session:

```
/plugin marketplace add <owner>/cp-plugins
/plugin install cp-accessibility@cp-plugins
```

Replace `<owner>` with the GitHub account that hosts this repository. The repository README has the full install notes, including a local folder install for testing.

## Usage

```
/cp-accessibility:check topics/week-01.html
/cp-accessibility:check build/content
```

Try it on the shipped sample, which has a missing alt attribute and a "click here" link:

```
/cp-accessibility:check plugins/cp-accessibility/samples/needs-work.html
```

You can also run the script directly, outside Claude Code:

```
node plugins/cp-accessibility/scripts/check.mjs path/to/page.html
node plugins/cp-accessibility/scripts/check.mjs path/to/folder --json
```

Exit codes: 0 no findings, 1 findings reported, 2 missing or unreadable path.

## Rules

| Rule | WCAG 2.2 | Level |
|---|---|---|
| img-alt | 1.1.1 Non-text Content | A |
| link-text-generic | 2.4.4 Link Purpose (In Context) | A |
| link-empty | 2.4.4 Link Purpose (In Context) | A |
| html-lang | 3.1.1 Language of Page | A |
| page-title | 2.4.2 Page Titled | A |
| heading-skip | 1.3.1 Info and Relationships | A |
| heading-empty | 2.4.6 Headings and Labels | AA |
| iframe-title | 4.1.2 Name, Role, Value | A |
| input-label | 3.3.2 Labels or Instructions | A |
| tabindex-positive | 2.4.3 Focus Order | A |
| table-headers | 1.3.1 Info and Relationships | A |
| video-captions | 1.2.2 Captions (Prerecorded) | A |
| media-autoplay | 1.4.2 Audio Control | A |

Document-level rules (`html-lang`, `page-title`) only run when the file contains an `<html>` or `<head>` element, so Brightspace HTML fragments are not penalized for omitting them.

## Limits

These checks read markup only. They do not catch color contrast, reflow, focus visibility, reading order, or anything that depends on CSS or JavaScript at runtime. Pair this plugin with a browser-based tool such as axe and a human review before you call a page done.

## Configuration

The script reads an optional file at `%USERPROFILE%\.cp-plugins\config.json` (your home folder on macOS and Linux). Nothing in this repository is read as configuration.

```json
{
  "accessibility": {
    "disabledRules": [],
    "genericLinkText": ["tap this"],
    "format": "markdown"
  }
}
```

- `disabledRules`: rule ids from the table above to skip.
- `genericLinkText`: extra link phrases to treat as non-descriptive.
- `format`: `markdown` (default) or `json`.

A missing or malformed file is ignored and the defaults apply.

## Tests

```
node --test "plugins/cp-accessibility/tests/*.test.mjs"
```
