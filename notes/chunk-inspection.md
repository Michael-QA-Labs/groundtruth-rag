# Chunk inspection

Stratified sample of 7 chunks from 1,662.
Read this BEFORE writing gold labels - after Day 4 the chunk IDs are frozen.

For each: `text_raw` is what you label against, `text_embed` is what the
model actually sees.

---

## `doc-25:c127` — block_type=code
`agent-sdk/python` · code · 252 tokens · chars 151,910–152,714

**text_raw**
```
        "cache_read_input_tokens": int | None,
        "server_tool_use": {"web_search_requests": int, "web_fetch_requests": int} | None,
        "service_tier": str | None,
        "cache_creation": {"ephemeral_1h_input_tokens": int, "ephemeral_5m_input_tokens": int} | None,
        "inference_geo": str | None,
        "speed": str | None,
        "iterations": Any | None,
    },
    "toolStats": {  # Aggregate tool activity for the run
        "readCount": int,
        "searchCount": int,
        "bashCount": int,
        "editFileCount": int,
        "linesAdded": int,
        "linesRemoved": int,
        "otherToolCount": int,
        "frameCount": int | None,
    } | None,
    "prompt": str,  # The prompt the agent ran
    "worktreePath": str | None,  # Present for worktree-isolated runs
```

**text_embed**
```
"cache_read_input_tokens": int | None,
        "server_tool_use": {"web_search_requests": int, "web_fetch_requests": int} | None,
        "service_tier": str | None,
        "cache_creation": {"ephemeral_1h_input_tokens": int, "ephemeral_5m_input_tokens": int} | None,
        "inference_geo": str | None,
        "speed": str | None,
        "iterations": Any | None,
    },
    "toolStats": {  # Aggregate tool activity for the run
        "readCount": int,
        "searchCount": int,
        "bashCount": int,
        "editFileCount": int,
        "linesAdded": int,
        "linesRemoved": int,
        "otherToolCount": int,
        "frameCount": int | None,
    } | None,
    "prompt": str,  # The prompt the agent ran
    "worktreePath": str | None,  # Present for worktree-isolated runs
```

---

## `doc-18:c006` — block_type=prose
`plugins` · prose · 233 tokens · chars 7,507–8,533

**text_raw**
```
    <Note>
      **Why namespacing?** Plugin skills are always namespaced (like `/my-first-plugin:hello`) to prevent conflicts when multiple plugins have skills with the same name.

      To change the namespace prefix, update the `name` field in `plugin.json`.
    </Note>
  </Step>

  <Step title="Add skill arguments">
    Make your skill dynamic by accepting user input. The `$ARGUMENTS` placeholder captures any text the user provides after the skill name.

    Update your `SKILL.md` file:

    ```markdown my-first-plugin/skills/hello/SKILL.md theme={null}
    ---
    description: Greet the user with a personalized message
    ---

    # Hello Skill

    Greet the user named "$ARGUMENTS" warmly and ask how you can help them today. Make the greeting personal and encouraging.
    ```

    Run `/reload-plugins` to pick up the changes. The skills count in the summary covers only `commands/`
```

**text_embed**
```
**Why namespacing?** Plugin skills are always namespaced (like `/my-first-plugin:hello`) to prevent conflicts when multiple plugins have skills with the same name.

      To change the namespace prefix, update the `name` field in `plugin.json`.
    
  

  
Add skill arguments

    Make your skill dynamic by accepting user input. The `$ARGUMENTS` placeholder captures any text the user provides after the skill name.

    Update your `SKILL.md` file:

    ```markdown my-first-plugin/skills/hello/SKILL.md theme={null}
    ---
    description: Greet the user with a personalized message
    ---

    # Hello Skill

    Greet the user named "$ARGUMENTS" warmly and ask how you can help them today. Make the greeting personal and encouraging.
    ```

    Run `/reload-plugins` to pick up the changes. The skills count in the summary covers only `commands/` directories, so it can report `0 skills` ev
```

