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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q07

**Question:** when to use edit mode in claude code

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q09

**Question:** when does claude code need to use dependencies

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Question:** what are some key features unique to claude code

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q15

**Question:** What are hooks?

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q16

**Question:** How to build tools in claude code

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q25

**Question:** how do i implement workflow guidelines and instructions to claude code

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Question:** how can i improve claude code's ui/ux design

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q29

**Question:** what are some strategies i can use to keep token usages low

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

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

**Type:**
**Source:**
**Answerable:**
**Gold chunks:**
**Gold answer:**
**Not covered because:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

# Tally

Fill this on Day 5, before you compute anything.

| Check | Target | Actual |
|---|---|---|
| Questions written | 30 | |
| Marked unanswerable | 5 | |
| Multi-hop (2+ gold chunks) | 3+ | |
| Questions sharing 3+ rare words with their own gold chunk | 0 | |
| Questions rewritten on Day 5 | count | |
| Questions whose gold label you changed your mind about | count | |

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
