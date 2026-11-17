# Privacy policy: cp-course-builder

Last updated: November 17, 2026

cp-course-builder is a Claude Code plugin. It runs on your own computer, inside Claude Code. It has no server, account, database or connector of its own, so its publisher never receives, sees or keeps your data.

## What the plugin reads

- The faculty content folder you name when you run `/cp-course-builder:start`, and the course folder the plugin writes. The faculty folder is only read, never changed.
- Faculty files can include personal data, most often the instructor's name and contact details in a syllabus.

## What the plugin stores

- Everything it writes goes to one course folder, by default `<faculty-folder>-cpb` beside the faculty folder: intake notes, the blueprint, lesson Markdown, reviews, rendered pages and packages. Personal data in the faculty files can appear in those copies.
- Learner pages store nothing: no cookies, no local storage, no network calls. In an LMS they report only SCORM completion.
- The course folder stays where you keep it. You decide when to delete it.

## What the plugin sends

- The plugin's scripts send no course content or personal data to any outside service.
- `npm install` in `scripts/` downloads the pinned accessibility packages from the npm registry. That request downloads software; it does not send your files.
- The plugin never uploads to Brightspace or any other system, and never emails or messages anyone.

## Claude

The plugin works inside Claude Code, so the content Claude reads while running it is processed by Claude under your Claude account's terms and Anthropic's privacy policy, as with any other Claude Code session. The plugin adds no other recipient.

## Children

The plugin is built for instructional designers and course production staff. It is not intended for users under 18.

## Questions

Ask about this policy or report a privacy concern in [GitHub Issues](https://github.com/abeasley2020/cp-plugins/issues).
