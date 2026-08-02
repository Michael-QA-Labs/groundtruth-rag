# Gold set

Corpus: `a887366bab9778b59129493073c38a116d55ff8e6657b191be1f9d5678473737` (30 pages, frozen 2026-07-29)
Index: 1,637 chunks · `all-MiniLM-L6-v2` · 384-dim · 254-token budget
Built on: _(date)_

Target: **30 questions, 5 of them unanswerable.**
Final output is `gold/gold-set.json`. This file is the working surface.

---

## How to fill this in

**Day 3 fills `Question`. Nothing else is required.**
Write with the docs closed. Gold chunks are Day 4. Metrics are Day 6.

`Type` and `Source` are optional. Fill them only when the answer is obvious in
the moment. Leave them blank rather than stopping to think, and never let them
interrupt the flow of writing questions.

### Fields

| Field | When | Notes |
|---|---|---|
| `Question` | Day 3 | Your own words, from a problem you actually hit |
| `Type` | optional | `configuration` · `factual` · `procedural` · `multi_hop` · `comparison` · `error` |
| `Source` | optional | The real situation this came from. One line. Memory jog for Day 5 |
| `Answerable` | Day 4 | `yes` or `no` |
| `Gold chunks` | Day 4 | Chunk IDs, `doc-NN:cNNN`. `none` if unanswerable |
| `Gold answer` | Day 4 | What a correct answer must contain |
| `Not covered because` | Day 4 | Unanswerable only. Plus the search that proves it |
| `Retrieved top 10` | Day 6 | Chunk IDs from `search.py`, in rank order |
| Metrics table | Day 6 | By hand first. Day 7 code gets checked against these |

### Five rules

1. **Chunk IDs, not doc IDs.** `doc-10:c005`, never `doc-10`. Doc-level metrics
   fall out of chunk labels for free. The reverse does not, and chunk labels
   survive a re-chunk.

2. **Label against `text_raw`.** Never `text_embed`. A rendering bug can degrade
   retrieval; it must not be able to corrupt a label. See `notes/chunk-inspection.md`.

3. **Gold is a set.** Median chunk is ~214 tokens, so answers straddle
   boundaries. Two or three gold chunks is normal, not a mistake.

4. **Duplicate groups get labeled together.** If your gold chunk is in one of
   these pairs, label both, or a correct retrieval scores as a miss:
   `doc-01:c002`/`doc-02:c002` · `doc-01:c003`/`doc-02:c003` ·
   `doc-13:c022`/`doc-14:c002` · `doc-13:c023`/`doc-14:c003`

5. **Unanswerable means demonstrably not covered.** Not "I couldn't find it."
   Failing to find something is not evidence of absence. Verify with
   `search.py "..." --top 20 --show-text` and record what you checked.

### Recall and precision are undefined when `Answerable: no`

There is no gold chunk, so there is nothing to recall. Those five questions are
scored on abstention instead: did the system correctly decline. Their metric
block is different, and they are excluded from the recall/precision means.

---

## Worked example (reference, not one of the 30)

**Question:** How do I stop Claude asking me before every single file edit?

**Type:** configuration
**Source:** Approving every edit by hand during a long refactor.
**Answerable:** yes
**Gold chunks:** `doc-02:c008`, `doc-10:c005`
**Gold answer:** Permission behavior is set by the permission mode. `Shift+Tab`
cycles modes live and `acceptEdits` auto-approves file edits; `defaultMode` in
`settings.json` sets it persistently.

**Not covered because:** n/a

**Why this question is good:** the phrasing shares no rare vocabulary with
either gold chunk. The chunks say "permission mode", "acceptEdits",
"defaultMode"; the question says "stop asking me before every edit". The
retriever has to bridge that semantically, which is the thing worth measuring.

**Retrieved top 10:** `doc-02:c008, doc-05:c013, doc-13:c060, doc-05:c012, doc-17:c023, doc-05:c035, doc-17:c031, doc-17:c030, doc-10:c005, doc-06:c032`

| Metric | Value | Working |
|---|---|---|
| recall@3 | 0.5 | 2 gold chunks, 1 in top 3 (`doc-02:c008` at rank 1) → 1/2 |
| recall@10 | 1.0 | both found, `doc-10:c005` at rank 9 → 2/2 |
| precision@3 | 0.333 | 1 gold in the top 3 → 1/3 |
| first relevant rank | 1 | |

**Read the recall@3 of 0.5.** The top hit was correct and the score is still
half, because the second gold chunk sits at rank 9. A single-number "it found
it" would have hidden that. This is why gold is a set.

