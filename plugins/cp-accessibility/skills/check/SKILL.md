---
name: check
description: Check one or more HTML files (or a folder of them) for WCAG 2.2 AA problems and report each finding with its success criterion, level, line number, and a fix. Use for Brightspace topic pages, SCORM content, and any HTML a learner will see.
argument-hint: <file-or-folder> [more paths]
allowed-tools: Bash(node "${CLAUDE_PLUGIN_ROOT}/scripts/check.mjs" *), Read, Glob
---

# cp-accessibility: check

You are checking HTML course content for accessibility problems. Report findings; do not edit files unless the user asks for fixes afterward.

## Steps

1. Decide what to check. If `$ARGUMENTS` is empty, look for `.html` and `.htm` files in the current project with Glob and ask which ones to check. Never guess a file.
2. Run the checker. It needs Node.js 20 or later and no other dependencies:

   ```
   node "${CLAUDE_PLUGIN_ROOT}/scripts/check.mjs" $ARGUMENTS
   ```

   Exit code 0 means no findings, 1 means findings were reported, 2 means a path was missing or unreadable.
3. Present the report. Keep the table the script prints: one row per finding with the line, the WCAG criterion number and name, the level, the problem, and the fix. Group by file. Below the table, say in one or two sentences what the biggest problems are and which to fix first (Level A before Level AA).
4. Say what the static check cannot see. Always include this note: color contrast, reflow at 320 CSS pixels, focus visibility, and reading order need a browser-based check and a human review.
5. Offer to apply the fixes. If the user says yes, edit the HTML and run the checker again to confirm the findings are gone.

## If Node.js is not available

Tell the user the script could not run, then review each file yourself with Read and report the same way, using this rule list:

| Rule | WCAG 2.2 | Level | What to look for |
|---|---|---|---|
| img-alt | 1.1.1 Non-text Content | A | `<img>` with no `alt` attribute |
| link-text-generic | 2.4.4 Link Purpose (In Context) | A | Link text such as "click here", "here", "read more", "more", "learn more", "link" |
| link-empty | 2.4.4 Link Purpose (In Context) | A | A link with no text, aria-label, or image alt |
| html-lang | 3.1.1 Language of Page | A | `<html>` without `lang` |
| page-title | 2.4.2 Page Titled | A | `<head>` without a non-empty `<title>` |
| heading-skip | 1.3.1 Info and Relationships | A | Heading levels that skip, such as h2 to h4 |
| heading-empty | 2.4.6 Headings and Labels | AA | A heading with no text |
| iframe-title | 4.1.2 Name, Role, Value | A | `<iframe>` without `title` |
| input-label | 3.3.2 Labels or Instructions | A | A form control with no label, aria-label, or aria-labelledby |
| tabindex-positive | 2.4.3 Focus Order | A | `tabindex` greater than 0 |
| table-headers | 1.3.1 Info and Relationships | A | A data table with no `<th>` |
| video-captions | 1.2.2 Captions (Prerecorded) | A | `<video>` without a captions track |
| media-autoplay | 1.4.2 Audio Control | A | `<audio>` or `<video>` with `autoplay` |

## Configuration

The checker reads an optional team config at `%USERPROFILE%\.cp-plugins\config.json` (the user's home folder on macOS and Linux). The `accessibility` section can disable rules or add generic link phrases. The repository README documents the format. If the user asks why a rule did not fire, check that file first.