---

## `doc-07:c028` — block_type=table_row
`settings` · table_row · 205 tokens · chars 42,529–43,791

**text_raw**
```
| `autoMode`                         | Customize what the [auto mode](/docs/en/permission-modes#eliminate-prompts-with-auto-mode) classifier blocks and allows. Contains `environment`, `allow`, `soft_deny`, and `hard_deny` arrays of prose rules. Include the literal string `"$defaults"` in an array to inherit the built-in rules at that position. See [Configure auto mode](/docs/en/auto-mode-config). Read from user settings, the `--settings` flag, and managed settings only. Ignored in project `.claude/settings.json` and local `.claude/settings.local.json`. {/* min-version: 2.1.207 */}Before v2.1.207, `.claude/settings.local.json` was also read
```

**text_embed**
```
autoMode
Description: Customize what the [auto mode](/docs/en/permission-modes#eliminate-prompts-with-auto-mode) classifier blocks and allows. Contains environment, allow, soft_deny, and hard_deny arrays of prose rules. Include the literal string "$defaults" in an array to inherit the built-in rules at that position. See [Configure auto mode](/docs/en/auto-mode-config). Read from user settings, the --settings flag, and managed settings only. Ignored in project .claude/settings.json and local .claude/settings.local.json. {/* min-version: 2.1.207 */}Before v2.1.207, .claude/settings.local.json was also read
Example: {"soft_deny": ["$defaults", "Never run terraform apply"]}
```

---

## `doc-07:c066` — largest/smallest doc: settings
`settings` · table_row · 252 tokens · chars 124,329–126,833

**text_raw**
```
| `pluginSuggestionMarketplaces`     | (Managed settings only) Marketplace names whose plugins can appear as contextual install suggestions. No marketplace-declared suggestions surface without this allowlist; the built-in first-party frontend-design tip is unaffected. Suggestions come from each plugin's `relevance` declaration in its marketplace entry. A name only takes effect when the marketplace is registered on the machine and its registered source is also declared in managed settings, either as the `extraKnownMarketplaces` entry for that name or as an entry of `strictKnownMarketplaces`. A marketplace registered from a different source under an allowlisted name is ignored. The official marketplace is exempt from the source requirement: allowlisting its name alone suffices, since that name can only register from the official Anthropic source.
```

**text_embed**
```
pluginSuggestionMarketplaces
Description: (Managed settings only) Marketplace names whose plugins can appear as contextual install suggestions. No marketplace-declared suggestions surface without this allowlist; the built-in first-party frontend-design tip is unaffected. Suggestions come from each plugin's relevance declaration in its marketplace entry. A name only takes effect when the marketplace is registered on the machine and its registered source is also declared in managed settings, either as the extraKnownMarketplaces entry for that name or as an entry of strictKnownMarketplaces. A marketplace registered from a different source under an allowlisted name is ignored. The official marketplace is exempt from the source requirement: allowlisting its name alone suffices, since that name can only register from the official Anthropic source.
Example: ["acme-corp-plugins"]

pluginTrustMes
```

---

## `doc-11:c008` — largest/smallest doc: checkpointing
`checkpointing` · prose · 207 tokens · chars 7,054–7,881

**text_raw**
```
To see which paths a restore skips, turn on debug logging with `/debug` before you restore: the debug log at `~/.claude/debug/<session-id>.txt` names each skipped path. For every skip reason and the recovery steps, see [the skipped-files entry in the error reference](/docs/en/errors#restored-the-code-but-skipped-files).

<Note>
  Before v2.1.216, `/rewind` wrote and deleted through links at tracked paths without a warning.
</Note>

### Not a replacement for version control

Checkpoints are designed for quick, session-level recovery. For permanent version history and collaboration:

* Continue using version control (ex. Git) for commits, branches, and long-term history
* Checkpoints complement but don't replace proper version control
* Think of checkpoints as "local undo" and Git as "permanent history"

## See also
```