> These retrieved IDs are real output from `src/search.py` against the frozen
> index. The two gold chunks are provisional: confirm them on Day 4 by reading
> `text_raw` yourself. The previous version of this template used invented
> numbers, which is the exact failure this project exists to avoid.

---

## Q01

**Question:** How do i set-up claude code in my CLI

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-02:c005`, `doc-01:c001`, `doc-02:c001`
**Gold answer:** You need a Claude account (Pro, Max, Team or Enterprise, or a
Console account), then run the official install command for your OS in a
terminal: `curl -fsSL https://claude.ai/install.sh | bash` on macOS, Linux or
WSL.
**Not covered because:** n/a

Author's answer confirmed on both claims, including the four plan names.

| Claim | Chunk |
|---|---|
| account, plans named Pro / Max / Team / Enterprise | `doc-02:c005` (the only chunk naming all four) |
| official install command for your OS | `doc-01:c001` or `doc-02:c001`, alternatives under D5a |

**Windows pair excluded.** `doc-01:c002` / `doc-02:c002` carry the PowerShell and
CMD commands and are one of the four byte-identical duplicate groups. The gold
answer's claim is "run the official install command for your OS", which
`doc-01:c001` already satisfies for a reader on any one platform. Adding them
would push gold to five chunks and depress recall without measuring anything the
existing three do not.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q02

**Question:** How do i import a plugin

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-05:c020`, `doc-12:c056`, `doc-16:c003`
**Gold answer:** Run `/plugin` to browse the marketplace, or install directly
with `/plugin install <name>@<marketplace>`. After installing, run
`/reload-plugins` to activate it in the current session.
**Not covered because:** n/a

Author's answer confirmed on all three claims, including "activate it by
reloading your environment", which turned out to be a real command rather than a
guess: *"Once installed, run `/reload-plugins` to activate it in the current
session."*

| Claim | Chunk |
|---|---|
| `/plugin` browses the marketplace | `doc-05:c020` |
| install, then reload to activate | `doc-12:c056` or `doc-16:c003`, alternatives under D5a |

**One correction to the author's phrasing.** The docs document the command form
`/plugin install <name>@<marketplace>`, not a browse-and-select flow with
keystrokes. "Navigate to the plugin and hit enter" is how the picker behaves, but
no chunk describes it, so the gold answer states the command instead.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q03

**Question:** Can claude code create a mcp

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-16:c003`
**Gold answer:** Yes. Install the MCP server development plugin with
`/plugin install mcp-server-dev@claude-plugins-official`, run `/reload-plugins`,
then run `/mcp-server-dev:build-mcp-server`. Claude asks about your use case and
scaffolds a remote HTTP or local stdio server.
**Not covered because:** n/a

