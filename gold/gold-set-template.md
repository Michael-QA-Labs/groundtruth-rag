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
**Gold chunks:** `doc-08:c000`, `doc-01:c011`, `doc-04:c016`, `doc-05:c028`, `doc-19:c008`
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
| ask for JSON with `--output-format json` | `doc-05:c028`, `doc-19:c008`, alternatives under D5a |

**`doc-19:c008` added by the D5a sweep, 2026-08-05.** It documents the flag in
prose rather than using it in passing: "To get output conforming to a specific
schema, use `--output-format json` with `--json-schema`", followed by a worked
extraction example on the same page as the `claude -p` surface the gold answer
uses. That is the bar this entry already set when it rejected `doc-08:c026`.

**This makes the recall problem below worse, not better, and it is still
correct.** Five gold chunks now, so a retriever that returns one sufficient
chunk scores 0.20. The label describes the corpus; the metric's discomfort with
that is a fact about recall, not a reason to under-label.

**`doc-19:c010` rejected.** It is the code continuation of `c008`'s example and
its own prose documents `--output-format stream-json`, a different flag. Same
ruling as `doc-08:c026`.

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

**`doc-26:c023` found by the D5a sweep and REJECTED, 2026-08-05. The strongest
candidate the sweep produced anywhere, and the rejection is the finding.** It
says: "A bare tool name such as `"Bash"` removes the tool from Claude's context,
the same as omitting it from `tools`. A scoped rule such as `"Bash(rm *)"`
leaves the tool in context and denies only matching calls." That asserts both of
this answer's claims outright, more cleanly than most accepted alternatives in
the set.

It is rejected because it documents the **Agent SDK's** `disallowedTools`, while
the gold answer describes Claude Code's `permissions.deny`. Same behavior,
different product, different configuration file.

**What the rejection protects is worth more than the label.** No gold chunk
anywhere in this set comes from an `agent-sdk/*` page, and those are 7 of the 30
pages and 363 of the 1,637 chunks. So an SDK chunk in the top 10 of any of these
30 questions is a surface confusion *by construction*, and Day 8 gets that
failure category counted for free. Accepting this one chunk would make one SDK
chunk a correct answer and force every future SDK hit to be adjudicated by hand.
That trades a standing measurement for one alternative on one question.

**Q15 already settled that surface is material**, when Claude Code hooks turned
out to be shell commands and Agent SDK hooks callback functions. That these two
surfaces happen to agree about tool blocking is a coincidence, not a principle.
A rule of "cross-surface counts when the behavior coincides" has to be
adjudicated per chunk and manufactures contested labels.

**If a later version wants SDK coverage**, write SDK questions deliberately.
Backfilling one SDK chunk into a CLI question is not coverage.

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

**Near miss, not gold: `doc-06:c035`.** Found by the D5a sweep, 2026-08-05. It
says "Project-root CLAUDE.md survives compaction: after `/compact`, Claude
re-reads it from disk and re-injects it into the session", which is this answer's
first claim, and nothing about unscoped rules, auto memory, the system prompt or
the output style. Not sufficient for the answer, so not an alternative under
D5a/D5b. The chunk agrees: it closes by pointing at "What survives compaction",
the section `doc-09:c061` comes from, for "the full breakdown".

**Expect this at rank 1 or 2 on Day 8.** If it appears and scores as a miss, that
is the D5 lower-bound effect, not a retrieval failure. The user would have been
told yes, their project rules survive.

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

**KEPT on the Day 5 review, 2026-08-05, with the breadth recorded rather than
fixed.** The label is correct: `doc-02:c011` supports both claims the gold answer
makes, near-verbatim. What is not correct is the question, and no label can fix
that.

**Read a low score here as breadth, not as retrieval failure.** The corpus
answers this across a page, so several chunks would leave a user genuinely
served while scoring zero. `doc-03:c017` is the clearest: "Be specific upfront.
The more precise your initial prompt, the fewer corrections you'll need.
Reference specific files, mention constraints, and point to example patterns."
That is real prompting advice and it supports nothing this gold answer claims,
so under D5 it is an alternative route and stays out, the same ruling D5 gives
`doc-10:c006`. See D5b.

