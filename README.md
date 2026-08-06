# groundtruth-rag

A retrieval system over technical documentation, plus the evaluation harness
that measures whether it works. The retriever is simple on purpose. The
measurement is the part I care about.

**Status: baseline measured, and it is weak.** Mean recall@10 is **0.362** over
the 24 answerable questions, and **12 of those 24 return no gold chunk in the
top 10 at all**. The corpus is frozen, the index is built, 138 tests pass. The
retriever is a single dense vector search chosen to be beatable, so those
numbers are the starting line rather than a result. Five of the failures are
diagnosed chunk by chunk in [`notes/failures.md`](./notes/failures.md).

## What exists today

| Stage | State | Detail |
|---|---|---|
| Corpus | done | 30 Claude Code doc pages, 1,788,786 chars, sha256 `a887366…473737` |
| Chunking | done | 1,637 chunks, packed to a 254-token budget |
| Embedding | done | `all-MiniLM-L6-v2`, 384-dim, L2-normalised |
| Search | done | cosine top-k over the full index |
| Gold set | labeled | 30 questions, 24 answerable, 6 unanswerable. Every label audited, 6 of 24 revised |
| Metrics | done | recall@k, precision@k, MRR, first relevant rank. 37 tests, 4 injected wrong implementations caught |
| Baseline | done | mean recall@10 0.362 over 24 answerable questions; 12 of 24 return no gold chunk in the top 10 |
| Hybrid | not started | BM25 with reciprocal rank fusion, same questions |
| Confidence intervals | not started | bootstrap CI on the paired per-question difference |

Gold labels are chunk IDs plus a written answer, and every entry carries its
reasoning and the candidates it rejected. See
[`gold/gold-set-template.md`](./gold/gold-set-template.md).

```
corpus/     30 frozen doc pages + INDEX.md with per-page sha256
src/        tokens · mdx · tables · chunk · embed · search · show
            leakage · run_retrieval · metrics · report
index/      chunks.jsonl + manifest.json (pins model, versions, corpus hash)
tests/      138 tests
notes/      decisions and chunk inspection
docs/       design writeups
gold/       30 labeled questions, reasoning and rejected candidates per entry
```

## What measuring caught that guessing missed

### The corpus moves under you

I re-fetched the same 30 pages 24 hours apart. Fourteen of the thirty had
changed size, and two had shrunk. Any metric computed against a live corpus is
measured against a moving target.

The corpus is now pinned by sha256 in `corpus/INDEX.md`. `requirements.txt`
pins library versions for the same reason, one layer up. A minor
`sentence-transformers` bump changes embedding values, which changes every
metric, and no hash would catch it.

### Tokenization killed the chunker's design

I assumed tables were the densest content in the corpus, since every `|` is a
token. Measuring it with `src/tokens.py` showed the opposite. Tables are the
*least* dense at 3.54 chars/token. Code is the real constraint at 2.20. Prose
sits between them at 2.66.

That 1.6x spread means no character-based chunk limit can work. Whatever value
packs code safely wastes about 40% of the budget on tables. `src/chunk.py`
packs by token count instead.

### A passing module test is not a passing pipeline

I had a corpus-wide assertion that no MDX build comment survives
`mdx.transform`. It passed green while 104 of them reached the index. Table
cells and one fallback path never called the transform at all. The test was
correct and the system was broken, which is the harder of the two to notice.

### A quarter of the first-pass gold labels were wrong

24 questions got gold chunk labels. Afterwards, every gold answer was checked
claim by claim against the `text_raw` of every chunk it cited. **Six of the 24
were defective.**

Two different mistakes, needing two different defenses:

- **Searching by a conclusion already reached.** For "how do I create a skill" I
  searched `skill-creator`, got three confident hits, and stopped. The corpus's
  actual walkthrough says "Create the skill directory" and "Write SKILL.md" and
  never uses the phrase I searched for. A query built from an assumed answer
  returns evidence for that assumption.
- **Attaching a plausible chunk to a fluent answer.** Four labels cited chunks
  that did not contain the claims made. One answer said `/context` shows what
  each part costs; the corpus attributes per-server costs to `/mcp`.

The instructive one: an answer claimed Claude Code is normally an MCP *client*.
Both cited chunks contain the word "client", so a grep passes. In those chunks it
means *another application connecting in*, the opposite direction. A term
appearing is not the same as a claim being supported.

That 25% figure is here on purpose. A gold set nobody audited has an unknown
error rate, not a zero one.

### Half a page of "documentation" was JavaScript

The `context-window` page produced 66 chunks. **29 of them are the JSX source of
an interactive visualization embedded in the page**: `useState` calls, event
handlers, hex colours, inline style objects. That is 1.8% of the entire index
made of UI code no query will ever legitimately match, but which still occupies
vector space and can win a similarity contest by accident.

The MDX handling transformed component *tags*. It never anticipated a docs page
embedding a whole component's source. The chunker did what it was told and the
output is still junk. Two gold questions now draw on that page's prose
deliberately, so retrieval has to find one real chunk among 29 decoys.

### Six pages the corpus cites are not in the corpus

`model-config`, `permission-modes`, `costs`, `commands`, `statusline` and
`sandboxing` are linked repeatedly from inside the 30 pages, and none of them was
fetched. Four questions survive only because another page happens to restate the
material. One did not survive and had to be rewritten.

