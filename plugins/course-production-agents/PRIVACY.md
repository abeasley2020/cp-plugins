# Privacy policy: Course Production Agents

Last updated: November 9, 2026

Course Production Agents is a Claude Code plugin. It runs on your own computer, inside Claude Code. It has no server, account, database or connector of its own, so its publisher never receives, sees or keeps your data.

## What the plugin reads

- The faculty content folder you name when you run `/course-production-agents:build-course`: syllabi, slides, documents, PDFs, notes, images and caption files.
- That material can include personal data, most often the instructor's name and contact details in a syllabus, and sometimes the names of teaching assistants or guest speakers.

## What the plugin stores

- Everything it writes goes to one work folder beside the faculty folder, named `<faculty-folder>-cp`. The faculty folder itself is never changed.
- The work folder holds text extracted from the faculty files (`intake/`), the course map, media plan, topic files, review pages, packages and reports. Any personal data in the faculty files can appear in those copies, for example an instructor's name in the course map or extracted syllabus text.
- The work folder stays on your computer, or wherever you keep that folder, such as a synced drive. You decide how long to keep it and when to delete it.

## What the plugin sends

- The plugin's scripts send no course content or personal data to any outside service.
- The first build may run `npm install` to download the pinned accessibility packages listed in `scripts/package.json` from the npm registry. That request downloads software; it does not send your files.
- The plugin never uploads to Brightspace, Kaltura, SharePoint or any other system, and never emails or messages anyone. You import the packages yourself.

## Claude

The plugin works inside Claude Code, so the content Claude reads while running the plugin is processed by Claude under your Claude account's terms and Anthropic's privacy policy, as with any other Claude Code session. The plugin adds no other recipient.

## Retention

The publisher retains nothing, because nothing is sent to the publisher. Files in the work folder last until you delete them.

## Children

The plugin is built for instructional designers and course production staff. It is not intended for users under 18.

## Questions

Ask about this policy or report a privacy concern in [GitHub Issues](https://github.com/abeasley2020/cp-plugins/issues).
