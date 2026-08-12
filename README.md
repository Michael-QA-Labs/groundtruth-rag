# groundtruth-rag

A retrieval system over technical documentation, plus the evaluation harness
that measures whether it works. The retriever is simple on purpose. The
measurement is the part I care about.

Three variants were built over the same frozen corpus and scored against the
same hand-labeled gold set: dense embeddings, BM25, and a reciprocal-rank
fusion of the two. **None of the three is distinguishable from the others.**
All 12 paired comparisons have a 95% confidence interval containing zero.

That non-result is the most useful thing in this repo. The point estimates on
their own would support a confident story about fusion working, and the only
reason that story is not in this README is that the intervals got computed.

What follows is the result, then how the gold set it rests on was built, then
what the non-result means.

---

## What was measured

Four metrics, three variants, 24 answerable questions. Every point estimate
carries its 95% interval, from a 2,000-resample paired bootstrap over the
questions, percentile method, seed `20260806`. The 6 unanswerable questions
have no gold chunk, so recall and precision on them are 0/0 rather than 0, and
they are excluded from every mean here.

| Metric | dense | BM25 | hybrid RRF-60 |
|---|---|---|---|
| recall@3 | 0.181 [0.056, 0.326] | 0.167 [0.042, 0.312] | 0.286 [0.132, 0.454] |
| recall@10 | 0.362 [0.203, 0.536] | 0.453 [0.293, 0.625] | 0.433 [0.271, 0.607] |
| precision@3 | 0.083 [0.028, 0.153] | 0.069 [0.014, 0.125] | 0.139 [0.069, 0.208] |
| MRR | 0.215 [0.111, 0.340] | 0.203 [0.106, 0.323] | 0.288 [0.164, 0.425] |

The headline comparison, hybrid over dense on recall@10, is **+0.071 with an
interval of [-0.075, +0.217]**. The largest observed difference against the
dense baseline is hybrid on recall@3, +0.106, [-0.042, +0.281]. The closest to
settled
is precision@3, hybrid over dense, +0.056, [+0.000, +0.125], whose lower bound
sits at exactly 0.000 under all eight seeds tried.

**The counts say more than the means.** 12 of 24 answerable questions return no
gold chunk in the top 10 under the dense baseline, 9 under BM25, 10 under the
hybrid. Two questions put a gold chunk at rank 1. The baseline is weak, and it
is weak on purpose: a retriever that already worked would have nothing to
measure. Five of those failures are diagnosed chunk by chunk in
[`notes/failures.md`](./notes/failures.md).

**Three questions are measuring the corpus rather than the retriever.** Q06,
Q08 and Q23 ask about pages that were never fetched, so their gold is an
incidental mention rather than the page documenting the answer.
[`results/comparison.md`](./results/comparison.md) reports every metric a second
time without them, and doing so dissolves BM25's apparent advantage at depth:
recall@10 goes from 0.453 against 0.433 to **0.446 against 0.448**. Most of the
keyword retriever's edge was it matching literal words like "plan mode" in
passing mentions on questions whose real page is absent. That is worth knowing
and it is not worth building on.

**What stands behind the arithmetic.** The Day 6 worksheet in
[`notes/hand-computed.md`](./notes/hand-computed.md) was meant to score ten
questions by hand so the metric code had an independent check, and it was
filled by running that code instead. It is not independent and should not be
read as one. What does stand behind the numbers is the synthetic suite in
`tests/test_metrics.py`, written before the results existed and reading nothing
from them, covering one case the real data cannot reach: no question has two
gold chunks inside its top 3, so no real number exercises a precision numerator
above 1. Four deliberately wrong implementations were injected and all four were
caught.

Full numbers: [`results/baseline.md`](./results/baseline.md),
[`results/comparison.md`](./results/comparison.md),
[`results/confidence.md`](./results/confidence.md).

---

## How the gold set was built

Every number above is only as good as the labels underneath it, so this is the
part of the project that got the most care.

