# Corpus INDEX

30 pages from the Claude Code docs, fetched 2026-07-29.

**FROZEN.** Do not add, remove, or re-fetch pages. Every metric in
`results/` is only comparable to another number computed against this
exact corpus. To verify nothing has drifted, re-run this script and
check the hash below still matches.

- Total: 1,788,786 chars
- sha256: `a887366bab9778b59129493073c38a116d55ff8e6657b191be1f9d5678473737`

## Size skew — read this before trusting a metric

The three largest pages are 40% of the corpus by characters:

- `settings` — 272,476 chars
- `hooks` — 242,072 chars
- `agent-sdk/python` — 193,850 chars

They were kept rather than dropped (see notes/decisions.md D3), so
expect them to dominate chunk counts. Report per-doc chunk counts
alongside any aggregate metric.

## Pages

| ID | Slug | Source URL | Chars | Fetched |
|---|---|---|---:|---|
| doc-01 | `overview` | https://code.claude.com/docs/en/overview.md | 16,435 | 2026-07-29 |
| doc-02 | `quickstart` | https://code.claude.com/docs/en/quickstart.md | 13,115 | 2026-07-29 |
| doc-03 | `how-claude-code-works` | https://code.claude.com/docs/en/how-claude-code-works.md | 20,221 | 2026-07-29 |
| doc-04 | `common-workflows` | https://code.claude.com/docs/en/common-workflows.md | 18,743 | 2026-07-29 |
| doc-05 | `best-practices` | https://code.claude.com/docs/en/best-practices.md | 39,664 | 2026-07-29 |
| doc-06 | `memory` | https://code.claude.com/docs/en/memory.md | 35,300 | 2026-07-29 |
| doc-07 | `settings` | https://code.claude.com/docs/en/settings.md | 272,476 | 2026-07-29 |
| doc-08 | `cli-reference` | https://code.claude.com/docs/en/cli-reference.md | 104,140 | 2026-07-29 |
| doc-09 | `context-window` | https://code.claude.com/docs/en/context-window.md | 57,905 | 2026-07-29 |
| doc-10 | `permissions` | https://code.claude.com/docs/en/permissions.md | 60,808 | 2026-07-29 |
| doc-11 | `checkpointing` | https://code.claude.com/docs/en/checkpointing.md | 8,108 | 2026-07-29 |
| doc-12 | `skills` | https://code.claude.com/docs/en/skills.md | 73,820 | 2026-07-29 |
| doc-13 | `hooks-guide` | https://code.claude.com/docs/en/hooks-guide.md | 62,452 | 2026-07-29 |
| doc-14 | `hooks` | https://code.claude.com/docs/en/hooks.md | 242,072 | 2026-07-29 |
| doc-15 | `sub-agents` | https://code.claude.com/docs/en/sub-agents.md | 94,952 | 2026-07-29 |
| doc-16 | `mcp` | https://code.claude.com/docs/en/mcp.md | 80,849 | 2026-07-29 |
| doc-17 | `tools-reference` | https://code.claude.com/docs/en/tools-reference.md | 87,834 | 2026-07-29 |
| doc-18 | `plugins` | https://code.claude.com/docs/en/plugins.md | 27,692 | 2026-07-29 |
| doc-19 | `headless` | https://code.claude.com/docs/en/headless.md | 26,099 | 2026-07-29 |
| doc-20 | `github-actions` | https://code.claude.com/docs/en/github-actions.md | 29,715 | 2026-07-29 |
| doc-21 | `code-review` | https://code.claude.com/docs/en/code-review.md | 29,638 | 2026-07-29 |
| doc-22 | `worktrees` | https://code.claude.com/docs/en/worktrees.md | 18,415 | 2026-07-29 |
| doc-23 | `output-styles` | https://code.claude.com/docs/en/output-styles.md | 9,909 | 2026-07-29 |
| doc-24 | `agent-sdk/overview` | https://code.claude.com/docs/en/agent-sdk/overview.md | 9,069 | 2026-07-29 |
| doc-25 | `agent-sdk/python` | https://code.claude.com/docs/en/agent-sdk/python.md | 193,850 | 2026-07-29 |
| doc-26 | `agent-sdk/custom-tools` | https://code.claude.com/docs/en/agent-sdk/custom-tools.md | 41,402 | 2026-07-29 |
| doc-27 | `agent-sdk/structured-outputs` | https://code.claude.com/docs/en/agent-sdk/structured-outputs.md | 21,248 | 2026-07-29 |
| doc-28 | `agent-sdk/hooks` | https://code.claude.com/docs/en/agent-sdk/hooks.md | 52,671 | 2026-07-29 |
| doc-29 | `agent-sdk/cost-tracking` | https://code.claude.com/docs/en/agent-sdk/cost-tracking.md | 18,558 | 2026-07-29 |
| doc-30 | `agent-sdk/sessions` | https://code.claude.com/docs/en/agent-sdk/sessions.md | 21,626 | 2026-07-29 |