**What that means for Day 8.** If this question scores badly, check what came
back before writing it up as a retrieval miss. A near-miss here is a property of
a question with no determinate answer, and the honest fix is a narrower question
in a v2 gold set, not a bigger gold set now.

**Why not rewritten.** Rewriting costs a re-label and buys a cleaner number on a
question that has no vocabulary leak and a correct label. Documenting the
weakness is worth more than hiding it, and one question whose ceiling is set by
its own breadth is a fact about this gold set that the README should carry.

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
**Gold chunks:** `doc-03:c016`, `doc-05:c010`, `doc-06:c006`
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

**RE-LABELED on the Day 5 re-read, 2026-08-04. Two alternatives were missing.**
D5a says mutually redundant chunks are all gold, and `/init` is documented three
times in the corpus, each time sufficiently:

| Chunk | What it states alone |
|---|---|
| `doc-03:c016` | "`/init` walks you through creating a CLAUDE.md for your project" |
| `doc-05:c010` | "Run `/init` to generate a starter CLAUDE.md file based on your current project structure" |
| `doc-06:c006` | "Run `/init` to generate a starting CLAUDE.md automatically. Claude analyzes your codebase and creates a file..." |

**`doc-05:c011` deliberately excluded, and it is the closest call in the set.**
It says "the `/init` command analyzes your codebase to detect build systems, test
frameworks, and code patterns, giving you a solid foundation to refine", and it
opens by defining what CLAUDE.md is. A reader joins those. But the chunk never
states that `/init` produces a CLAUDE.md, and the delete test asks what the chunk
supports, not what an attentive reader can infer beside it. Revisit if the Day 8
failure analysis lands on this question.

**What this costs.** Gold went from 1 chunk to 3, so retrieving `doc-03:c016` at
rank 1 and nothing else now scores recall 0.33 rather than 1.0, on a question the
user would consider fully answered. Same D5a effect flagged on Q04. Read it
against first-relevant-rank.

**This also breaks the Q26 correlation**, which was the reason the question was
flagged. That was a side effect, not the motive: the label was wrong under a rule
written on Day 4, and would have been wrong with no correlation anywhere. The
questions were not rewritten. Rewriting a question to decorrelate a statistic
would be adjusting the instrument to suit the analysis.

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

**Near miss, not gold: `doc-05:c027`.** Found by the D5a sweep, 2026-08-05. It
says "Checkpoints only track changes made through Claude's file editing tools.
Changes made through Bash commands or external processes are not captured",
which answers the question asked and carries this answer's first claim. It says
nothing about symlinked or hard-linked paths, so it is not sufficient for the
answer as written and is not an alternative under D5a/D5b.

**This is the clearest case of the verbosity effect in the set.** Strip the
symlink sentence from the gold answer and `doc-05:c027` becomes a clean
alternative, which would take gold to 2 chunks and halve recall. The answer's
length is doing labeling work, which is a property of the instrument. See D5b.
Not fixed by trimming the answer, because trimming answers to admit alternatives
is fitting the data to the rule.

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

**KEPT on the Day 5 decision, 2026-08-04. The set has 6 unanswerable, not 5.**
Day 4 left this open: accept 6, or rewrite Q19 to hit the target of 5. Keeping
it. The only argument for rewriting was a number chosen on Day 0, before any
question existed, and this is the single best-evidenced unanswerable of the six.
Deleting the strongest one to make a target come out round is the exact move this
project exists to avoid, and it would have to be explained in the README, where
"we removed a question because we had one too many" reads worse than 6.

6 of 30 is a 20% abstention rate, which is a defensible share for measuring
whether a system declines to answer rather than inventing. The target was never
load-bearing: nothing downstream needs 5, both the metric denominators and the
Day 11 bootstrap take whatever number the labeling produced.

