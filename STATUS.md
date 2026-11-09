# STATUS

Tracker Project: cp-plugins

## Current state

- Two plugins in the marketplace layout: `cp-accessibility` 0.1.0 and `course-production-agents` 0.2.2, with the fictional FSPG 101 example in `examples/fspg-101`.
- Repository CI (marketplace check, content scan, 38 unit tests) passes locally and on GitHub Actions (Ubuntu and Windows). Both plugins pass `claude plugin validate`.
- The team installs from GitHub: `/plugin marketplace add abeasley2020/cp-plugins`, then `/plugin install course-production-agents@cp-plugins`.
- Claude plugin directory: the submission for course-production-agents is refused. Accounts that are not a Verified organization may only submit Markdown, text, JSON, YAML and images, and the plugin's build is Python and Node scripts with npm dependencies.

## Next steps

1. Send the first teammate the macOS setup steps and confirm the GitHub install works on their machine.
2. Decide whether to pursue organization verification for a directory listing, or withdraw the submission and keep GitHub as the only channel.
3. Retire the older local copy of the plugin outside this repository and install from this marketplace instead.

## Closeout 2026-11-09
- Completed: added course-production-agents to the marketplace (merged with the local marketplace work); Windows-safe Python launcher; one module per week in SCORM packages; full-width pages; infographic support with required "Full description" accordions and packaged images; directory review fixes (no pre-approved tools, no download-and-run text, listing icon, privacy policy); version 0.2.2.
- In progress: nothing uncommitted.
- Next action: send the first teammate the macOS setup steps and confirm the GitHub install works.
- Blocker: directory listing needs a Verified organization (does not block team use through GitHub).
