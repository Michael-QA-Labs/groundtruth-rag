# groundtruth-rag

A retrieval system over technical documentation, built alongside the evaluation
harness that measures whether it actually works. The retriever is deliberately
simple; the measurement is the point. Most RAG portfolio projects report no
numbers at all, and the ones that do rarely say how the gold labels were made.

**Status: retrieval works end to end, evaluation is in progress.** The corpus is
frozen, the index is built, and 46 tests pass. The gold question set — the part
that makes any number meaningful — is being written now. There are no retrieval
metrics in this README yet, because there is no validated gold set to compute
them against. That ordering is deliberate.

---

## What exists today

| Stage | State | Detail |
|---|---|---|
| Corpus | ✅ frozen | 30 Claude Code doc pages, 1,788,786 chars, sha256 `a887366…473737` |
| Chunking | ✅ | 1,637 chunks, packed to a 254-**token** budget |
| Embedding | ✅ | `all-MiniLM-L6-v2`, 384-dim, L2-normalised |
| Search | ✅ | cosine top-k over the full index |
| Gold set | 🔨 in progress | 30 questions, 5 deliberately unanswerable |
| Metrics | ⬜ | recall@k, precision@k, MRR — by hand first, then in code |
| Baseline + hybrid | ⬜ | BM25 + reciprocal rank fusion, same questions |
| Confidence intervals | ⬜ | bootstrap CI on the paired per-question difference |

```
corpus/     30 frozen doc pages + INDEX.md with per-page sha256
src/        tokens · mdx · tables · chunk · embed · search
index/      chunks.jsonl + manifest.json (pins model, versions, corpus hash)
tests/      46 tests
notes/      decisions and chunk inspection
docs/       design writeups
gold/       gold question set (in progress)
```

## Three things measurement caught that assumption missed

**1. The corpus moves under you.** Re-fetching the same 30 pages 24 hours apart,
14 of 30 had changed size and 2 had *shrunk*. Any metric computed against a live
corpus is comparing against a moving target. The corpus is now pinned by sha256
in `corpus/INDEX.md`, and `requirements.txt` pins the library versions for the
same reason one layer up — a minor `sentence-transformers` bump changes
embedding values, which changes every metric, with no hash to catch it.

**2. Measuring tokenization killed the chunker's design premise.** The plan
assumed tables were the densest content — every `|` is a token. Measuring it
(`src/tokens.py`) showed tables are the *least* dense at 3.54 chars/token, while
code is the real constraint at 2.20. Prose sits between at 2.66. A 1.6x spread
means **no character-based chunk limit can work**: whatever value packs code
safely wastes ~40% of the budget on tables. `src/chunk.py` packs by token count
instead.

**3. A passing test on a module is not a passing test on the pipeline.** A
corpus-wide assertion that no MDX build comment survives `mdx.transform` passed
green while 104 of them still reached the index. Table cells and one fallback
path never called the transform at all. The test was correct and the system was
broken, which is the more dangerous of the two failure modes.

## Design decisions worth arguing with

- **Chunks carry both `text_raw` and `text_embed`.** Labels are written against
  the byte-exact source; the model sees the transformed version. A rendering bug
  can then never silently corrupt a gold label.
- **Gold labels are recorded at chunk level, not doc level.** Doc-level metrics
  fall out of the same labels for free, and chunk-level labels survive a
  re-chunk. The reverse is not true.
- **`index/manifest.json` lists 4 duplicate chunk groups.** When the same answer
  appears in two docs, both must be labelled, or a correct retrieval is scored
  as a miss.
- **The corpus is skewed on purpose and reported per-doc.** `doc-14` alone is
  226 of 1,637 chunks and `doc-07` is 160; three pages are ~40% of the corpus.
  Aggregate numbers hide this, so chunk counts are reported per doc.

Full reasoning in [`notes/decisions.md`](./notes/decisions.md) and
[`docs/day-02-design.md`](./docs/day-02-design.md).

## Run it

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m pytest -q                              # 46 tests
.venv/bin/python src/embed.py                              # rebuild index/vectors.npz
.venv/bin/python src/search.py "how do I stop the permission prompt?" --top 10 --show-text
```

`index/vectors.npz` and `corpus/combined.md` are derived and not committed —
both rebuild from what is here. `src/fetch_corpus.py` is included for provenance
but **should not be re-run**: it hits the network and would break the freeze.

## How this was built

The corpus selection and freeze, every design decision recorded in
`notes/decisions.md`, and the gold set, metrics and analysis still to come are
mine. The Day 2 pipeline source (`tokens · mdx · tables · chunk · embed ·
search`) was AI-assisted and reviewed line by line against a standing rule for
this project: **if I can't explain a line the next day, it doesn't ship.**

I'm stating that rather than leaving it ambiguous, because the claim this repo
makes is about measurement rigour, and a project about honest reporting that was
vague on its own provenance would be self-refuting. The reasoning behind each
choice — why token-based packing, why raw and rendered text are stored
separately, why chunk-level labels — is written up in `notes/` and `docs/`, and
I'm happy to walk any of it line by line.

## Corpus attribution

`corpus/` contains 30 pages of Claude Code documentation published by Anthropic
at `code.claude.com/docs` and `platform.claude.com/docs`, fetched 2026-07-29 and
included verbatim so that any number in this repo can be reproduced against the
exact bytes it was computed from. Copyright remains with Anthropic. This project
is unaffiliated with Anthropic and is not endorsed by them. Source URLs for
every page are in [`corpus/INDEX.md`](./corpus/INDEX.md).

## What's next

Write the gold set with the docs closed, then compute recall@3, recall@10 and
precision@3 by hand before writing `src/metrics.py`, so the code has something
to be checked against rather than being trusted on sight. After a baseline
exists: BM25 + reciprocal rank fusion as a second variant, then a bootstrap
confidence interval on the paired per-question difference — because on 30
questions, a +0.09 swing may well be noise, and reporting it as an improvement
without a CI would be exactly the kind of unmeasured claim this project exists
to avoid.
