# Chunk inspection

Stratified sample of 7 chunks from 1,637.
Read this BEFORE writing gold labels - after Day 4 the chunk IDs are frozen.

For each: `text_raw` is what you label against, `text_embed` is what the
model actually sees.

---

## `doc-25:c125` — block_type=code
`agent-sdk/python` · code · 253 tokens · chars 150,119–150,975

**text_raw**
```
```python theme={null}
{
    "description": str,  # A short (3-5 word) description of the task
    "prompt": str,  # The task for the agent to perform
    "subagent_type": str | None,  # The type of specialized agent to use
    "model": "sonnet" | "opus" | "haiku" | "fable" | None,  # Model override for this agent
    "run_in_background": bool | None,  # Agents run in the background by default; set to False to run synchronously
    "name": str | None,  # Name for the spawned agent
    "team_name": str | None,  # Deprecated; ignored
    "mode": "acceptEdits" | "auto" | "bypassPermissions" | "default" | "dontAsk" | "plan" | None,  # Deprecated; ignored. Subagents inherit the parent session's permission mode; agent-definition frontmatter may override it
    "isolation": "worktree" | "remote" | None,  # Isolation mode for the agent's changes
}
```
```

**text_embed**
```
```python theme={null}
{
    "description": str,  # A short (3-5 word) description of the task
    "prompt": str,  # The task for the agent to perform
    "subagent_type": str | None,  # The type of specialized agent to use
    "model": "sonnet" | "opus" | "haiku" | "fable" | None,  # Model override for this agent
    "run_in_background": bool | None,  # Agents run in the background by default; set to False to run synchronously
    "name": str | None,  # Name for the spawned agent
    "team_name": str | None,  # Deprecated; ignored
    "mode": "acceptEdits" | "auto" | "bypassPermissions" | "default" | "dontAsk" | "plan" | None,  # Deprecated; ignored. Subagents inherit the parent session's permission mode; agent-definition frontmatter may override it
    "isolation": "worktree" | "remote" | None,  # Isolation mode for the agent's changes
}
```
```

---

## `doc-18:c015` — block_type=prose
`plugins` · prose · 235 tokens · chars 16,024–16,981

**text_raw**
```
Setting `agent` activates one of the plugin's [custom agents](/docs/en/sub-agents) as the main thread, applying its system prompt, tool restrictions, and model. This lets a plugin change how Claude Code behaves by default when enabled.

```json settings.json theme={null}
{
  "agent": "security-reviewer"
}
```

This example activates the `security-reviewer` agent defined in the plugin's `agents/` directory. Settings from `settings.json` take priority over `settings` declared in `plugin.json`. Unknown keys are silently ignored.

### Organize complex plugins

For plugins with many components, organize your directory structure by functionality. For complete directory layouts and organization patterns, see [Plugin directory structure](/docs/en/plugins-reference#plugin-directory-structure).

### Test your plugins locally

Use the `--plugin-dir` flag to test plugins during development. This loa
```

**text_embed**
```
Setting `agent` activates one of the plugin's [custom agents](/docs/en/sub-agents) as the main thread, applying its system prompt, tool restrictions, and model. This lets a plugin change how Claude Code behaves by default when enabled.

```json settings.json theme={null}
{
  "agent": "security-reviewer"
}
```

This example activates the `security-reviewer` agent defined in the plugin's `agents/` directory. Settings from `settings.json` take priority over `settings` declared in `plugin.json`. Unknown keys are silently ignored.

### Organize complex plugins

For plugins with many components, organize your directory structure by functionality. For complete directory layouts and organization patterns, see [Plugin directory structure](/docs/en/plugins-reference#plugin-directory-structure).

### Test your plugins locally

Use the `--plugin-dir` flag to test plugins during development. This loa
```

---

## `doc-07:c027` — block_type=table_row
`settings` · table_row · 184 tokens · chars 43,791–46,305