**Right answer, wrong mechanism.** The author's "yes" is correct, but the reason
given was generic agent capability ("operates natively as a terminal agent with
full file access, you can command it to scaffold, code and register it"). The
corpus never makes that claim. It documents one specific supported path, and
`doc-16:c003` contains the whole of it: install the plugin, reload, run the build
skill. Answer rewritten to the documented path.

This is the same failure family as Q15: a confident answer assembled from how the
tool obviously *could* work rather than from what the docs state.

**Considered and rejected:** `doc-16:c002` points at the external MCP server
guide at modelcontextprotocol.io for protocol fundamentals. That is a pointer off
the corpus, not an answer inside it, and the gold answer does not depend on it.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q04

**Question:** How can i extract a json using claude code

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-08:c000`, `doc-01:c011`, `doc-04:c016`, `doc-05:c028`
**Gold answer:** Pipe the content into non-interactive mode and ask for JSON:
`cat file | claude -p "extract the fields you want" --output-format json`. Stdin
and stdout behave like any Unix tool.
**Not covered because:** n/a

**The clipboard is not in this corpus.** The author's mechanism was "copied to
your clipboard… feed it directly to claude code". The word `clipboard` appears in
exactly **one** chunk corpus-wide (`doc-14:c067`), about OSC 52 escape sequences
being rejected in hook output. Unrelated. The intent (feed content in, get JSON
out) is well documented; the route is stdin, not the clipboard.

| Claim | Chunks |
|---|---|
| pipe content into `claude -p` | `doc-08:c000`, `doc-01:c011`, `doc-04:c016`, alternatives under D5a |
| ask for JSON with `--output-format json` | `doc-05:c028` |

**Flagged for Day 5, and this one is a genuine problem.** Four gold chunks makes
recall@10 hard to satisfy: three of them are interchangeable demonstrations of
the same Unix pipe, so a retriever that finds one has served the user completely
while scoring 0.25. D5a says label them all and read MRR alongside recall, which
is correct but unsatisfying at this set size. Candidate fix on Day 5 is to narrow
the question so it turns on the output format rather than on the plumbing.

**Considered and rejected:** `doc-08:c026` documents `--input-format` and only
shows `--output-format json` incidentally inside its example. It does not
document the flag the answer depends on.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q05

**Question:** how do we use agents in claude code

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-15:c059`
**Gold answer:** Three escalating styles: name the subagent in natural language
and let Claude decide whether to delegate; `@`-mention it to guarantee it runs
for one task; or make it session-wide with the `--agent` flag or the `agent`
setting.
**Not covered because:** n/a

**Two of the author's three styles were right.** The corpus lists exactly three,
all in one chunk:

| Documented | Author's answer |
|---|---|
| natural language, Claude decides | ✅ "natural language delegation" |
| `@`-mention, guarantees it runs | ✅ "direct `@` mentioning" |
| session-wide via `--agent` flag or `agent` setting | ❌ "direct slash command" |

Slash commands invoke **skills** (`/plugin-name:skill-name`, `doc-18:c017`), not
subagents. Third style corrected.

**Single gold chunk, deliberately.** `doc-15:c059` states all three styles
together, so it alone supports the whole answer. `doc-15:c060` expands the
`@`-mention step and `doc-15:c017` covers plugin subagents in the typeahead;
both fail the delete test because nothing in the gold answer needs them.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q06

**Question:** when to use auto mode in claude code

**Type:** configuration
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-05:c015`, `doc-05:c032`
**Gold answer:** Use auto mode when you trust the general direction of a task but
don't want to click through every step. A separate classifier model reviews
commands before they run and blocks scope escalation, unknown infrastructure and
hostile-content-driven actions, letting routine work proceed without prompts.
**Not covered because:** n/a

*Gold answer written by Claude, not the author.*

Alternatives under D5a: `doc-05:c015` gives the "best when" framing directly,
`doc-05:c032` gives the same guidance from the uninterrupted-execution angle.
Either alone supports the answer.

**Note the corpus gap.** Every one of these chunks links to
`/docs/en/permission-modes`, which is **not** one of the 30 pages. The
when-to-use guidance survives only because `best-practices` happens to restate
it. See the Day 4 corpus-gap note at the end of this file.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q07

**Question:** if i block a tool completely does claude still know it exists

**Type:** factual
**Source:** Replaced 2026-08-01. Original asked about a nonexistent "edit mode".
**Answerable:** yes
**Gold chunks:** `doc-10:c004`
**Gold answer:** No. A bare tool name in a deny rule, like `Bash`, removes the
tool from Claude's context entirely, so Claude never sees it. A scoped rule like
`Bash(rm *)` leaves the tool visible and blocks only matching calls when Claude
attempts them.
**Not covered because:** n/a

*Question and gold answer written by Claude, not the author.*

**Vocabulary check passed.** Question says "block a tool completely", "know it
exists". Chunk says "deny rules", "bare tool name", "removes the tool from
Claude's context". No rare term is shared, so the retriever has to bridge
block → deny and know it exists → sees it semantically.

Replaces the malformed "when to use edit mode". Draws on `permissions`, which had
70 chunks and zero questions before this.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q08

**Question:** when to use plan mode in claude code

**Type:** configuration
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-04:c015`, `doc-03:c018`
**Gold answer:** Use plan mode when you want to review changes before they touch
disk, or to separate research from coding on a complex problem. Claude reads
files and proposes a plan but makes no edits until you approve. Enter it with
`claude --permission-mode plan` or `Shift+Tab` twice.
**Not covered because:** n/a

*Gold answer written by Claude, not the author.*

**Complements, not alternatives. Corrected on re-verification 2026-08-01**, which
found this entry had called them alternatives. It was wrong: each chunk carries a
different "when" *and* a different entry method, and the gold answer claims both.

| Claim | Chunk |
|---|---|
| review before changes touch disk; Claude proposes but does not edit | `doc-04:c015` |
| `claude --permission-mode plan` | `doc-04:c015` |
| separate research from coding on complex problems | `doc-03:c018` |
| `Shift+Tab` twice | `doc-03:c018` |

A grep confirms `Shift+Tab` does not appear in `doc-04:c015` at all. Neither
chunk alone supports the answer as written, so the delete test keeps both for the
ordinary D5 reason rather than the D5a one.

Same `permission-modes` corpus gap as Q06.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q09

**Question:** after a long chat gets summarised do my project rules stick around

**Type:** factual
**Source:** Replaced 2026-08-01. Original had no documented referent.
**Answerable:** yes
**Gold chunks:** `doc-09:c061`
**Gold answer:** Yes. Project-root CLAUDE.md, unscoped rules and auto memory are
re-injected from disk after compaction. The system prompt and output style are
unchanged because they were never part of message history.
**Not covered because:** n/a

*Question and gold answer written by Claude, not the author.*

**Vocabulary check passed.** Question says "long chat gets summarised", "project
rules", "stick around". Chunk says "compaction", "re-injected from disk". The
retriever must bridge summarised → compaction, which is the interesting part.

**A hard case by construction.** 29 of `context-window`'s 66 chunks are the JSX
source of an embedded visualization. This question tests whether the retriever
finds one prose chunk among that noise.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q10

**Question:** what are the best practices when prompting in claude code

**Type:** factual
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-02:c011`
**Gold answer:** Be specific rather than vague: "fix the login bug where users
see a blank screen after entering wrong credentials" instead of "fix the bug".
Give step-by-step instructions for multi-part work.
**Not covered because:** n/a

*Gold answer written by Claude, not the author.*

**Deliberately narrow, and this is a judgement call worth checking.** The whole
of `best-practices` (doc-05, 38 chunks) is arguably an answer to "best practices
when prompting", which would make gold enormous and recall meaningless. The gold
answer is therefore scoped to the corpus's own explicit prompting-advice block,
`doc-02:c011`, which lists the practices under that heading.

**Day 5 candidate.** If the intent was broader, this question needs splitting.
As written it is close to Q12 and Q14 in breadth.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q11

**Question:** can task monitor tell if a background task will finish or loop forever?

**Type:**
**Source:**
**Answerable:** no
**Gold chunks:** none
**Gold answer:**
**Not covered because:** Verified 2026-08-01 with `search.py --top 20`. Docs cover background tasks, `/tasks`, timeouts, auto-backgrounding and `--max-budget-usd`, but never completion prediction. Top hit `doc-17:c028` scores 0.558 and is on-topic without answering.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q12

**Question:** what is already eating my context before i type anything

**Type:** factual
**Source:** Replaced 2026-08-01. Original turned on "unique", which the corpus
never claims about anything.
**Answerable:** yes
**Gold chunks:** `doc-09:c060`
**Gold answer:** CLAUDE.md, auto memory, MCP tool names and skill descriptions
all load into context before your first prompt. Setup-specific additions such as
an output style or `--append-system-prompt` text go into the system prompt the
same way.
**Not covered because:** n/a

*Question and gold answer written by Claude, not the author.*

**Vocabulary check passed.** Question says "eating my context", "before i type
anything". Chunk says "Before you type anything" as a bold lead-in, which is a
partial phrase match and the one weak point in this question. Everything else
(CLAUDE.md, auto memory, MCP tool names) appears only in the answer, not the
question. **Flag for Day 5:** consider rephrasing to "what is loaded into context
at startup" to remove even that overlap.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q13

**Question:** at what token volume does max become cheaper than the api?

**Type:**
**Source:**
**Answerable:** no
**Gold chunks:** none
**Gold answer:**
**Not covered because:** Verified 2026-08-01 with `search.py --top 20`. The corpus links to the pricing page but states no plan price anywhere. Top hits are `agent-sdk/cost-tracking`, which measures spend rather than comparing plans. No breakeven figure exists in the corpus.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q14

**Question:** starting a project in claude code

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-03:c016`
**Gold answer:** Run `/init`, which walks you through creating a CLAUDE.md for
your project.
**Not covered because:** n/a

**NARROWED on re-verification 2026-08-01.** The previous answer read "Run
`claude` from your project directory, then use `/init` to generate a CLAUDE.md
that captures the project's conventions". Grepping `doc-03:c016` shows neither
"project directory" nor "conventions" appears in it. Two of the three claims were
unsupported by the only chunk cited, which would have scored a retriever against
text that does not exist. Answer cut back to what `c016` actually states.

*Gold answer written by Claude, not the author.*

**Narrowed deliberately.** "starting a project in claude code" could mean
installing, launching, or setting up project configuration. The install reading
duplicates Q01, so this is scoped to the project-setup reading, where `/init` is
the documented entry point.

**Day 5 candidate**, for the same breadth reason as Q10 and Q12. If the intent
was the launch reading, this collapses into Q01 and one of them should go.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q15

**Question:** what are hooks in claude code

**Type:** factual
**Source:** Rewritten 2026-08-01 during labeling. Original was "What are hooks?",
which the corpus answers two incompatible ways. See `private/findings.md`.
**Answerable:** yes
**Gold chunks:** `doc-14:c000`, `doc-14:c009`
**Gold answer:** Hooks are user-defined shell commands (also HTTP endpoints or
LLM prompts) that Claude Code executes automatically at specific points in its
lifecycle. They are defined in JSON settings files, keyed by hook event such as
`PreToolUse` or `Stop`.
**Not covered because:** n/a

**Why these two chunks, and not the other obvious ones.** The gold answer makes
three claims, and each chunk earns its place by supporting one the other cannot:

| Claim | Supported by |
|---|---|
| what a hook *is* — shell command / HTTP endpoint / LLM prompt | `doc-14:c000` |
| *when* it runs — automatically, at lifecycle points | `doc-14:c000` |
| *where* it is configured — JSON settings files, keyed by event | `doc-14:c009` |

Applying D5's delete test to the three near-misses:

- **`doc-13:c000`** (hooks-guide) — "Hooks are user-defined shell commands." A
  correct definitional sentence. Delete it: the answer still stands on
  `doc-14:c000`, which is strictly more complete. **Not gold.** This one feels
  wrong and is the rule working as intended.
- **`doc-05:c017`** (best-practices) — adds that hooks are deterministic where
  `CLAUDE.md` is advisory. Genuinely useful, but the gold answer above makes no
  determinism claim, so nothing depends on it. **Not gold.**
- **`doc-28:c000`** (agent-sdk/hooks) — "Hooks are callback functions." A
  different product surface. Correct for the SDK, wrong for Claude Code.
  **Not gold**, and the reason the question needed rewriting at all.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q16

**Question:** does rewind undo edits i made by hand outside claude

**Type:** factual
**Source:** Replaced 2026-08-01. Original said "tools", which spans three
product surfaces with disjoint answers.
**Answerable:** yes
**Gold chunks:** `doc-11:c007`
**Gold answer:** No. Checkpointing only tracks files edited within the current
session, so manual changes and edits from other concurrent sessions are not
captured unless they touch the same files. Symlinked and hard-linked paths are
also skipped on restore, with a `Restored the code, but skipped N files` warning.
**Not covered because:** n/a

*Question and gold answer written by Claude, not the author.*

**Vocabulary check passed.** Question says "rewind", "by hand", "outside claude".
Chunk says "Checkpointing only tracks", "Manual changes you make to files outside
of Claude Code". "outside" is shared but is not a rare term.

Draws on `checkpointing`, which had 10 chunks and zero questions.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q17

**Question:** how many tokens do i get in a 5-hour window on max?

**Type:**
**Source:**
**Answerable:** no
**Gold chunks:** none
**Gold answer:**
**Not covered because:** Verified 2026-08-01 with `search.py --top 20` plus a corpus grep for dollar figures and quotas. `doc-25:c096` documents the `five_hour` rate limit type and a `utilization` fraction, but the underlying token allowance is never published.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q18

**Question:** What is the function between a client MCP and server MCP

**Type:** comparison
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-16:c000`, `doc-16:c075`, `doc-16:c076`
**Gold answer:** Claude Code is normally an MCP **client**: it connects to MCP
servers that expose tools to it. It can also run as an MCP **server** itself with
`claude mcp serve`, communicating over stdin and stdout so another client, such
as Claude Desktop, can use Claude Code's own tools (View, Edit, LS).
**Not covered because:** n/a

*Gold answer written by Claude, not the author.*

**`doc-16:c000` added on re-verification 2026-08-01.** The answer's first claim,
that Claude Code is normally a *client*, was not supported by either originally
cited chunk. `c075` and `c076` document only the server direction; the word
"client" appears in them meaning some *other* application connecting in. The
client role is stated in `doc-16:c000`: "MCP servers give Claude Code access to
your tools, databases, and APIs."

Complements, all three: `c000` establishes the client role, `c075` gives the
command and stdio transport, `c076` states that the server exposes Claude Code's
tools and that the connecting client owns user confirmation.

**This was the most dangerous of the four defects found.** A grep for "client"
returned hits in both chunks, so a shallow check would have passed it. Only
reading what the word referred to showed the claim unsupported.

**Wording note.** The question says "the function between", which is not quite
grammatical. Read as "the difference between". Worth cleaning up on Day 5, but
the intent is unambiguous, so it is labeled rather than flagged.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q19

**Question:** how do we use RAG in claude code

**Type:**
**Source:**
**Answerable:** no
**Gold chunks:** none
**Gold answer:**
**Not covered because:** Verified 2026-08-01. A word-boundary regex for `RAG`
over all 1,637 chunks returns **zero** matches; the 31 substring hits are
artifacts inside "drag" and "storage". `retrieval` appears in exactly one chunk
(`doc-25:c149`) and refers to retrieving a background task's output in the Python
SDK, nothing to do with retrieval-augmented generation. The corpus documents
context management, MCP and skills, but never RAG as a technique.

*Assessment by Claude, not the author.*

**The strongest unanswerable in the set.** Absence is demonstrated by regex over
the whole corpus rather than by a failed search, which is exactly the standard
template rule 5 asks for. The substring-versus-word-boundary distinction is
itself worth keeping: a naive `--find RAG` returns 31 hits and looks like solid
coverage.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q20

**Question:** is claude code dropping the ide extensions?

**Type:**
**Source:**
**Answerable:** no
**Gold chunks:** none
**Gold answer:**
**Not covered because:** Verified 2026-08-01 with `search.py --top 20` plus a grep for roadmap/deprecated/sunset across all 30 docs: zero hits. The docs confirm IDE extensions exist and that `autoInstallIdeExtension` defaults to true. Nothing states future direction.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q21

**Question:** how do we create a skill for the agent

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-12:c006`
**Gold answer:** Make a directory for the skill, for example
`mkdir -p ~/.claude/skills/summarize-changes`, then write a `SKILL.md` inside it
with two parts: YAML frontmatter between `---` markers containing a `description`
that tells Claude when to use the skill, and markdown content with the
instructions Claude follows. The directory name becomes the command you type.
**Not covered because:** n/a

*Gold answer written by Claude, not the author.*

**RELABELED 2026-08-01, after review flagged low confidence.** The first label
was `doc-12:c056` with a gold answer built around installing the `skill-creator`
plugin. That was wrong. Reading all 78 chunks of `doc-12` found `c006`, the
corpus's own step-by-step walkthrough for authoring a skill by hand, which is the
primary documented route. `skill-creator` (`doc-12:c055`/`c056`) is tooling for
*evaluating* an existing skill, not the answer to "how do I create one".

**Why the first label was wrong is worth keeping.** `--find "skill-creator"`
returned three confident-looking hits and I stopped there. The basic answer used
none of the vocabulary I had searched for: `c006` says "Create the skill
directory" and "Write SKILL.md", never "create a skill". Searching by the
mechanism you already have in mind finds chunks that confirm it and misses the
one that would have corrected it.

**Considered and rejected:** `doc-12:c007` is the worked YAML example, and
`doc-12:c013` covers project versus personal skill locations. The gold answer
quotes neither, and `c006` alone supports every claim it makes.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q22

**Question:** how do we check for token usage

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-03:c011`, `doc-03:c013`
**Gold answer:** Run `/context` to see what is using space in the context window.
**Not covered because:** n/a

**NARROWED on re-verification 2026-08-01.** The previous answer added "and what
each part costs". `costs` does not appear in `doc-03:c011` at all, and where it
does appear in `doc-03:c013` it belongs to a different command: "Run `/mcp` to
check per-server costs." The claim was attached to the wrong tool. Removing it
also restores the D5a alternatives relationship, since both chunks now carry the
identical supporting sentence, "Run `/context` to see what's using space."

*Gold answer written by Claude, not the author.*

Alternatives under D5a: both chunks independently state that `/context` shows
what is using space.

**Ambiguity worth noting.** "token usage" could mean context-window occupancy
(`/context`) or spend in dollars (`agent-sdk/cost-tracking`, doc-29). Labeled for
the context reading because the question says "check", not "bill". Q29 covers the
reduction side. If the author meant cost, this needs relabeling.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q23

**Question:** how do we switch between models in the cli

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-03:c002`, `doc-07:c015`
**Gold answer:** Use the `/model` command to switch models mid-session.
**Not covered because:** n/a

**These two are alternatives, not complements.** Each states the answer on its
own, so under D5a both are gold and retrieving either one serves the user. This
is the question that forced the D5a amendment: applied chunk-by-chunk the
original delete test made both non-gold and left an empty set.

**Deliberately excluded, though tempting:**

- `doc-08:c029` (cli-reference) — the `--model` flag. Sets the model *at launch*,
  which is not switching mid-session, and the gold answer makes no claim about
  aliases. Also a 221-token table chunk that is mostly `--mcp-config` and
  `--name`; only one row is relevant. Worth revisiting as a precision example.
- `doc-19:c023` (headless), `doc-12:c024` (skills), `doc-15:c091` (sub-agents) —
  each mentions `/model` while documenting something else.

**The page that should have answered this is not in the corpus.** Nine chunks
link to `/docs/en/model-config`, and it is not one of the 30 fetched pages. The
question stays answerable because `doc-03:c002` covers it, but the canonical
source is absent — a Day 1 selection gap found on Day 4, not a retrieval fault.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q24

**Question:** how to pick up a previous session after restarting claude code after settings

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-03:c010`
**Gold answer:** Reopen it with `claude --continue` or `claude --resume`, which
restore the session under the same session ID and append to the existing
conversation. `--fork-session` or `/branch` copies the history into a new session
instead.
**Not covered because:** n/a

*Gold answer written by Claude, not the author.*

Single gold chunk: `doc-03:c010` states the resume commands, the same-session-ID
behavior, and the forking contrast in one place, so nothing else is necessary.

**Question wording is garbled.** "after restarting claude code after settings"
has a trailing clause that does not parse. The resume intent is clear enough to
label; flag it for a Day 5 cleanup.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q25

**Question:** how do i stop repeating the same setup instructions to claude every time

**Type:** procedural
**Source:** Reworded 2026-08-01 to reduce the `doc-03` concentration.
**Answerable:** yes
**Gold chunks:** `doc-06:c001`, `doc-06:c003`
**Gold answer:** Put them in a CLAUDE.md. Claude Code has two complementary
memory systems, both loaded at the start of every session. Keep CLAUDE.md to
facts Claude should hold every time: build commands, conventions and project
structure.
**Not covered because:** n/a

*Reworded by Claude. Original question ("how do i implement workflow guidelines
and instructions to claude code") resolved to `doc-03:c016`, the same chunk as
Q26, making the two perfectly correlated.*

Complements: `doc-06:c001` establishes that memory loads at session start,
`doc-06:c003` says what belongs in the file.

Moves this question off the `how-claude-code-works` summary page and onto
`memory` (37 chunks), which had no coverage.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q26

**Question:** how do we scan for the health of claude's environment

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-03:c016`
**Gold answer:** Run `/doctor`, which performs a setup checkup that diagnoses
installation and configuration problems and can fix them.
**Not covered because:** n/a

*Gold answer written by Claude, not the author.*

See the correlation note on Q25: both questions resolve to `doc-03:c016`.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q27

**Question:** who is liable if claude writes a security bug that leaks data?

**Type:**
**Source:**
**Answerable:** no
**Gold chunks:** none
**Gold answer:**
**Not covered because:** Verified 2026-08-01 with `search.py --top 20` plus a grep for liability/indemnify/warranty/'at your own risk'/'you are responsible': zero hits. The corpus is purely technical. Top hits are hooks and permissions chunks about controlling access, not accountability.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q28

**Question:** how far back can i rewind and does it survive a restart

**Type:** factual
**Source:** Replaced 2026-08-01. Original had two readings, only one covered.
**Answerable:** yes
**Gold chunks:** `doc-11:c001`
**Gold answer:** Every prompt creates a checkpoint and Claude Code keeps file
snapshots for the 100 most recent in a session. Checkpoints are saved with the
conversation, so `/rewind` still works after you resume. They are deleted along
with sessions after 30 days, configurable via `cleanupPeriodDays`.
**Not covered because:** n/a

*Question and gold answer written by Claude, not the author.*

**Vocabulary check passed.** Question says "how far back", "survive a restart".
Chunk says "100 most recent checkpoints", "after you resume a session", "30
days". The numbers that make the answer correct appear nowhere in the question.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q29

**Question:** what can i do before a long session summarises itself

**Type:** procedural
**Source:** Sharpened 2026-08-01. Original ("strategies to keep token usages
low") was broad and resolved to the summary page.
**Answerable:** yes
**Gold chunks:** `doc-09:c063`
**Gold answer:** Three things: run `/compact` with a focus, like
`/compact focus on the auth bug fix`, so the summary keeps what you choose rather
than what the automatic pass guesses; run `/clear` when switching to unrelated
work; and delegate large reads to a subagent so file contents stay in its context
window rather than yours.
**Not covered because:** n/a

*Sharpened by Claude, not the author.*

**Why this is better than the original.** "strategies to keep token usages low"
landed on `doc-03:c012`, a summary-page chunk, and was broad enough that several
chunks could have qualified. This version names a specific moment (before
automatic compaction) and has one chunk that lists exactly three actions, so the
gold set is unambiguous.

**The dedicated page is still missing.** `costs#reduce-token-usage` is linked
from the corpus and was never fetched. This question is answerable only because
`context-window` restates the guidance.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q30

**Question:** what can i use to make sure that code being written is safe and bug free?

**Type:** procedural
**Source:**
**Answerable:** yes
**Gold chunks:** `doc-12:c002`, `doc-05:c032`
**Gold answer:** Use the bundled `/code-review` and `/verify` skills, which run
only when you invoke them. You can also add an adversarial review step: have a
subagent review the diff in a fresh context and report gaps before treating the
task as done.
**Not covered because:** n/a

*Gold answer written by Claude, not the author.*

**RELABELED 2026-08-01. The first label was internally inconsistent.** It cited
`doc-05:c019` while the gold answer described the adversarial-review tip, which
is not in `c019` at all. `c019` is a worked example of a `security-reviewer`
subagent definition; the tip lives at the tail of `doc-05:c032`. The label and
the answer pointed at different chunks, which is the kind of error that only
shows up when someone reads both.

Alternatives under D5a: `doc-12:c002` names the bundled review skills,
`doc-05:c032` gives the adversarial-subagent route. Either alone answers "what
can I use".

**Note `doc-05:c032` now serves two questions** (this and Q06), on different
content: its body is about auto mode, its closing tip is about adversarial
review. Legitimate, but it makes Q06 and Q30 share a retrieval outcome, so treat
them as correlated in Day 11's bootstrap.

**Considered and rejected:** deterministic enforcement via hooks (`doc-13`). The
gold answer makes no claim about guaranteed execution, so nothing depends on it.

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

# Day 4 corpus gaps

Found while labeling, not while fetching. Six pages are linked from inside the
corpus but are **not** among the 30 fetched, so the canonical answer to several
questions exists upstream and was never captured:

| Missing page | Questions it would have answered |
|---|---|
| `model-config` | Q23 (switching models) |
| `permission-modes` | Q06, Q07, Q08 (when to use each mode) |
| `costs` | Q29 (reducing token usage) |
| `commands` | slash-command questions generally |
| `statusline` | Q28, second reading |
| `sandboxing` | Q06, adjacent |

Every affected question stayed answerable because another page happened to
restate the material, except **Q07**, which did not.

The corpus is frozen, so this is documented rather than fixed. It belongs in the
README as a limitation with a date: page selection on Day 1 was made by reading
titles, and the gap only became visible once questions were labeled against the
text. Selecting a corpus by browsing and validating it by labeling are different
activities, and only the second one finds this.

---

# Tally

Fill this on Day 5, before you compute anything.

Filled 2026-08-01 at the end of Day 4. The last two rows are counted, not
estimated.

| Check | Target | Actual |
|---|---|---|
| Questions written | 30 | **30** |
| Marked unanswerable | 5 | **6** — over target, see below |
| Multi-hop (2+ gold chunks) | 3+ | **11** of 24 answerable |
| Questions sharing 3+ rare words with their own gold chunk | 0 | **not yet checked** — Day 5 |
| Questions rewritten | count | **7** |
| Questions whose gold label was revised | count | **6** |

**Unanswerable is 6, not 5.** Q19 (RAG) is the extra: a word-boundary regex over
all 1,637 chunks returns zero hits. Accept 6 or rewrite Q19 on Day 5.

**Multi-hop distribution:** 13 answerable questions have one gold chunk, 11 have
two or more. Q04 has four, three of which are interchangeable pipe demonstrations
and will depress its recall to 0.25 even when the user is fully served. Flagged
on that entry.

**The 7 rewrites, all on Day 4 rather than Day 5**, because labeling exposed the
problems before the re-read pass could:

| Q | Why |
|---|---|
| Q07 | named an "edit mode" that does not exist |
| Q09 | no documented referent for "needs to use dependencies" |
| Q12 | turned on "unique", a comparison the corpus never makes |
| Q16 | "tools" spans three product surfaces with disjoint answers |
| Q28 | two readings, only one covered |
| Q25 | reworded to break a shared-chunk collision with Q26 |
| Q29 | sharpened off the summary page onto `context-window` |

**The 6 revised labels** are Q08, Q14, Q18, Q21, Q22, Q30, all found by a
verification pass that checked each gold answer's claims against the `text_raw`
of every chunk it cited. That is a **25% defect rate** on 24 first-pass labels.
Details per entry and in `private/findings.md`.

**Known correlations for Day 11.** The bootstrap assumes questions are
independent draws. These pairs are not: Q14 and Q26 both resolve to
`doc-03:c016`; Q06 and Q30 both cite `doc-05:c032`, on different parts of it. Two
pairs out of 24 is tolerable. More would not be.

**Page coverage: 15 of 30.** Deliberate. The set reflects questions actually
worth asking, not the shape of the corpus. Forcing 30/30 would mean writing
questions *from* pages, which is how vocabulary leaks get built in.

The last two rows go in the README. How many labels you revised is a credibility
signal, not an embarrassment. A gold set nobody revised is a gold set nobody
re-read.

# Averages

Across the 25 answerable questions only.

| Metric | Mean |
|---|---|
| recall@3 | |
| recall@10 | |
| precision@3 | |
| MRR | |

**Answerable questions where no gold chunk appeared in the top 10:** ___ / 25

That count is your ceiling. No amount of prompt work on a generator fixes a
question whose evidence was never retrieved.

**Unanswerable questions correctly declined:** ___ / 5