**30 questions, written with the docs closed.** They came from real problems
hit while using the tool, not from a checklist of pages, which is why page
coverage is 15 of 30 and deliberately so. Forcing one question per page means
writing questions *from* documents, and that is how a question ends up sharing
rare vocabulary with its own answer and quietly becomes easy. 24 are
answerable from the corpus and 6 are not, and the unanswerable ones are kept as
material for the abstention question.

**A chunk is gold only if the answer is impossible without it.** The rule was
decided and written down *before* any labeling, so it could not be quietly
fitted to the labels afterwards. The test is mechanical: delete the chunk, then
ask whether the gold answer still stands on what remains.

**Chunks that are each independently sufficient are alternatives, and all of
them are gold.** This amendment was forced an hour after the rule above was
written. One question had two chunks that each stated the answer on their own,
so applying the delete test chunk by chunk removed both and left an empty gold
set. The consequence is that recall *understates* performance on those
questions: two alternatives with one retrieved scores 0.5, though the reader
was fully served. MRR and first-relevant-rank are reported alongside recall for
exactly that reason, rather than inventing a fourth metric to paper over it.

**Gold was found without the retriever.** Labels picked from a top-10 list sit
inside that top-10 by construction, which forces recall@10 to 1.0 before a
single measurement runs. `src/show.py` exists so labels can be found by reading
the corpus directly. `search.py` is the thing being graded and stays downstream
of the judgement.

### A quarter of the first-pass labels were wrong

After 24 questions had gold chunk labels, every gold answer was checked claim by
claim against the `text_raw` of every chunk it cited. **Six of the 24 were
defective.** Two different mistakes, needing two different defenses:

- **Searching by a conclusion already reached.** For "how do I create a skill" I
  searched `skill-creator`, got three confident hits, and stopped. The corpus's
  actual walkthrough says "Create the skill directory" and "Write SKILL.md" and
  never uses the phrase I searched for. A query built from an assumed answer
  returns evidence for that assumption.
- **Attaching a plausible chunk to a fluent answer.** Four labels cited chunks
  that did not contain the claims made. One answer said `/context` shows what
  each part costs; the corpus attributes per-server costs to `/mcp`.

The instructive one: an answer claimed Claude Code is normally an MCP *client*.
Both cited chunks contain the word "client", so a grep passes. In those chunks
it means *another application connecting in*, the opposite direction. A term
appearing is not the same as a claim being supported.

That 25% figure is here on purpose. A gold set nobody audited has an unknown
error rate, not a zero one.

### Who wrote what

**The gold set is split, and the split is recorded per question.** All 30
questions are mine, written with the docs closed. Of the 30 gold *answers*, 7
are mine and 23 were drafted by Claude and reviewed by me. Every entry in
[`gold/gold-set-template.md`](./gold/gold-set-template.md) states which, and the
audit above was run across all of them. It is where the 25% defect rate came
from.

That is a weaker claim than "I hand-built the gold set", and it is the true one.
Writing the answers is the part that carries the judgement, which is why the 7 I
wrote myself produced the two most useful findings in the project: one of my
answers was confidently wrong in a way that exposed an ambiguity in the corpus,
and another turned out to be right about a command I had assumed I was guessing
at. A drafted answer produces neither of those collisions.

The same split applies to the code. The corpus selection and freeze, and the
design decisions in [`notes/decisions.md`](./notes/decisions.md), are mine. The
Day 2 pipeline source (`tokens`, `mdx`, `tables`, `chunk`, `embed`, `search`)
was AI-assisted and reviewed line by line, against a rule I set for this
project: if I can't explain a line the next day, it doesn't ship.

I would rather say all of this than leave it vague. This repo's whole claim is
about honest measurement, so being cagey about its own provenance would undercut
the point.

---

## What the non-result means

**0 of 12 paired comparisons exclude zero.** On this gold set, at this sample
size, none of the three variants is distinguishable from the others on any of
the four metrics. That is the result. It is not a failed experiment, and it is
not a reason to report the point estimates as if the intervals did not exist.