**Consequence:** 24 answerable, 6 unanswerable. Metric denominators updated in
the Averages block below, which had been written expecting 25 and 5.

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

**Question:** How do i reinstate or resume a previous claude code session

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

**REWRITTEN BY THE AUTHOR, 2026-08-05.** Was "how to pick up a previous session
after restarting claude code after settings", whose trailing clause did not
parse. Now "How do i reinstate or resume a previous claude code session".
Wording only. **The gold chunk and gold answer are unchanged**, because the
resume reading is what the old label already assumed and the new wording states
it plainly.

**"reinstate" appears on 0 of 30 pages.** The corpus never uses the word, so a
lexical retriever gets nothing from it and a dense one has to bridge to "resume"
on its own. That makes this one of the better retrieval tests in the set, and it
came from the rewrite rather than from any deliberate design. "resume" is on 20
of 30 pages, nowhere near rare, so nothing here is a vocabulary leak either way.

**Two other completions were considered and rejected.**

*"after closing my terminal"* would have kept the same label, but `doc-03:c010`
never says a session survives closing a terminal. It ties sessions to
directories and describes resume. Adding a clause the gold chunk does not
support is the defect that killed Q07 ("edit mode", which does not exist) and
Q12 ("unique", a claim the corpus never makes).

*"after changing my settings"* was the tempting one and is the reason this note
is long. It is answerable, `doc-07:c014` says Claude Code watches settings files
and reloads them so "edits to most keys apply to the running session without a
restart", and it would have added the `settings` page to a corpus coverage of 15
of 30. It was rejected because it carries two defensible readings: "how do I
resume" resolves to `doc-03:c010`, "do I even need to" resolves to
`doc-07:c014`. Both are covered, so a labeler can argue either, and a contested
label cannot be defended. That is the same reasoning that forced the rate-limit
question to be reworded on Day 3.

**Logged as a candidate replacement instead.** "do i need to restart claude code
after changing my settings", gold `doc-07:c014`, answer "no, most keys reload
into the running session". Determinate, adds page coverage, and the answer is
counterintuitive enough to catch a retriever that pattern-matches "restart". It
belongs in a deliberate swap in the Day 4 style, against a weaker question, not
grafted onto this one.

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
**Gold chunks:** `doc-03:c016`, `doc-08:c006`
**Gold answer:** Run `/doctor`, which performs a setup checkup that diagnoses
installation and configuration problems and can fix them. From the terminal
without starting a session, `claude doctor` prints the same diagnostics
read-only.
**Not covered because:** n/a

*Gold answer written by Claude, not the author.*

**RE-LABELED on the Day 5 re-read, 2026-08-04.** `doc-08:c006` in
`cli-reference` documents `claude doctor` as printing "installation and settings
diagnostics from the terminal without starting a session, including install
health, settings-file validation errors, and Remote Control eligibility", and
names `/doctor` as the in-session checkup that can also apply fixes. It answers
the question without `doc-03:c016`, so under D5a it is an alternative and it is
gold. It was missed on Day 4.

**The gold answer gained a sentence** because the CLI form is a genuinely
different way to do the thing asked about, and an answer that omits it would fail
to use half its own evidence.

**Nine other chunks mention `/doctor` and none of them qualify.** `doc-07:c015`
is about listing stripped policy entries, `doc-06:c034` about proposing CLAUDE.md
trims, `doc-12:c002` merely lists it among bundled skills. Each is `/doctor` in
service of a narrower question, not an answer to "is my environment healthy".
Mentioning the command is not the same as documenting the checkup.

**Previously the only shared-chunk collision in the set** (with Q14, both on
`doc-03:c016` alone). Both were under-labeled, and correcting both leaves
`doc-03:c016` as one alternative of two here and one of three there. See the
correlation note in the Tally.

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

