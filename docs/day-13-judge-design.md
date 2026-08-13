# Day 13: an LLM judge for D5 necessity, and whether it agrees with me

## Context

Phase 2 asks for an LLM judge plus validation: hand-label examples, measure
Cohen's κ. The PLAN calls it the single strongest differentiator and notes it
needs Day 11 solid first. Day 11 is solid.

The repo has no generation step. Every module is retrieval, and nothing produces
a candidate answer. So the judge grades **retrieval relevance**, not answer
quality, and it applies the project's own labeling rule (D5 necessity) rather
than a generic relevance rule. Building a generator is a separate project.

Measurement during design surfaced facts that reshaped the work:

- **Only 18 of the 44 gold pairs appear in the stored top-20 at all.** 26 gold
  pairs are never retrieved. This is the Day 8 weak-retriever finding showing up
  again as a sampling constraint.
- **Gold prevalence among retrieved pairs is 3.8%** (18 of 480). A uniform
  random sample of 100 pairs would contain about four positives, which is not
  enough to compute a κ anyone should believe.
- **Prevalence falls with rank**: 8.3% at ranks 1-3, 4.8% at 4-10, 1.7% at
  11-20. So per-rank-band κ is not affordable at this sample size.
- **Chunks average 1,093 chars** (median 895, p90 1,942), and gold answers
  average 224 chars. A 4-chunk pool plus rubric is about 2,100 input tokens,
  which makes the judge cheap to run and cheap to repeat.

## Three design decisions

### 1. Judge per question, not per pair: pair-level judging is degenerate

D5 necessity is not a property of a chunk. It is a property of a chunk
**relative to the alternatives available**. `doc-10:c006` is the case that
proves it: `bypassPermissions` genuinely does stop the asking, and it is still
not gold, purely because `c005` already suffices.

Judging one (question, chunk) pair in isolation has no good configuration:

| Configuration | Failure |
|---|---|
| Judge sees the gold set alongside the candidate | Every non-gold candidate is trivially unnecessary. The judge scores near-perfectly by answering "not necessary" to anything outside the set handed to it. Measures set membership, not judgment. |
| Judge sees only the candidate | The delete test is unrunnable. The judge cannot know whether something else covers the same claim, so it falls back to "is this on topic", which is the contributory rule D5 exists to reject. |

**Therefore:** the judge sees one question at a time, with the gold answer and a
shuffled pool of candidate chunks, and returns the **minimal subset that fully
supports the answer**. A pair is labeled necessary if and only if its chunk is
in that subset.

This is D5's delete test run mechanically, against real alternatives, with the
near-misses in the pool competing. It also means **both raters perform an
identical task**, which the pair-level design quietly failed to guarantee. κ
between raters doing different tasks is not a reliability measure.

### 2. Sample: 44 gold pairs plus 56 hard negatives

All 44 gold pairs, plus 56 non-gold pairs drawn from what the retriever ranked
in the top 20 for that same question. Prevalence 44%, so κ has stable marginals,
and every negative is a genuine near-miss the retriever thought was worth
returning.

Allocation, deterministic, no RNG:

- Every answerable question gets **2 negatives** (48 total).
- The remaining **8** go one each to the 8 questions with the most gold chunks,
  ties broken by question id, so pools stay proportionate to their gold.
- Negatives are drawn from that question's top-20 minus its gold chunks, seeded
  `20260813`. Only the draw uses the RNG; the allocation does not.
- Pool order is shuffled under the same seed, so position never encodes the
  label.

Every question's full gold set is in its pool, so **every pool is sufficient by
construction** and the minimal-subset question is always answerable.

### 3. Two judges, neither of them tuned

Primary is `claude-opus-5`. Second variant is `claude-haiku-4-5`, run after the
first is complete, on the identical pools with the identical prompt and schema.

This follows D10's discipline: nothing in the second variant is tuned. The
question is "does a judge 5x cheaper agree with me as well as the expensive
one", and tuning Haiku to close a gap would destroy the only interesting answer.

The two models do not accept the same request shape, which matters:

| | `claude-opus-5` | `claude-haiku-4-5` |
|---|---|---|
| Thinking | On by default (adaptive) | `{"type": "enabled", "budget_tokens": N}`, min 1024, must be < `max_tokens` |
| `effort` | Supported, `low` through `max` | **Rejected. Do not send it.** |
| Structured outputs | Supported | Supported |
| Prompt cache minimum | 512 tokens | 4,096 tokens, so the ~700-token rubric **will not cache** |
| Price per Mtok | $5 in / $25 out | $1 in / $5 out |

`budget_tokens` for Haiku is fixed at **2048, chosen before any results are
seen, and not adjusted afterwards**, the same pre-registration discipline D5
used when the labeling rule was fixed before labeling began.

**Admit the confound in the writeup.** Adaptive thinking against a fixed budget
is not a controlled model ablation. What this comparison measures is two judges
configured the way you would actually deploy them, not Opus-versus-Haiku holding
reasoning constant.

## Labeling protocol

Order is load-bearing:

1. Build pools. `judge/pools.json` carries chunk ids, question, gold answer, and
   nothing that marks gold status. The key lives separately in
   `judge/pools-key.json`.
2. **Hand-label all 24 pools first**, into `judge/hand-labels.csv`. 24 screens of
   about 4 candidates, not 100 isolated binary decisions.
3. Commit the labels. `results/agreement.md` records their sha256, and
   `src/agreement.py` refuses to run when the recorded hash does not match the
   file, the way `src/run_retrieval.py` refuses when the gold set and index
   disagree on the corpus hash.
4. Only then run the judge.

The hash gate makes it checkable, not merely claimed, that the hand labels
predate the judge output.

**What blindness does not buy here.** You wrote the gold set, and Day 5 reviewed
it. Fresh labels are contaminated by memory of your own decisions eleven days
ago. κ against the Day 3-5 labels is therefore an *upper bound biased upward*,
not a clean test-retest. Say so where the number appears.

## Measurement

| κ | Raters | Role |
|---|---|---|
| κ_ceiling | Day 3-5 gold vs fresh hand labels | **Primary context.** Human self-consistency. Not a mathematical bound on the others, but a judge scoring near or above it is evidence the rule is ambiguous, not that the judge is good. |
| κ_opus | Fresh hand labels vs Opus majority vote | **Headline.** |
| κ_haiku | Fresh hand labels vs Haiku majority vote | Second variant. |
| κ_models | Opus vs Haiku | Do the judges agree with each other more than either agrees with you? |
| Run-to-run | Run i vs run j within one model | Reproducibility. |

Each model runs the 24 pools **3 times**. Majority vote across runs gives the
label used for the headline κ; the spread across runs is the reproducibility
number. This exists because the judge is the first non-deterministic component
in a repo where the corpus, the vectors, and the dependency set are all pinned.

Intervals reuse `src/stats.py`. The cluster bootstrap clusters on **question**,
for the same reason Q06 and Q30 were clustered on Day 11: pairs from one pool
are not independent.

**Expect wide intervals and plan for them.** 100 labels across 24 clusters is
24 effective units. Report κ with its interval, never alone, and do not let a
point estimate become the finding. The sample size has been the binding
constraint before, and it is the binding constraint again here; that recurrence
is worth stating plainly rather than rediscovering.

κ is hand-computed on a small table first and pinned in a test, the way Day 6
preceded Day 7.

## Implementation

### Files

| Path | Contents |
|---|---|
| `src/build_judge_pools.py` | Deterministic sampler. Pure, seeded, no network. |
| `src/judge.py` | `build_request(pool)` and `parse_response(raw, pool)` are pure; a thin `main` does the I/O. |
| `src/agreement.py` | κ, the bootstrap intervals, the hash gate. |
| `judge/pools.json` | 24 pools, shuffled, no gold markers. |
| `judge/pools-key.json` | Gold status per pair. |
| `judge/hand-labels.csv` | Your labels. |
| `results/judge-opus-5.json` | Raw responses plus parsed labels, 3 runs. |
| `results/judge-haiku-4-5.json` | Same, second variant. |
| `results/agreement.md` | The writeup. |
| `notes/decisions.md` | D12, D13, D14. |

Raw responses are written to disk so `agreement.py` never touches the network.
Re-running the analysis is instant.

### Response schema

Structured outputs, `strict: true`, `additionalProperties: false`. The
`chunk_id` fields are an **enum built from that pool's ids**, so a hallucinated
id is a schema violation rather than a silent data error.

