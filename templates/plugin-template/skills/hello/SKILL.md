---
name: hello
description: Replace this with one or two sentences that say what the skill does and when Claude should use it. This text is how Claude decides to invoke the skill, so make it specific.
argument-hint: <what the user should pass>
---

# cp-PLUGIN_NAME: hello

Rename this folder from `hello` to the skill name you want. The skill is invoked as `/cp-PLUGIN_NAME:<folder-name>`.

## Steps

1. Say what to do with `$ARGUMENTS`.
2. If the skill runs a script, keep the script inside this plugin and call it with the substituted plugin path:

   ```
   node "${CLAUDE_PLUGIN_ROOT}/scripts/your-script.mjs" $ARGUMENTS
   ```

3. Say how to present the result to the user.

## Rules for this repository

- No real names, email addresses, dollar amounts, internal URLs, or credentials anywhere in the plugin.
- No em-dashes.
- Scripts use Node.js built-ins only. Do not add dependencies.
