# cp-plugins

Claude Code plugin marketplace for the Purdue University Online Course Production team.

Each plugin packages a repeatable piece of course production work (an accessibility check, a build step, a review) so every instructional designer runs it the same way from Claude Code.

## Plugins

| Plugin | Command | What it does |
|---|---|---|
| [cp-accessibility](plugins/cp-accessibility/README.md) | `/cp-accessibility:check <file-or-folder>` | Static WCAG 2.2 AA checks for HTML course content. Reports each finding with its success criterion, level, line, and fix. |

## Install

Requirements: Claude Code and Node.js 20 or later (the plugin scripts use Node built-ins only).

From a Claude Code session, add the marketplace from GitHub, then install the plugin you want:

```
/plugin marketplace add <github-owner>/cp-plugins
/plugin install cp-accessibility@cp-plugins
```

`<github-owner>` is the GitHub account or organization that hosts this repository. The marketplace name is `cp-plugins` regardless of where it is hosted.

To test a local checkout instead, point the marketplace at the folder that contains `.claude-plugin/marketplace.json`:

```
/plugin marketplace add ./cp-plugins
/plugin install cp-accessibility@cp-plugins
```

After the marketplace changes, run `/plugin marketplace update cp-plugins` (or restart the session) to pick up new versions.

## Configuration

Plugins read an optional runtime config from the user's home folder, never from this repository:

```
%USERPROFILE%\.cp-plugins\config.json
```

On macOS and Linux that is `~/.cp-plugins/config.json`. Installed plugins are copied into a cache, so a file inside the repository would not exist on team machines. Copy `config.example.json` to that location to start. Each plugin documents its own section; see the cp-accessibility README for the `accessibility` keys.

## Repository layout

```
.claude-plugin/marketplace.json   the marketplace manifest (every plugin must be listed here)
plugins/<name>/                   one folder per plugin
templates/plugin-template/        starting point for a new plugin
scripts/                          CI checks: validate-marketplace, scan-content, ci
.github/workflows/ci.yml          GitHub Actions: validate, scan, test on Ubuntu and Windows
config.example.json               template for the runtime config
```

## CI checks

Every push and pull request runs three checks. Run them locally with one command:

```
node scripts/ci.mjs
```

Or individually:

```
node scripts/validate-marketplace.mjs
node scripts/scan-content.mjs
node --test "scripts/tests/*.test.mjs" "plugins/*/tests/*.test.mjs"
```

1. **Validate marketplace.** `marketplace.json` parses, every entry has a name, source, description, and version, every entry's folder exists with a matching `plugin.json`, and every folder under `plugins/` is listed. Plugin names use the `cp-` prefix.
2. **Content scan.** No file may contain a dollar amount, an email address, an internal URL, a credential-like value, a person's name in a byline or author field, or an em-dash. This repository is public.
3. **Unit tests.** Node's built-in test runner covers the scripts and each plugin.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add a plugin from the template, what the checks require, and the pull request checklist.

## Dependencies

None. The scripts and plugins use only Node.js built-ins. CI uses the `actions/checkout` and `actions/setup-node` GitHub Actions.

## License

License pending. A license will be added once intellectual property ownership is confirmed. Until then, all rights reserved.
