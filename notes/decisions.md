# Decisions — Day 1, corpus

Four calls made on 2026-07-29. Each one changes downstream numbers, so each one
is written down with what it costs. "I hadn't thought about it" is the bad
answer; either choice is defensible if the reasoning is here.

---

## D1 — Freeze the corpus with a content hash, not a date

**Decision.** `corpus/INDEX.md` records a sha256 over all 30 doc files in
`PAGES` order. Before trusting any metric, re-run `fetch_corpus.py` and check
the hash still matches.

**Why this isn't paranoia.** I fetched the same 30 pages twice, about 24 hours
apart (28 Jul 23:51 and 29 Jul). **14 of 30 pages changed size in between:**

| Page | Before | After | Delta |
|---|---:|---:|---:|
| `headless` | 22,807 | 26,099 | +3,292 |
| `sub-agents` | 92,552 | 94,952 | +2,400 |
| `hooks` | 240,312 | 242,072 | +1,760 |
| `settings` | 271,213 | 272,476 | +1,263 |
| `how-claude-code-works` | 19,329 | 20,221 | +892 |
| `skills` | 73,113 | 73,820 | +707 |
| `agent-sdk/cost-tracking` | 17,979 | 18,558 | +579 |
| `quickstart` | 13,570 | 13,115 | **−455** |
| `permissions` | 60,703 | 60,808 | +105 |
| `mcp` | 80,789 | 80,849 | +60 |
| `checkpointing` | 8,078 | 8,108 | +30 |
| `hooks-guide` | 62,429 | 62,452 | +23 |
| `agent-sdk/custom-tools` | 41,395 | 41,402 | +7 |
| `output-styles` | 9,911 | 9,909 | **−2** |

Total 1,778,125 → 1,788,786 chars (+10,661) in one day.

`quickstart` and `output-styles` got *smaller* — content was deleted, not just
appended. If a gold chunk had pointed into deleted text, that label would now be
silently wrong, and recall@3 would drop for a reason that has nothing to do with
the retriever.

**Consequence.** These docs are live and change on a daily cadence. Any gold
label is only valid against a specific snapshot. The frozen snapshot is
`a887366bab9778b59129493073c38a116d55ff8e6657b191be1f9d5678473737`.

**Cost.** The corpus goes stale relative to the real docs. Accepted — this is a
measurement project, not a product. A reproducible wrong-in-the-same-way corpus
beats an unreproducible current one.

---

## D2 — 30 Claude Code pages; dropped the 6 API-platform pages

**Decision.** All 30 pages come from `code.claude.com/docs/en/`. The starter
list of candidate pages also included 6 from
`platform.claude.com/docs/en/` (`intro`, `get-started`, tool-use, agent-skills,
mcp-tunnels). Those were dropped and replaced with 6 more Claude Code pages:
`checkpointing`, `plugins`, `worktrees`, `output-styles`, `agent-sdk/python`,
`agent-sdk/cost-tracking`.

**Why.** The binding constraint on this whole project is being able to write and
verify gold answers, and that requires actually knowing the page. I've used
Claude Code daily; I have not worked with the Messages API directly. A gold
label I can't defend is worse than no label, because it enters the metric with
full weight and quietly corrupts it.

**Cost — and this one is real.** The API pages were suggested specifically to
create *cross-source confusion*: two domains that both document "MCP" and
"skills" in different senses, so a retriever can plausibly return the right
concept from the wrong product. That's a genuinely interesting failure mode and
I've given it up. Partial mitigation: `mcp` and `agent-sdk/hooks` vs `hooks`
still overlap heavily within Claude Code, so near-duplicate confusion is
available in-corpus even without the second domain.

If the corpus is ever unfrozen for a v2, adding those 6 back is the first change
to make. `API_BASE` is still defined in `fetch_corpus.py` for that reason.

---

## D3 — Keep the three oversized pages; report per-doc chunk counts

**Decision.** `settings` (272K), `hooks` (242K), and `agent-sdk/python` (194K)
are **40% of the corpus** between them. `checkpointing` is 8K — a 34x spread.
The initial plan said drop them or note them. Keeping all three.

**Why keep.** `settings` and `hooks` are two of the pages real users have the
most questions about. Dropping them to tidy the size distribution would mean
dropping the questions I'm best placed to write gold answers for, which trades a
real problem (bad labels) for a cosmetic one (uneven histogram).

