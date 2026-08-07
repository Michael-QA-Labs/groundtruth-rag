"""Reciprocal rank fusion of two or more ranked lists.

Import:  from fuse import fuse, rrf_scores

    score(chunk) = sum over lists of 1 / (k + rank in that list)

with k = 60 and rank starting at 1. A chunk missing from a list contributes
nothing from it.

WHY RANKS AND NOT SCORES
------------------------
The dense side returns cosine similarities, roughly 0.4 to 0.7 on this corpus.
The keyword side returns BM25 sums, unbounded above and frequently exactly 0.
There is no principled way to add those two numbers: any weighting is a
guess, and normalising each to [0,1] makes the result depend on the best and
worst scores of that particular query, so the same chunk fuses differently
depending on what else was retrieved.

Ranks have none of that. They are the same units on both sides by
construction, which is why this method survives being the simplest thing that
could work.

WHAT k = 60 DOES
----------------
It flattens the top. Rank 1 scores 1/61 and rank 10 scores 1/70, a difference
of 14%, where 1/rank would make rank 1 ten times rank 10. So a chunk needs
support from both retrievers to beat a chunk that one retriever loves, which
is the entire reason to fuse rather than to pick.

That is a real bet on this corpus, not a free win. The Day 8 failures split
two ways on it. Q21 and Q29 are cases where the right chunk ranks moderately
in the dense list and is beaten by a chunk that ranks first; if the keyword
side also ranks the right chunk moderately, fusion promotes it. Q22, Q06 and
Q08 have gold at ranks 192, 89 and 69, and nothing here reaches that far: a
chunk unranked by one side and 192nd by the other is still 192nd-ish.

**Predict before measuring.** If the hybrid improves, it should improve on the
first group and not the second. An improvement spread evenly across both is
evidence of something else, most likely a bug in how the lists were built.

k is a parameter, but it is not tuned. Fitting it to these 24 questions would
make Day 11's confidence interval a statement about a retriever that had
already seen its own evaluation set.
"""

from collections import defaultdict

K = 60


def rrf_scores(ranked_lists: list[list[str]], k: int = K) -> dict[str, float]:
    """Fused score per chunk ID. Higher is better.

    Every chunk appearing in any list gets an entry, so a chunk one retriever
    never found is ranked lower rather than dropped.
    """
    if not ranked_lists:
        raise ValueError("nothing to fuse")

    scores: dict[str, float] = defaultdict(float)
    for ranked in ranked_lists:
        for position, chunk_id in enumerate(ranked, start=1):
            scores[chunk_id] += 1.0 / (k + position)
    return dict(scores)


def fuse(ranked_lists: list[list[str]], k: int = K, top: int | None = None) -> list[str]:
    """Chunk IDs best first, ties broken by chunk ID.

    Same tie convention as `run_retrieval.rank` and `BM25Index.search`. Fusing
    lists that each break ties one way, with a third rule here, would produce
    an order that depends on nothing in the data.
    """
    scores = rrf_scores(ranked_lists, k)
    ranked = sorted(scores, key=lambda cid: (-scores[cid], cid))
    return ranked if top is None else ranked[:top]