Pages were selected by reading titles. The gap only became visible when questions
were labeled against the text. Choosing a corpus and validating one are different
activities, and only the second finds this.

## Design decisions

**Chunks carry both `text_raw` and `text_embed`.** Labels get written against
byte-exact source text. The model sees the transformed version. A rendering bug
can degrade retrieval, but it cannot corrupt a gold label.

**Gold labels are recorded at chunk level, not doc level.** Doc-level metrics
fall out of the same labels for free, and chunk-level labels survive a
re-chunk. The reverse is not true.

**`index/manifest.json` lists 4 duplicate chunk groups.** When the same answer
appears in two docs, both need labels. Otherwise a correct retrieval scores as
a miss.

**The corpus is skewed, and chunk counts are reported per doc.** `doc-14` alone
is 226 of 1,637 chunks and `doc-07` is 160. Three pages are roughly 40% of the
corpus. Aggregate numbers hide that.

**A chunk is gold only if the answer is impossible without it.** Decided and
written down *before* any labeling, so the rule could not be quietly fitted to
the labels. The test is mechanical: delete the chunk, and ask whether the gold
answer still stands on what remains.

**Chunks that are each independently sufficient are alternatives, and all of
them are gold.** This amendment was forced an hour after the rule above was
written. One question had two chunks that each stated the answer on their own,
so applying the delete test chunk by chunk removed both and left an empty gold
set. The consequence is that recall *understates* performance on those
questions: two alternatives with one retrieved scores 0.5, though the reader was
fully served. MRR and first-relevant-rank are reported alongside recall for
exactly this reason, rather than inventing a fourth metric.

**Gold was found without the retriever.** Labels picked from a top-10 list sit
inside that top-10 by construction, which forces recall@10 to 1.0 before a single
measurement runs. `src/show.py` exists so labels can be found by reading the
corpus directly. `search.py` is the thing being graded and stays downstream of
the judgement.

**Page coverage is 15 of 30, deliberately.** The questions came from real
problems, not from a checklist of pages. Forcing one question per page would mean
writing questions *from* documents, which is how a question ends up sharing rare
vocabulary with its own answer and quietly becomes easy.

Full reasoning is in [`notes/decisions.md`](./notes/decisions.md) and
[`docs/day-02-design.md`](./docs/day-02-design.md).

## Run it

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m pytest -q                              # 138 tests
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

## How this was built

The corpus selection and freeze, and the design decisions recorded in
`notes/decisions.md`, are mine. The Day 2 pipeline source (`tokens`, `mdx`,
`tables`, `chunk`, `embed`, `search`) was AI-assisted and reviewed line by line,
against a rule I set for this project: if I can't explain a line the next day, it
doesn't ship.

**The gold set is split, and the split is recorded per question.** All 30
questions are mine, written with the docs closed. Of the 30 gold *answers*,
7 are mine and 23 were drafted by Claude and reviewed by me. Every entry in
`gold/gold-set-template.md` states which. The audit described above was run
across all of them, and it is where the 25% defect rate came from.

That is a weaker claim than "I hand-built the gold set", and it is the true one.
Writing the answers is the part that carries the judgement, which is why the
7 I wrote myself produced the two most useful findings in the project: one of my
answers was confidently wrong in a way that exposed an ambiguity in the corpus,
and another turned out to be right about a command I had assumed I was guessing
at. A drafted answer produces neither of those collisions.

I would rather say all of this than leave it vague. This repo's whole claim is
about honest measurement, so being cagey about its own provenance would undercut
the point. The reasoning behind every choice is written up in `notes/` and
`docs/`, and I can walk through any of it.

## Corpus attribution

`corpus/` holds 30 pages of Claude Code documentation published by Anthropic at
`code.claude.com/docs` and `platform.claude.com/docs`, fetched 2026-07-29. They
are included verbatim so that any number in this repo can be reproduced against
the exact bytes it was computed from. Copyright remains with Anthropic. This
project is unaffiliated with Anthropic and is not endorsed by them. Source URLs
for every page are listed in [`corpus/INDEX.md`](./corpus/INDEX.md).

## What's next

Finish the gold set: run a rare-vocabulary check across all 30 questions against
their own gold chunks, settle whether 6 unanswerable stays or returns to 5, and
serialize to `gold/gold-set.json`. The markdown file is the working surface, not
the artifact.

`src/metrics.py` is written and tested. The plan was to score ten questions by
hand first, so the code had something to be checked against rather than trusted
on sight, and that is not what happened: the worksheet in
`notes/hand-computed.md` was filled by running the code it was meant to check.
The reasoning and the cost are in D9 in `notes/decisions.md`, and the worksheet
says so above its own numbers.

What still stands behind the metrics is the synthetic test suite, which was
written first, reads nothing from the results file, and covers one case the
real data cannot reach: no question in the gold set has two gold chunks inside
its top 3, so no real number exercises a precision numerator above 1. Four
deliberately wrong implementations were injected and all four were caught.

After a baseline exists: BM25 with reciprocal rank fusion as a second variant,
then a bootstrap confidence interval on the paired per-question difference. On
30 questions a swing of +0.09 may well be noise, and reporting it as an
improvement without a CI would be exactly the kind of unmeasured claim this
project exists to avoid.