**text_embed**
```
To see which paths a restore skips, turn on debug logging with `/debug` before you restore: the debug log at `~/.claude/debug/<session-id>.txt` names each skipped path. For every skip reason and the recovery steps, see [the skipped-files entry in the error reference](/docs/en/errors#restored-the-code-but-skipped-files).

  Before v2.1.216, `/rewind` wrote and deleted through links at tracked paths without a warning.

### Not a replacement for version control

Checkpoints are designed for quick, session-level recovery. For permanent version history and collaboration:

* Continue using version control (ex. Git) for commits, branches, and long-term history
* Checkpoints complement but don't replace proper version control
* Think of checkpoints as "local undo" and Git as "permanent history"

## See also
```

---

## `doc-14:c109` — <Tabs> region
`hooks` · prose · 238 tokens · chars 126,486–127,517

**text_raw**
```
| `displayContent` | Text displayed in place of the delta. Omit it to display the original |

MessageDisplay hooks have no decision control. They can't block the message or change what is stored in the transcript or sent to Claude.

This example strips markdown formatting from Claude's responses for a plain-text display. The script reads each batch from stdin, removes bold markers and inline code backticks from `delta`, and returns the result as `displayContent`.

<Tabs>
  <Tab title="macOS/Linux">
    Register a command hook for the event in your settings file:

    ```json theme={null}
    {
      "hooks": {
        "MessageDisplay": [
          {
            "hooks": [
              {
                "type": "command",
                "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/plain-display.sh",
                "args": []
              }
            ]
          }
        ]
```

**text_embed**
```
displayContent
Description: Text displayed in place of the delta. Omit it to display the original

MessageDisplay hooks have no decision control. They can't block the message or change what is stored in the transcript or sent to Claude.

This example strips markdown formatting from Claude's responses for a plain-text display. The script reads each batch from stdin, removes bold markers and inline code backticks from `delta`, and returns the result as `displayContent`.

  
Alternative (macOS/Linux):

    Register a command hook for the event in your settings file:

    ```json theme={null}
    {
      "hooks": {
        "MessageDisplay": [
          {
            "hooks": [
              {
                "type": "command",
                "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/plain-display.sh",
                "args": []
              }
            ]
          }
        ]
```

---

## `doc-20:c016` — <Steps> region
`github-actions` · prose · 249 tokens · chars 14,144–15,184

**text_raw**
```
       * Choose "Only select repositories" and select the specific repository
       * Click "Install"
    9. Add the private key as a secret to your repository:
       * Go to your repository's Settings → Secrets and variables → Actions
       * Create a new secret named `APP_PRIVATE_KEY` with the contents of the `.pem` file
    10. Add the App ID as a secret:

    * Create a new secret named `APP_ID` with your GitHub App's ID

    <Note>
      This app will be used with the [actions/create-github-app-token](https://github.com/actions/create-github-app-token) action to generate authentication tokens in your workflows.
    </Note>

    **Alternative for Claude API or if you don't want to setup your own Github app**: Use the official Anthropic app:

    1. Install from: [https://github.com/apps/claude](https://github.com/apps/claude)
    2. No additional configuration needed for authentic
```

**text_embed**
```
* Choose "Only select repositories" and select the specific repository
       * Click "Install"
    9. Add the private key as a secret to your repository:
       * Go to your repository's Settings → Secrets and variables → Actions
       * Create a new secret named `APP_PRIVATE_KEY` with the contents of the `.pem` file
    10. Add the App ID as a secret:

    * Create a new secret named `APP_ID` with your GitHub App's ID

    
      This app will be used with the [actions/create-github-app-token](https://github.com/actions/create-github-app-token) action to generate authentication tokens in your workflows.
    

    **Alternative for Claude API or if you don't want to setup your own Github app**: Use the official Anthropic app:

    1. Install from: [https://github.com/apps/claude](https://github.com/apps/claude)
    2. No additional configuration needed for authentication
  

  
Configu
```