**Near miss, not gold: `doc-05:c024`.** Found by the D5a sweep, 2026-08-05. It
carries two of the three limbs, "Use `/clear` frequently between tasks" and "run
`/compact <instructions>`, like `/compact Focus on the API changes`", and not the
third, delegating large reads to a subagent. Not sufficient for the answer, so
not an alternative.

**This question is why "primary claim" sufficiency was rejected.** The answer
opens "Three things:" and the three limbs are co-equal, so there is no primary
claim for a looser rule to be sufficient for. A standard that cannot be applied
here cannot be applied uniformly, which is D5's own objection to contributory
inclusion.

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

**Complements under D5, not alternatives under D5a. Rationale corrected
2026-08-05.** It previously read "either alone answers 'what can I use'", which
is the question-anchored test D5b rules out. The gold answer asserts both limbs:
`doc-12:c002` supports the bundled review skills, `doc-05:c032` supports the
adversarial-subagent step. Delete either and half the answer loses its support,
so each is necessary under plain D5 and D5a never enters. Same chunks, right
reason.

**`doc-05:c019` considered and rejected**, on the D5 rule that excluded
`doc-10:c006` in the permissions case. It defines a `security-reviewer` subagent,
which is a real third route to safer code, and the gold answer does not take it.
An alternative route is not gold.

**One unstated condition in the gold answer.** "Run only when you invoke them" is
true from v2.1.215; `doc-12:c002` says that before it, Claude could run
`/verify` and `/code-review` on its own. The answer states it flatly. Left as is,
because the corpus snapshot is post-2.1.215 and every other answer in the set
describes current behavior, but it is the kind of condition a judge could mark
either way.

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
| Questions sharing 3+ rare words with their own gold chunk | 0 | **0** of 24, checked 2026-08-04 |
| Questions rewritten | count | **8**, being 7 on Day 4 and Q24's wording on Day 5 |
| Questions whose gold label was revised | count | **6** |

**Unanswerable is 6, not 5, and that is now the final count.** Q19 (RAG) is the
extra: a word-boundary regex over all 1,637 chunks returns zero hits. Decided on
Day 5, 2026-08-04: kept. It is the best-evidenced unanswerable in the set, and
the only case for cutting it was a target number written on Day 0. Reasoning on
the Q19 entry.

**Zero vocabulary leaks, and the zero survives the threshold moving.** Counted by
`src/leakage.py`, not by re-reading. Nothing is flagged until "rare" is stretched
to 16 of 30 pages, at which point the word doing the flagging is `outside` and
the definition has stopped meaning anything. Rule and reasoning in
`notes/decisions.md` D6. Re-run 2026-08-05 after the Q14 and Q26 re-labeling:
unchanged at 0 of 24. The rarest shared term in the set is now `health` on 2 of
30 pages, held by Q26, which picked it up along with `doc-08:c006`. One term
against a threshold of three.

**Multi-hop distribution:** 11 answerable questions have one gold chunk, 13 have
two or more, after the Day 5 re-labeling of Q14 and Q26 below. Q04 has four,
three of which are interchangeable pipe demonstrations and will depress its
recall to 0.25 even when the user is fully served. Flagged on that entry.

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
| Q24 | Day 5. Trailing clause did not parse. Wording only, label unchanged |

**The 6 revised labels** are Q08, Q14, Q18, Q21, Q22, Q30, all found by a
verification pass that checked each gold answer's claims against the `text_raw`
of every chunk it cited. That is a **25% defect rate** on 24 first-pass labels.
Details per entry and in `private/findings.md`.

**Day 5 authorship review, 2026-08-05: all 17 answerable Claude-drafted answers
verify, 0 further defects.** 23 of the 30 gold answers were drafted by Claude and
say so inline; 17 of those are answerable and therefore have claims to check.
Every claim traces to a cited chunk, most near-verbatim. Q21 and Q30, the two
carried as lower-confidence since Day 4, are both sound and that flag is cleared.

A second pass finding nothing is weak evidence on its own, since both passes were
run the same way by the same kind of reader. What it does establish is that the
6 defects Day 4 found were actually fixed rather than reworded, and that nothing
new was introduced by fixing them.