```
{
  "minimal_set": ["doc-02:c005", ...],
  "rationale": [{"chunk_id": ..., "required": bool, "why": "one sentence"}]
}
```

`minimal_set` is authoritative for labels. `rationale` exists so disagreements
can be read chunk by chunk, in the Day 8 tradition. When `rationale.required`
contradicts `minimal_set`, `minimal_set` wins **and the contradiction is logged
as a judge-consistency defect**, because that is itself a result.

### Decisions to record

- **D12**: why the judge runs per question and not per pair, with the
  degeneracy argument and the `c006` case.
- **D13**: sample construction, the 3.8% prevalence that forced it, and the
  admission that a balanced sample does not estimate deployment κ.
- **D14**: judge configuration, the pre-registered Haiku budget, the unmatched
  variants, and the reproducibility problem below.

## Verification

Tests never touch the network. Fixtures are recorded real responses, checked in.

Beyond the happy path, tests exist to catch errors that return plausible
numbers, the way `test_stats.py` does:

- A κ that is silently raw agreement. (The classic bug. Pin a hand-computed
  table where the two differ substantially.)
- κ of a rater against itself must be exactly 1.0.
- A parser that silently drops chunks absent from the pool, or accepts an id
  outside it.
- A sampler that leaks gold position through pool ordering. (Shuffle must be
  seeded and asserted.)
- A majority vote that silently fills in a missing run. With 3 runs and binary
  labels a tie is impossible, so a tie can only mean a run failed or returned an
  invalid response. That case must surface, not be voted away.

Each of these gets mutation-checked: break the implementation deliberately,
confirm the test fails.

## Scope and sequencing

1. Sampler plus tests. Pools built and committed.
2. Hand-label 24 pools. Commit, record hash.
3. Opus 5 judge, 3 runs. Raw output committed.
4. κ, intervals, `results/agreement.md`.
5. Haiku 4.5, 3 runs, on the identical pools. Comparison appended.

Steps 1 to 4 are the deliverable. Step 5 is the experiment.

### Cost

72 calls per model (24 pools × 3 runs). About 2,100 input tokens per call and an
estimated ~2,750 output-plus-thinking tokens.

| | Input | Output | Total |
|---|---|---|---|
| Opus 5 | $0.76 | $4.95 | **~$6** |
| Haiku 4.5 | $0.15 | $0.99 | **~$1** |

About **$7 for everything**, with a realistic band of $4 to $12 depending
entirely on how much the models think. Cost is 85% thinking tokens; the corpus
is irrelevant to the bill because the judge never sees it.

Prerequisites: `ANTHROPIC_API_KEY` in the environment (currently unset), and
`anthropic` pinned in `requirements.txt`.

## Done when

- 100 pair labels exist from you, hashed and committed before any judge ran.
- κ_ceiling, κ_opus, κ_haiku and run-to-run agreement are all reported with
  intervals.
- `results/agreement.md` states what the numbers do not support, not only what
  they do.
- Someone who has never seen the repo can tell why the judge grades pools rather
  than pairs.

## Residual risks

**Pinning the SDK does not pin the model.** `requirements.txt` exists because a
minor version bump in `sentence-transformers` can change every metric with no
hash to catch it. That protection does not extend here: the model behind
`claude-opus-5` can change server-side at any time, and no pin prevents it.
Record the response `model` field and the run date in the results, and treat
every judge number as measured on a date rather than reproducible on demand.
This is a real weakening of the repo's reproducibility story and belongs in the
README, not in a footnote.

**The sample is balanced, deployment is not.** κ at 44% prevalence does not
estimate κ at the 3.8% you would actually meet. State it next to every κ.

**Gold and negatives differ systematically.** All 56 negatives were retrieved in
a top-20; 26 of the 44 gold pairs never were. If retrievability correlates with
anything about the text, it is confounded with label. Counts are too small to
split 18 against 26 and say anything, so this is documented, not measured.

**Pool composition changes the verdict.** That is inherent to D5 rather than a
flaw in the harness, but it means the sampler is load-bearing and a different
negative draw could move κ.

## Out of scope

- Any generation step, and therefore any judging of answer quality.
- An effort sweep on the judge. Interesting, and it doubles the runs.
- Expanding the question set, which is the only real fix for the interval width
  and is a project of its own.