**Why this is dangerous anyway.** Chunk count scales with characters, so these
three will produce ~40% of all chunks. Two distinct effects to keep separate:

1. A big page has more chances to land in top-k *by luck*, inflating apparent
   recall if I'm careless about what counts as a hit.
2. Aggregate metrics get dominated by these pages, so a retriever that's
   excellent on `settings` and useless on the 8K pages can still post a decent
   mean.

**Mitigation, starting Day 2.** Report per-doc chunk counts next to every
aggregate metric, and on Day 8 check whether the 5 worst questions cluster on
small pages. If they do, the story is skew, not retrieval quality.

---

## D4 — MDX: keep the corpus raw, transform selectively at chunk time

This is the call most likely to be challenged, so the reasoning
matters more than the answer.

**What's actually in there.** 467 component tags across the 30 pages:

| Tag | Count | | Tag | Count |
|---|---:|---|---|---:|
| `<Step ` | 111 | | `<Warning>` | 29 |
| `<Note>` | 99 | | `<Accordion ` | 20 |
| `<Tip>` | 71 | | `<Tabs>` | 11 |
| `<Tab ` | 34 | | `<Card ` | 10 |
| `<Steps>` | 33 | | `<Info>` | 8 |
| `<CodeGroup>` | 31 | | `<AccordionGroup>` | 5 |

Plus raw `<div>` and `<span>` from embedded HTML blocks.

**Decision, part 1 — the stored corpus stays byte-identical to what the server
returned.** No stripping at fetch time. Two reasons: the D1 hash has to
fingerprint real upstream bytes to be worth anything, and any transform I apply
later stays reproducible from raw. Cleaning at ingest is a one-way door.

**Decision, part 2 — the Day 2 chunker transforms per-tag, not wholesale:**

| Tag | Treatment | Why |
|---|---|---|
| `<Tabs>` / `<Tab title="npm">` | flatten to `Alternative (npm): …` | **Load-bearing.** These are mutually exclusive options |
| `<Steps>` / `<Step title="…">` | flatten to numbered list | **Load-bearing.** Order is meaning |
| `<Accordion title="…">` | keep title as a heading, unwrap body | Title is often the question a user would ask |
| `<Note>` `<Tip>` `<Warning>` `<Info>` | drop tag, keep body text | Presentational emphasis only |
| `<CodeGroup>` | drop tag, keep fenced code | Fences already delimit the code |
| `<Card>` `<CardGroup>` `<Frame>` | drop tag, keep body | Layout |
| `<div>` `<span>` | drop tag and attributes | Pure layout, zero semantic content |

**Why not keep the tags verbatim.** `<Note>` appears 99 times and `<Step` 111
times. No user query contains the token "Note" in that sense, so these tokens
add signal on the document side that can never be matched on the query side.
They act as a near-constant component across every vector, which compresses the
usable range of cosine similarity and makes ranking mushier — worst exactly
where the corpus is densest in components.

**Why not blanket-strip either.** Strip `<Tabs>` naively and three mutually
exclusive install methods concatenate into what reads like one sequential
procedure. A chunk that says "run the npm install, then the Homebrew install,
then the native install" is not noisy — it is **wrong**, and if it's retrieved
and cited it will assert something false. That's a correctness bug wearing a
preprocessing costume, which is why this one is worth 40 lines of chunker code
rather than a regex that deletes every `<[A-Z]\w+>`.

**Cost.** Meaningfully more chunker code than `re.sub()`, and each rule is a
place a bug can hide. Mitigation: unit-test the `<Tabs>` and `<Steps>` cases
specifically on a real page — `quickstart` has both — since those are the two
rules where being wrong changes meaning rather than just adding noise.

**Falsifiable prediction, to check on Day 8.** If the tag noise argument is
right, questions about pages densest in components (`hooks-guide`, `skills`)
should improve most versus a keep-tags-verbatim variant. If they don't, this
decision was cargo-culted and D4 needs rewriting. That's a Phase 2 ablation,
not a Day 2 one.

---

## D5 — A chunk is gold only if the answer is impossible without it

Made 2026-08-01, before labeling any of the 25 answerable questions. Deciding
this *after* labeling would mean the rule got fitted to the labels.

**Decision.** Strict / necessary inclusion. A chunk is gold if and only if:

> Delete this chunk from the corpus. Is the gold answer still fully supported by
> the remaining gold chunks? If yes — **not gold.**

Applied identically to all 25. Not re-litigated per question.

**The case that forced the choice.** *"How do I stop Claude asking me before
every single file edit?"* The chunker split the permission-modes table:

| Chunk | Contents | Gold? |
|---|---|---|
| `doc-02:c008` | `Shift+Tab` cycles modes; `acceptEdits` auto-approves edits | yes |
| `doc-10:c005` | table header + the `acceptEdits` row | yes |
| `doc-10:c006` | continuation rows: `auto`, `dontAsk`, `bypassPermissions` | **no** |

`doc-10:c006` is a genuinely hard call. `bypassPermissions` reads "Skips
permission prompts", which *does* stop the asking. It fails the test anyway: the
answer is complete with `c005` alone, so `c006` is an alternative route, not a
requirement.

**Why strict over contributory.** The loose rule ("contains anything a correct
answer would draw on") has no natural stopping point. Under it, Q12 ("key
features unique to claude code") and Q14 ("starting a project") could each
justify 15 chunks, and by question 19 the working definition has quietly drifted
to "on topic". A rule that drifts isn't a rule — and it drifts in the direction
that flatters the numbers, because bigger gold sets make recall@10 easier to
satisfy by accident.

**Cost — and it's a real one.** Strict labels understate recall in a specific
way. If retrieval returns `doc-10:c006` at rank 2, that scores as a miss even
though a generator handed that chunk could answer the question. So the recall
numbers are a **lower bound**, not a point estimate. Say that in the README
rather than letting a reader assume otherwise.

### D5a — amendment, same day: the delete test scores the SET, not each chunk alone

Q23 broke the rule as originally written, about an hour after it was written.

**The break.** Q23 is "how do we switch between models in the cli", gold answer
"use `/model` to switch mid-session". Two chunks support that independently:
`doc-03:c002` ("Switch with `/model` during a session") and `doc-07:c015` ("use
`/model` to switch mid-session"). Applying the delete test chunk by chunk:
remove either and the answer survives on the other, so *neither* is necessary,
so the gold set is empty. The question is plainly answerable. The rule was
wrong, not the question.

**The amendment.** The delete test asks whether a *candidate set* is minimal and
sufficient — it is not applied to chunks one at a time in isolation. When two or
more chunks are **mutually redundant** (each independently sufficient), they are
**alternatives**, and all of them are gold. Retrieving any one is a success for
the user, so all of them must be able to count as a hit.

This is the same principle already in the gold template's rule 4 about the four
byte-identical duplicate groups, generalised: rule 4 covers chunks with identical
*text*, D5a covers chunks with equivalent *content*.

**Consequence for the metric, and it is not cosmetic.** Recall is
`|retrieved ∩ gold| / |gold|`. With two alternatives and one retrieved, recall
scores 0.5 even though the user got a complete answer. Recall therefore
understates performance on every alternatives-style question — on top of the
lower-bound effect D5 already documents.

**Not fixing this with a new metric.** The plan already computes MRR and
first-relevant-rank, and those capture exactly what recall misses here: how
quickly *some* sufficient chunk arrived. Read them together. A question with
recall@10 = 0.5 and first-relevant-rank = 1 was answered well; the same recall
with first-relevant-rank = 9 was not. Introducing a separate success@k would add
a fourth metric to explain in the README to say something MRR already says.

**Say this in the README.** A gold set where every label is independent is easy
to score and rare in practice. Documenting that alternatives exist, and that
recall understates them, is more honest than a clean number that hides it.

**Consequence for Day 8.** Some "failures" will be near-misses of exactly this
kind. Read the retrieved text before classifying any failure as a retrieval
error; the failure taxonomy needs to separate R1 (nothing relevant retrieved)
from a strict-labeling artifact. Rejected recording a `Near miss:` field per
question — it's 25 extra judgements to serve one day of analysis, and Day 8 can
recover the same information by reading the top 10 for the handful of questions
that actually score badly.

---

## Housekeeping

`~/corpus/` holds the first (28 Jul) fetch — slug-named files under `pages/`,
plus `index-raw.txt` and `pages.txt`. It is **superseded** by
`rag-eval-practice/corpus/` and does not match the frozen hash. Left in place
rather than deleted; don't read from it.
