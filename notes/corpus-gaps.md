# What the missing pages actually cost

2026-08-06, after Day 11. Corpus `a887366bab9778b5`, 30 pages, 1,637 chunks.

The README has said since Day 4 that six cited pages are not in the corpus.
That is true and it undersells one thing while overselling another. This file
measures both.

## The census

**108 distinct `/docs/en/` slugs are cited from inside the corpus and are not
in it.** By link instance rather than by slug: **727 of the 1,440 internal
documentation links in this corpus point at a page that was never fetched,
50.5%.**

That number sounds alarming and mostly is not. A 30-page slice of a docs site
that cross-references itself constantly will dangle about half its links by
construction. It is the shape of the decision made on Day 1, not a defect
introduced later.

**The six the README names are not the six most cited.**

| Rank of 108 | Slug | Chunks citing | Pages citing | Named in README |
|---:|---|---:|---:|---|
| 1 | `env-vars` | 50 | 13 | no |
| 2 | `agent-sdk/typescript` | 35 | 8 | no |
| 3 | `model-config` | 32 | 10 | yes |
| 4 | `permission-modes` | 29 | 11 | yes |
| 5 | `plugins-reference` | 29 | 10 | no |
| 6 | `agent-view` | 24 | 9 | no |
| 7 | `commands` | 22 | 13 | yes |
| 8 | `agent-teams` | 20 | 8 | no |
| 9 | `sandboxing` | 18 | 8 | yes |
| 10 | `remote-control` | 16 | 9 | no |
| 34 | `statusline` | 5 | 3 | yes |
| 45 | `costs` | 4 | 4 | yes |

The README's list is the six noticed while labeling, which is a different
thing from the six most cited and was never the claim it looked like. `costs`
is cited by 4 chunks and `statusline` by 5, while `env-vars` at 50 chunks
across 13 of the 30 pages goes unmentioned.

**Corrected, the honest sentence is:** roughly half of this corpus's internal
links point outside it, the most-cited absent page is `env-vars`, and the six
originally named are the ones that happened to surface during labeling.

## What fetching any of them would buy, measured

Audited on Day 9, question by question, with a mechanical rule: a question
counts only if **the sentence carrying its gold answer defers to an absent page
by name and anchor**, which is the corpus itself saying the canonical treatment
lives elsewhere.

| Absent page | Questions it would fix | Evidence |
|---|---|---|
| `permission-modes` | Q06, Q08 | gold sentence links `#eliminate-prompts-with-auto-mode` and `#analyze-before-you-edit-with-plan-mode` |
| `model-config` | Q23 | gold sentence links `#setting-your-model` |
| every other absent page | none measured | deferrals are for extra detail, with an in-corpus chunk carrying the answer |

**3 of 24 answerable questions, 12.5%.** Q24 and Q26 were checked and rejected:
both defer to absent pages, `sessions` and `commands` respectively, but only for
picker shortcuts and a command list, while an in-corpus chunk states the answer.
Deferring is not the same as depending.

**None of them will be fetched.** D1 froze the corpus by sha256, and adding a
page invalidates the index hash, every stored result, every chunk ID in the gold
set and every number in `results/`. Two questions are not worth that. The v2
move is to re-fetch and re-label from scratch, not to patch.

`results/comparison.md` reports every metric a second time with those three
questions removed, which is what turned out to matter: BM25's apparent recall@10
advantage over the hybrid, 0.453 to 0.433, becomes 0.446 to 0.448 without them.
Most of the keyword retriever's edge was it matching literal words in the
passing mentions those three questions are stuck with.

## The thing the missing pages are blamed for and did not do

The dangling links concentrate in a particular kind of chunk: short blocks that
are nothing but a bulleted list of links with a one-line gloss each. Those
chunks are also disproportionately retrieved.

| Group | n | Mean links per chunk | Link-dense share |
|---|---:|---:|---:|
| every chunk in the index | 1,637 | 0.95 | 1.3% |
| chunks in an answerable top 10 | 240 | 1.53 | **6.2%** |
| gold chunks | 44 | 1.77 | 2.3% |

Link-dense means 3 or more markdown links per 100 tokens. **A link-dense chunk
is about five times more likely to appear in a top 10 than its share of the
index would predict.** Gold chunks carry plenty of links too, but they are
rarely link-*dominated*.

**In 7 of 24 answerable questions a link-dense chunk outranks the first gold
chunk**, and six of those seven are the same chunk:

`doc-05:c037` is the four-bullet block at the end of `best-practices`: how the
agentic loop works, extend Claude Code, common workflows, CLAUDE.md. It is a
table of contents for the product. It contains no answer to anything, it is in
the top 10 of 6 different questions, and it outranks the gold chunk in all six.
`doc-03:c008`, the "you can access Claude Code through the desktop app, VS Code,
Slack, CI/CD" surface list, is in five top 10s and has 4 dangling links of 7.

That is a real finding about dense retrieval on documentation: **a chunk that
names every major concept once is a near-optimal match for any question about
the product, and answers none of them.**

It is also **not** a missing-pages problem. It would happen identically with a
complete corpus. The two issues share a location and nothing else.

## The fix that does not work, tested twice

**Attempt 1: drop chunks with 3+ links per 100 tokens.** 22 chunks, 1.3% of the
index.

| Metric | Before | After | Difference | 95% CI |
|---|---:|---:|---:|---|
| recall@3 | 0.181 | 0.181 | +0.000 | [+0.000, +0.000] |
| recall@10 | 0.362 | 0.349 | **-0.014** | [-0.042, +0.000] |
| precision@3 | 0.083 | 0.083 | +0.000 | [+0.000, +0.000] |
| MRR | 0.222 | 0.225 | +0.003 | [+0.001, +0.006] |

Recall@10 got *worse*, and the reason is the whole lesson: the filter deletes
`doc-02:c001`, which is **real gold for Q01**. It is the quickstart note saying
this guide covers the terminal CLI while Claude Code also runs on web, desktop,
VS Code, JetBrains, Slack and CI, and it is link-dense because listing six
interfaces requires six links. Link density finds links, not navigation.

**Attempt 2: drop chunks where 60%+ of lines are a bullet that starts with a
link.** This separates the cases exactly: `doc-05:c037` and `doc-12:c076` score
1.00, `doc-02:c001` and `doc-03:c008` score 0.00. 25 chunks, 1.5% of the index,
**no gold lost**.

| Metric | Before | After | Difference | 95% CI | Excludes zero |
|---|---:|---:|---:|---|---|
| recall@3 | 0.181 | 0.181 | +0.000 | [+0.000, +0.000] | no |
| recall@10 | 0.362 | 0.362 | +0.000 | [+0.000, +0.000] | no |
| precision@3 | 0.083 | 0.083 | +0.000 | [+0.000, +0.000] | no |
| MRR | 0.222 | 0.225 | +0.003 | [+0.001, +0.006] | **yes** |

*(MRR reads 0.222 rather than the 0.215 in `results/baseline.md` because this
simulation ranks all 1,637 chunks, so gold beyond rank 20 contributes 1/rank
instead of 0.)*

**A correctly targeted filter, losing nothing, buys +0.003 MRR.**

## Why so little, and what it means

The displacement is real and the removal does not help, because **the gold
chunk is not sitting at rank 11 waiting to be promoted.** In the six questions
`doc-05:c037` pollutes, gold sits at ranks 13, 89, 916, 8 and nowhere at all.
Deleting one chunk above it moves everything up exactly one rank. Nothing
crosses a threshold that matters.

**Deliberately not implemented.** There is no `src/navigation.py`, because
shipping a filter to buy 0.003 MRR would be adding code and a maintenance
surface to fix a symptom, and the note explaining why is worth more than the
filter.

**The counterpart to Day 11, in the opposite direction.** D11 recorded a set of
differences too small to distinguish from zero. This is a difference that *does*
exclude zero, on every seed, and is worthless anyway: +0.003 MRR is not a
retrieval improvement, it is a rounding artifact with a confidence interval
attached. An interval that excludes zero answers "is this real", never "is this
worth anything", and those come apart in both directions.

## Reproducing this

```python
# nav_share: share of non-empty lines that are a bullet starting with a link
BULLET_LINK = re.compile(r"^\s*[*-]\s*\**\[")
lines = [l for l in chunk["text_raw"].splitlines() if l.strip()]
nav_share = sum(bool(BULLET_LINK.match(l)) for l in lines) / len(lines)
```

Dangling links are `/docs/en/<slug>` references whose slug is not a page name in
`corpus/INDEX.md`. The rank data comes from a full-depth run:
`src/run_retrieval.py --top 1637 --out /tmp/full-depth.json`.