The temptation it defuses is concrete. Day 9 produced three tables in which the
hybrid wins recall@3, precision@3 and MRR, and a summary of "fusion improves
three of four metrics" would have been a true statement about these 24
questions and not a claim about the retrievers at all. The mean recall@10 gain
of +0.071 rests on five questions: four improved, one got worse, and **19 of 24
did not move at all**. A mean over 24 questions where 19 are identical is a very
small amount of evidence.

**Roughly 106 questions would settle it.** By normal approximation on the
observed effect and the spread of the per-question differences, that is what the
recall@10 comparison would need before a 95% interval excluded zero. This gold
set has 24.

**What this project will not do is grow the gold set to chase significance.**
Going from 24 to about 106 hand-labeled questions is the majority of the project
again, and it would buy the ability to distinguish two retrievers that differ by
0.07. The honest move is to say so rather than to re-run quietly until something
clears. A portfolio project reporting "+0.071, so the hybrid wins" is
indistinguishable from one that got lucky, and the reader has no way to tell
which they are holding.

Two smaller calls are recorded in [`notes/decisions.md`](./notes/decisions.md)
rather than left implicit: **BCa intervals were refused**, since the correction
cannot change a conclusion when every interval already contains zero, and **all
three variants stay**, since dropping BM25 after fusion failed to win would
leave a comparison of two things with no context.

---

## What measuring caught that guessing missed

**The corpus moves under you.** The same 30 pages, re-fetched 24 hours apart:
fourteen had changed size and two had shrunk. The corpus is now pinned by
sha256 in `corpus/INDEX.md`, and `requirements.txt` pins library versions for
the same reason one layer up, since a minor `sentence-transformers` bump changes
every embedding value with no hash to catch it.

**Tokenization killed the chunker's design.** I assumed tables were the densest
content, since every `|` is a token. Measuring with `src/tokens.py` showed the
opposite: tables are the *least* dense at 3.54 chars/token, code is the real
constraint at 2.20, prose sits between at 2.66. That 1.6x spread means no
character-based limit can work, because whatever value packs code safely wastes
about 40% of the budget on tables. `src/chunk.py` packs by token count instead.

**A passing module test is not a passing pipeline.** A corpus-wide assertion
that no MDX build comment survives `mdx.transform` passed green while 104 of
them reached the index. Table cells and one fallback path never called the
transform at all. The test was correct and the system was broken, which is the
harder of the two to notice.

**Half a page of "documentation" was JavaScript.** The `context-window` page
produced 66 chunks, and 29 of them are the JSX source of a visualization
embedded in the page: `useState` calls, event handlers, hex colours. That is
1.8% of the index made of UI code no query will legitimately match, which still
occupies vector space and can win a similarity contest by accident. Two gold
questions now draw on that page's prose deliberately, so retrieval has to find
one real chunk among 29 decoys.
[`notes/chunk-inspection.md`](./notes/chunk-inspection.md).

**Half this corpus's internal links point outside it.** 727 of the 1,440
internal links lead to a page that was never fetched, across 108 absent slugs,
which is what a 30-page slice of a cross-referenced docs site looks like. The
measured cost is the 3 questions above. Pages were selected by reading titles,
and the gap only became visible when questions were labeled against the text:
choosing a corpus and validating one are different activities, and only the
second finds this.

**Navigation blocks get blamed for it, and did not cause it.** Dangling links
concentrate in blocks that are nothing but a bulleted list of links, and those
reach a top 10 at five times their share of the index, outranking the first gold
chunk in 7 of 24 questions. Filtering them buys +0.003 MRR and nothing else,
because the gold chunk is not at rank 11 waiting to be promoted, it is at 89 or
916. The first filter tried deleted a real gold chunk, since link density finds
links rather than navigation. Why no filter shipped is in
[`notes/corpus-gaps.md`](./notes/corpus-gaps.md).

## Design decisions

**Chunks carry both `text_raw` and `text_embed`.** Labels get written against
byte-exact source text and the model sees the transformed version, so a
rendering bug can degrade retrieval but cannot corrupt a gold label.

