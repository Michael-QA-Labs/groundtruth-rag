# groundtruth-rag

A retrieval system over technical documentation, plus the evaluation harness
that measures whether it works. The retriever is simple on purpose. The
measurement is the part I care about.

**Status: retrieval runs end to end, evaluation is in progress.** The corpus is
frozen, the index is built, 46 tests pass. The gold question set is being
written now. There are no retrieval metrics in this README yet, because there is
no gold set to compute them against.

## What exists today

| Stage | State | Detail |
|---|---|---|
| Corpus | done | 30 Claude Code doc pages, 1,788,786 chars, sha256 `a887366…473737` |
| Chunking | done | 1,637 chunks, packed to a 254-token budget |
| Embedding | done | `all-MiniLM-L6-v2`, 384-dim, L2-normalised |
| Search | done | cosine top-k over the full index |
| Gold set | in progress | 30 questions, 5 of them unanswerable |
| Metrics | not started | recall@k, precision@k, MRR. By hand first, then in code |
| Baseline + hybrid | not started | BM25 with reciprocal rank fusion, same questions |
| Confidence intervals | not started | bootstrap CI on the paired per-question difference |

```
corpus/     30 frozen doc pages + INDEX.md with per-page sha256
src/        tokens · mdx · tables · chunk · embed · search
index/      chunks.jsonl + manifest.json (pins model, versions, corpus hash)
tests/      46 tests
notes/      decisions and chunk inspection
docs/       design writeups
gold/       gold question set (in progress)
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

Full reasoning is in [`notes/decisions.md`](./notes/decisions.md) and
[`docs/day-02-design.md`](./docs/day-02-design.md).

## Run it

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m pytest -q                              # 46 tests
.venv/bin/python src/embed.py                              # rebuild index/vectors.npz
.venv/bin/python src/search.py "how do I stop the permission prompt?" --top 10 --show-text
```

`index/vectors.npz` and `corpus/combined.md` are derived and not committed.
Both rebuild from what is here. `src/fetch_corpus.py` is included so the corpus
provenance is checkable, but it should not be re-run. It hits the network and
would break the freeze.

## How this was built

The corpus selection and freeze, the design decisions recorded in
`notes/decisions.md`, and the gold set and analysis still to come are mine. The
Day 2 pipeline source (`tokens`, `mdx`, `tables`, `chunk`, `embed`, `search`)
was AI-assisted and reviewed line by line, against a rule I set for this
project: if I can't explain a line the next day, it doesn't ship.

I would rather say that than leave it vague. This repo's whole claim is about
honest measurement, so being cagey about its own provenance would undercut the
point. The reasoning behind every choice is written up in `notes/` and `docs/`,
and I can walk through any of it.

## Corpus attribution

`corpus/` holds 30 pages of Claude Code documentation published by Anthropic at
`code.claude.com/docs` and `platform.claude.com/docs`, fetched 2026-07-29. They
are included verbatim so that any number in this repo can be reproduced against
the exact bytes it was computed from. Copyright remains with Anthropic. This
project is unaffiliated with Anthropic and is not endorsed by them. Source URLs
for every page are listed in [`corpus/INDEX.md`](./corpus/INDEX.md).

## What's next

Write the gold set with the docs closed. Then compute recall@3, recall@10 and
precision@3 by hand before writing `src/metrics.py`, so the code has something
to be checked against rather than trusted on sight.

After a baseline exists: BM25 with reciprocal rank fusion as a second variant,
then a bootstrap confidence interval on the paired per-question difference. On
30 questions a swing of +0.09 may well be noise, and reporting it as an
improvement without a CI would be exactly the kind of unmeasured claim this
project exists to avoid.