**What the review found instead was three defects of a kind the first pass could
not see, because it was checking answers against chunks rather than questions
against themselves:** Q24's wording is garbled and awaits an author rewrite,
Q10's breadth caps its own score no matter what the retriever does, and Q30's
rationale had the wrong rule written into it. Two of the three are properties of
questions, not labels. A verification pass aimed at labels will never find them,
which is the argument for the Day 5 re-read existing as a separate day.

**Author-written throughout:** Q01-Q05, Q15, Q23. This distinction goes in the
README with its counts. Anyone asking which answers were written by hand and
which were drafted by a model should get the number, not a characterization.

**Known correlations for Day 11.** The bootstrap assumes questions are
independent draws. Q06 and Q30 both cite `doc-05:c032`, on different parts of it.
One pair out of 24 is tolerable. More would not be.

**The Q14/Q26 collision is gone, and the fix was a label, not a rewrite.** Both
resolved to `doc-03:c016` alone, which is a single 248-token chunk containing a
two-item bullet list: one line on `/init`, one on `/doctor`. A single retrieval
decided both questions, which is as correlated as two questions can get. The
Day 5 re-read found that both were simply under-labeled under D5a. Q14 has three
independently sufficient chunks, Q26 has two, and `doc-03:c016` is now one
alternative among them rather than the whole answer. Neither question was
touched. Rewriting a question to break a statistical correlation would be
changing the instrument to suit the analysis, and the labels were wrong on their
own terms regardless.

**Systematic D5a sweep run 2026-08-05 with `src/sweep.py`. Yield: 1 addition,
1 rejection, 3 documented near-misses.** Far less than predicted, and the
prediction is worth keeping visible: after Q14 and Q26 both turned out
under-labeled, the expectation was that many of the other 22 would be too.

| Result | Question | Chunk |
|---|---|---|
| Added | Q04 | `doc-19:c008`, documents `--output-format json` in prose |
| Rejected | Q07 | `doc-26:c023`, right behavior, Agent SDK surface. See D7 |
| Near miss | Q09 | `doc-06:c035`, first claim only |
| Near miss | Q16 | `doc-05:c027`, first claim only |
| Near miss | Q29 | `doc-05:c024`, two limbs of three |

**Coverage of the sweep itself, which is not 24 of 24.** The tool searches from
the gold answer's identifiers, so it swept 14 questions and reported the other 10
as unswept rather than clean: 5 whose answers contain no identifier at all, and 5
whose only identifier is something the corpus says everywhere (`CLAUDE.md` is in
108 chunks). Those 10 were probed by hand with phrases chosen per answer. A "no
candidates" line from a check that could not have found anything is the failure
this project already made once, on the leak check's first run.

**Why the yield was low, and it is the interesting part.** All three confirmed
D5a cases in the set (Q14, Q23, Q26) have single-claim answers. Every rejection
in the sweep was a chunk carrying some but not all of a multi-claim answer. Under
whole-answer sufficiency, alternatives essentially only arise for answers that
make one claim, which means gold-set size is partly a function of how much
elaboration the answer carries. Recorded in D5b with the caveat that the
causation is not established.

**Page coverage: 15 of 30.** Deliberate. The set reflects questions actually
worth asking, not the shape of the corpus. Forcing 30/30 would mean writing
questions *from* pages, which is how vocabulary leaks get built in.

The last two rows go in the README. How many labels you revised is a credibility
signal, not an embarrassment. A gold set nobody revised is a gold set nobody
re-read.

# Averages

Across the 24 answerable questions only.

| Metric | Mean |
|---|---|
| recall@3 | |
| recall@10 | |
| precision@3 | |
| MRR | |

**Answerable questions where no gold chunk appeared in the top 10:** ___ / 24

That count is your ceiling. No amount of prompt work on a generator fixes a
question whose evidence was never retrieved.

**Unanswerable questions correctly declined:** ___ / 6