**Gold labels are recorded at chunk level, not doc level.** Doc-level metrics
fall out of the same labels for free, and chunk-level labels survive a re-chunk.
The reverse is not true.

**`index/manifest.json` lists 4 duplicate chunk groups.** When the same answer
appears in two docs, both need labels, or a correct retrieval scores as a miss.

**The corpus is skewed, and chunk counts are reported per doc.** `doc-14` alone
is 226 of 1,637 chunks and `doc-07` is 160. Three pages are roughly 40% of the
corpus, and aggregate numbers hide that.

**RRF fuses full-depth lists, all 1,637 ranks from each side.** Truncating first
makes "absent from this list" ambiguous between rank 21 and rank 1,600, and
those are different evidence. Only ranks are stored, never RRF scores, which are
not comparable across questions.

Full reasoning is in [`notes/decisions.md`](./notes/decisions.md) and
[`docs/day-02-design.md`](./docs/day-02-design.md).

## What's in the repo

| Stage | Detail |
|---|---|
| Corpus | 30 Claude Code doc pages, 1,788,786 chars, sha256 `a887366…473737` |
| Chunking | 1,637 chunks, packed to a 254-token budget |
| Embedding | `all-MiniLM-L6-v2`, 384-dim, L2-normalised |
| Search | cosine top-k over the full index |
| Metrics | recall@k, precision@k, MRR, first relevant rank |
| Tests | 195 passing |

```
corpus/     30 frozen doc pages + INDEX.md with per-page sha256
src/        tokens · mdx · tables · chunk · embed · search · show
            leakage · run_retrieval · metrics · report
            keyword_search · fuse · run_hybrid · stats
index/      chunks.jsonl + manifest.json (pins model, versions, corpus hash)
tests/      195 tests
notes/      decisions, chunk inspection, failures, corpus gaps
docs/       design writeups
gold/       30 labeled questions, reasoning and rejected candidates per entry
results/    baseline, bm25, hybrid, comparison, confidence
```

Nothing here depends on a vector database or a RAG framework. The index is a
JSONL file plus a numpy array, BM25 and RRF and the metrics and the bootstrap
are all written from their definitions, and the full dependency list is six
pinned packages.

## Run it

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m pytest -q                              # 195 tests
.venv/bin/python src/embed.py                              # rebuild index/vectors.npz
.venv/bin/python src/search.py "how do I stop the permission prompt?" --top 10 --show-text

# inspect chunks without loading the model (0.1s vs ~3s)
.venv/bin/python src/show.py doc-14:c000        # one chunk, full text_raw
.venv/bin/python src/show.py doc-14             # every chunk in a doc
.venv/bin/python src/show.py --find acceptEdits # which chunks contain a string
```

`index/vectors.npz` and `corpus/combined.md` are derived and not committed.
Both rebuild from what is here. `src/fetch_corpus.py` is included so the corpus
provenance is checkable, but it should not be re-run. It hits the network and
would break the freeze.

## Corpus attribution

`corpus/` holds 30 pages of Claude Code documentation published by Anthropic at
`code.claude.com/docs` and `platform.claude.com/docs`, fetched 2026-07-29. They
are included verbatim so that any number in this repo can be reproduced against
the exact bytes it was computed from. Copyright remains with Anthropic. This
project is unaffiliated with Anthropic and is not endorsed by them. Source URLs
for every page are listed in [`corpus/INDEX.md`](./corpus/INDEX.md).

## What's next

Phase 1 is complete. In priority order from here:

1. **A cross-encoder reranker over the top 50.** The Day 9 numbers argue for
   this concretely: fusion moved four gold chunks from ranks 89, 160, 365 and
   916 to 19, 23, 26 and 39, putting them inside a rerankable candidate list for
   the first time. That is a better use of effort than further fusion tuning.
2. **A Pareto'd failure taxonomy over all 24 questions**, rather than the five
   currently diagnosed in `notes/failures.md`.
3. **An LLM judge validated against hand labels**, reported with Cohen's kappa
   against those labels rather than trusted on its own.
