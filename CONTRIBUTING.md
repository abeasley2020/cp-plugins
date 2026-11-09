# Contributing

This repository is public. Everything in it is visible to anyone, so the rules below are about keeping internal details out as much as they are about code quality.

## Ground rules

- No real names. Credit the team ("Purdue University Online Course Production"), never a person.
- No email addresses, dollar amounts, internal URLs (SharePoint, Brightspace, intranet hosts, private IPs), or credentials of any kind.
- No em-dashes in any file.
- No dependencies. Scripts use Node.js built-ins only. If a plugin truly needs a package, open an issue first and list the package and why.
- Runtime configuration lives in `%USERPROFILE%\.cp-plugins\config.json`, never in the repository.
- Plugin names start with `cp-` and use kebab-case: `cp-accessibility`, `cp-media-plan`.

The CI content scan enforces the first three mechanically. Reviewers check the rest.

## Add a new plugin

Run each command on its own line. Do not chain commands.

1. Copy the template into `plugins/` under the new plugin name:

   ```powershell
   Copy-Item -Recurse templates\plugin-template plugins\cp-my-plugin
   ```

2. Edit `plugins/cp-my-plugin/.claude-plugin/plugin.json`. Replace every placeholder:

   | Placeholder | Replace with |
   |---|---|
   | `cp-PLUGIN_NAME` | the plugin name, for example `cp-my-plugin` |
   | `PLUGIN_DESCRIPTION` | one sentence that says what the plugin does |
   | `PLUGIN_KEYWORD` | one or more search keywords, or remove it |

   Leave `author.name` as the team name. Do not add an email.

3. Rename `skills/hello` to the skill name you want and rewrite `SKILL.md`. The skill is invoked as `/cp-my-plugin:<folder-name>`. Keep the frontmatter `description`; CI rejects a skill without one.

4. Rewrite `README.md` in the plugin folder. Replace the placeholders and describe usage, configuration, and limits.

5. Register the plugin in `.claude-plugin/marketplace.json`. Add an entry with the same `name` and `version` as `plugin.json`:

   ```json
   {
     "name": "cp-my-plugin",
     "source": "./plugins/cp-my-plugin",
     "description": "One sentence that says what the plugin does.",
     "version": "0.1.0"
   }
   ```

   CI fails if a folder under `plugins/` is not listed here, and fails if an entry points at a folder that does not exist.

6. Add tests under `plugins/cp-my-plugin/tests/` as `*.test.mjs` files if the plugin has scripts. CI runs them with `node --test`.

7. Run the checks locally:

   ```powershell
   node scripts/ci.mjs
   ```

   Optionally confirm with the Claude Code validator:

   ```powershell
   claude plugin validate .
   ```

   ```powershell
   claude plugin validate plugins\cp-my-plugin
   ```

8. Try it in a session. Add the local checkout as a marketplace and install the plugin:

   ```
   /plugin marketplace add ./cp-plugins
   ```

   ```
   /plugin install cp-my-plugin@cp-plugins
   ```

   Run your skill and confirm it behaves. If you already have the marketplace added, run `/plugin marketplace update cp-plugins` first.

9. Open a pull request. Fill in the checklist in the template.

## Change an existing plugin

- Bump `version` in both `plugins/<name>/.claude-plugin/plugin.json` and the matching entry in `.claude-plugin/marketplace.json`. CI fails if they differ. Use patch for fixes, minor for new behavior, major for breaking changes.
- Update the plugin README when behavior or configuration changes.
- Run `node scripts/ci.mjs` before you push.

## What CI checks

| Check | Command | Fails when |
|---|---|---|
| Validate marketplace | `node scripts/validate-marketplace.mjs` | the manifest is malformed, a plugin is unlisted or missing, names or versions disagree, a placeholder is left in, a README or component is missing, or a skill lacks a description |
| Content scan | `node scripts/scan-content.mjs` | any text file contains a dollar amount, email, internal URL, credential, person-like byline or author name, or em-dash |
| Unit tests | `node --test "scripts/tests/*.test.mjs" "plugins/*/tests/*.test.mjs"` | any test fails |

The content scan prints the file, line, column, rule, and a redacted snippet for every finding. Fix the content rather than suppressing the rule. If a rule produces a false positive, change the rule in `scripts/lib/scan-rules.mjs` with a test that shows the case.

## Pull request checklist

- [ ] `node scripts/ci.mjs` passes locally
- [ ] No real names, emails, dollar amounts, internal URLs, or credentials
- [ ] No em-dashes
- [ ] No new dependencies
- [ ] Plugin README updated
- [ ] Version bumped in `plugin.json` and `marketplace.json` (for changes to an existing plugin)
