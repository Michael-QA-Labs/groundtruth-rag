# Three variants on the same 30 questions

Day 9, 2026-08-06. Corpus `a887366bab9778b5`, index `f0587a0e188318e0`,
model `all-MiniLM-L6-v2`. Per-variant tables are in `baseline.md`, `bm25.md`
and `hybrid.md`; this file is the comparison.

**No confidence intervals yet. Nothing below is a claim that a difference is
real.** That is Day 11, and the paired movement in the third table is the
reason it is not optional.

## The numbers

Means over the 24 answerable questions. The 6 unanswerable are excluded, D8.

| Metric | dense | BM25 | hybrid RRF-60 |
|---|---:|---:|---:|
| mean recall@3 | 0.181 | 0.167 | **0.286** |
| mean recall@10 | 0.362 | **0.453** | 0.433 |
| mean precision@3 | 0.083 | 0.069 | **0.139** |
| MRR | 0.215 | 0.203 | **0.288** |
| no gold in top 10 | 12 of 24 | **9 of 24** | 10 of 24 |
| no gold in top 20 | 9 | **7** | 8 |
| gold at rank 1 | 2 | 2 | **3** |
| SDK slots of 240 (D7) | 21 | 22 | 21 |

**The hybrid wins everything about the top of the list and loses recall@10 to
BM25 alone.** That is not the result Day 9 was set up to produce, and it is the
reason `run_hybrid.py` saves the keyword-only run: without it, the hybrid's
+0.071 recall@10 over dense would read as fusion working, when a plain keyword
retriever does better on that metric than either.

**BM25 is deep but blunt.** It puts a gold chunk somewhere in the top 20 more
often than anything else here, and it is the worst of the three at putting one
near the top: worst recall@3, worst precision@3, worst MRR. Its wins are at
ranks 6, 9 and 10, which is why they show up in recall@10 and nowhere else.

**Nothing shifted the SDK confusion count.** 21, 22, 21 of 240 top-10 slots.
D7's category is insensitive to the retrieval method, which makes it a property
of the corpus rather than of the ranker.

## The same table with the three corpus-gap questions removed

Q06, Q08 and Q23 are the questions whose canonical page was never fetched, so
their gold is an incidental mention rather than the page that documents the
answer. Audited on Day 9: 3 of 24, evidenced by the gold chunk's own answer
sentence linking out to the absent page by name and anchor.

| Metric | dense | BM25 | hybrid |
|---|---:|---:|---:|
| mean recall@3 | 0.206 | 0.143 | **0.327** |
| mean recall@10 | 0.390 | 0.446 | **0.448** |
| mean precision@3 | 0.095 | 0.048 | **0.159** |
| MRR | 0.239 | 0.179 | **0.310** |

**BM25's recall@10 lead over the hybrid disappears, 0.446 against 0.448.** On
all 24 it looked like 0.453 against 0.433. So most of the keyword retriever's
apparent edge at depth comes from two questions where the right page is not in
the corpus at all, and it earns that edge by matching literal words like "auto
mode" and "plan mode" in passing mentions the dense side reads past.

That is worth knowing and it is not worth building on. It means BM25 is
compensating for a Day 1 corpus decision, not retrieving better.

## What actually moved, question by question

Paired against the dense baseline, over the 24 answerable.

| | better | worse | unchanged |
|---|---:|---:|---:|
| hybrid, recall@10 | 4 | 1 | 19 |
| hybrid, reciprocal rank | 11 | 6 | 7 |
| BM25, recall@10 | 7 | 4 | 13 |

**The headline +0.071 in mean recall@10 rests on five questions.** Q04, Q08,
Q12 and Q29 improved, Q07 got worse, and 19 of 24 did not move at all. A mean
over 24 questions where 19 are identical is a very small amount of evidence,
and this is exactly the situation Day 11 exists for: with n that small, the
bootstrap interval on the paired difference is the only thing that separates
this from noise.

**Reciprocal rank tells a different and more encouraging story**, moving on 17
of 24 rather than 5. Recall@10 is a threshold and hides everything that happens
inside the top 20; the hybrid moved Q14 from rank 8 to rank 1, Q24 from 8 to 2
and Q26's gold to rank 2, none of which recall@10 can see.

## Why the hybrid loses questions BM25 alone wins

RRF support from rank *r* is worth `1 / (60 + r)`. Rank 1 is 0.0164, rank 6 is
0.0152, rank 61 is 0.0083, rank 160 is 0.0046, rank 916 is 0.0010. Two
mid-ranked appearances beat one excellent one, by design.

Measured on the four questions where the two variants disagree most:

| Q | gold chunk | dense rank | BM25 rank | fused rank | RRF score |
|---|---|---:|---:|---:|---|
| Q21 | `doc-12:c006` | 160 | 6 | **26** | 0.00455 + 0.01515 = 0.01970 |
| Q10 | `doc-02:c011` | 916 | 6 | **39** | 0.00102 + 0.01515 = 0.01618 |
| Q06 | `doc-05:c032` | 89 | 2 | **19** | 0.00671 + 0.01613 = 0.02284 |
| Q07 | `doc-10:c004` | 2 | 365 | **23** | 0.01613 + 0.00235 = 0.01848 |

Q21's fused rank 1 is `doc-12:c001`, which neither retriever ranked first:
dense 3, BM25 3, RRF 0.03175. It beats the gold chunk by agreement alone.

**So the gold chunks are not lost by fusion, they are placed at 19, 23, 26 and
39.** Every one of them would be inside a top-50 candidate list. That is a
concrete argument for the Phase 2 reranking item over any further fusion
tuning: the material is now in reach of a cross-encoder, which it was not in
the dense baseline where these sat at 89, 160, 365 and 916.

**Q07 is the one real regression and it is the mirror image.** Dense put its
gold chunk at rank 2; BM25 buried it at 365; fusion split the difference at 23
and recall@10 went from 1.00 to 0.00. Fusing a good list with a bad one costs
you the good list's wins.

## The prediction, and how it did

`src/fuse.py` recorded a prediction before this was run: the hybrid should help
the Q21 and Q29 shape, where the right chunk ranks moderately in both lists,
and should not help Q22, Q06 and Q08, where the gold sits at 192, 89 and 69.

**Half right.** Q29 improved as predicted, from no gold in the top 20 to rank 5.
Q22 did not move, as predicted. But Q21 got worse than BM25 alone rather than
better, because the prediction assumed the dense side ranked its gold
moderately and it does not: rank 160. And Q08 improved from 0.00 to 0.50,
which the prediction ruled out, because BM25 finds a passing mention of "plan
mode" that the dense side never surfaces.

The error in both cases is the same: the prediction was written from the Day 8
failure categories, which describe where gold sits in the *dense* list, and said
nothing about where the keyword side would put it. A fusion prediction needs
both lists.

## What Day 11 has to answer

1. Is +0.071 mean recall@10, hybrid over dense, distinguishable from zero on
   24 questions where 19 did not move? Bootstrap the paired per-question
   difference, not the two means separately.
2. Same question for MRR, +0.073, which moved 17 of 24 and is the better
   powered comparison.
3. Q06 and Q30 both cite `doc-05:c032`, flagged since Day 4. Two of the
   questions in the tables above are therefore correlated, and the resample
   should treat them as such.
4. Report the interval for BM25 alone too. If it overlaps the hybrid's, then
   "fusion helps" is not a claim this gold set can support, and the honest
   Day 12 sentence is that the two are indistinguishable at this sample size.