**text_raw**
```
| `autoMode.classifyAllShell`        | {/* min-version: 2.1.193 */}**Default**: `false`. When `true`, suspends every Bash and PowerShell allow rule while auto mode is active so all shell commands route through the classifier, not only rules that match arbitrary-code-execution patterns. See [Route all shell commands through the classifier](/docs/en/auto-mode-config#route-all-shell-commands-through-the-classifier). Requires Claude Code v2.1.193 or later
```

**text_embed**
```
autoMode.classifyAllShell
Description: **Default**: false. When true, suspends every Bash and PowerShell allow rule while auto mode is active so all shell commands route through the classifier, not only rules that match arbitrary-code-execution patterns. See [Route all shell commands through the classifier](/docs/en/auto-mode-config#route-all-shell-commands-through-the-classifier). Requires Claude Code v2.1.193 or later
Example: true

autoScrollEnabled
Description: **Default**: true. In [fullscreen rendering](/docs/en/fullscreen), follow new output to the bottom of the conversation. Appears in /config as **Auto-scroll**. Permission prompts still scroll into view when this is off
Example: false
```

---

## `doc-07:c066` — largest/smallest doc: settings
`settings` · table_row · 122 tokens · chars 131,861–133,113

**text_raw**
```
| `prUrlTemplate`                    | URL template for the PR badge shown in the footer and in tool-result summaries. Substitutes `{host}`, `{owner}`, `{repo}`, `{number}`, and `{url}` from the `gh`-reported PR URL. Use to point PR links at an internal code-review tool instead of `github.com`. Does not affect `#123` autolinks in Claude's prose
```

**text_embed**
```
prUrlTemplate
Description: URL template for the PR badge shown in the footer and in tool-result summaries. Substitutes {host}, {owner}, {repo}, {number}, and {url} from the gh-reported PR URL. Use to point PR links at an internal code-review tool instead of github.com. Does not affect #123 autolinks in Claude's prose
Example: "https://reviews.example.com/{owner}/{repo}/pull/{number}"
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

## `doc-20:c014` — <Steps> region
`github-actions` · prose · 234 tokens · chars 12,155–13,223

**text_raw**
```
For enterprise environments, you can use Claude Code GitHub Actions with your own cloud infrastructure. This approach gives you control over data residency and billing while maintaining the same functionality.

### Prerequisites

Before setting up Claude Code GitHub Actions with cloud providers, you need:

#### For Google Cloud's Agent Platform:

1. A Google Cloud Project with Google Cloud's Agent Platform enabled
2. Workload Identity Federation configured for GitHub Actions
3. A service account with the required permissions
4. A GitHub App (recommended) or use the default GITHUB\_TOKEN

#### For Amazon Bedrock:

1. An AWS account with Amazon Bedrock enabled
2. GitHub OIDC Identity Provider configured in AWS
3. An IAM role with Amazon Bedrock permissions
4. A GitHub App (recommended) or use the default GITHUB\_TOKEN

<Steps>
  <Step title="Create a custom GitHub App (Recommended for 3P P
```

**text_embed**
```
For enterprise environments, you can use Claude Code GitHub Actions with your own cloud infrastructure. This approach gives you control over data residency and billing while maintaining the same functionality.

### Prerequisites

Before setting up Claude Code GitHub Actions with cloud providers, you need:

#### For Google Cloud's Agent Platform:

1. A Google Cloud Project with Google Cloud's Agent Platform enabled
2. Workload Identity Federation configured for GitHub Actions
3. A service account with the required permissions
4. A GitHub App (recommended) or use the default GITHUB\_TOKEN

#### For Amazon Bedrock:

1. An AWS account with Amazon Bedrock enabled
2. GitHub OIDC Identity Provider configured in AWS
3. An IAM role with Amazon Bedrock permissions
4. A GitHub App (recommended) or use the default GITHUB\_TOKEN

  
Create a custom GitHub App (Recommended for 3P Providers)

    For b
```
