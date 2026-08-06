"""The four retrieval metrics, written out by hand.

Import:  from metrics import recall_at_k, precision_at_k, reciprocal_rank
         from metrics import first_relevant_rank

WHY THIS IS NOT A LIBRARY CALL
------------------------------
`ir_measures` and `ranx` both compute all four of these correctly and in one
line. The point of writing them is that Day 8's numbers get defended out loud:
"recall@10 is 0.31" is only a claim you can stand behind if you can say what is
in the numerator and what is in the denominator without looking it up. Four
functions of three lines each is the cheapest way to own that.

They are also checked against ten questions computed on paper in
notes/hand-computed.md. A library would make that comparison meaningless,
since disagreement would just mean the hand math was wrong.

WHAT IS UNDEFINED, AND WHY IT IS NOT ZERO
-----------------------------------------
6 of the 30 questions are unanswerable and have no gold chunk. Recall and
precision on those are 0/0, which is undefined, and returning 0.0 would let
them average into Day 8's mean as if the retriever had failed a question that
cannot be failed. They return None, and the caller decides.

A retrieved list containing no gold chunk is a different thing entirely. The
question had an answer and the retriever missed it. That is 0.0, it belongs in
the mean, and it is the honest half of this project's headline number: 12 of
the 24 answerable questions return no gold chunk anywhere in the top 10.

WHAT THESE DO NOT KNOW ABOUT
----------------------------
Nothing here reads gold-set.json or the results file, and nothing here averages.
These take a ranked list of chunk IDs and a gold collection, and score one
question. Day 8 does the loading, the aggregation, and the decision about what
to do with the Nones.
"""

from collections.abc import Collection


def _hits_in_top_k(retrieved: list[str], gold: set[str], k: int) -> int:
    """How many distinct gold chunks appear in the first `k` ranks.

    Distinct, via set intersection, for two reasons. gold-set.json is hand
    written so a chunk ID can be typed twice, and counting the list instead
    would let recall come out above 1.0. And the index holds four groups of
    byte-identical chunks, so a retrieved list can hold two IDs with the same
    text; those are genuinely two different retrieved chunks and both count,
    which is what set intersection on IDs already does.
    """
    return len(set(retrieved[:k]) & gold)


def _check_k(retrieved: list[str], k: int) -> None:
    """k must be a real position in the list.

    Asking for precision@20 of a 10-item list is not a smaller number, it is a
    number with a denominator the data cannot fill: at most 0.5, whatever the
    retriever did. Silent is the dangerous version of that, so it raises.
    """
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
    if k > len(retrieved):
        raise ValueError(f"k={k} exceeds the {len(retrieved)} ranks retrieved")


def recall_at_k(retrieved: list[str], gold: Collection[str], k: int) -> float | None:
    """Fraction of the gold chunks that appear in the top k.

    Denominator is the size of the gold set, so the ceiling moves per question:
    a question with 5 gold chunks cannot score above 3/5 at k=3 even when
    retrieval is perfect for the user's purposes. That is D5b in
    notes/decisions.md, and it is why Day 8 reads this next to |gold| and
    treats first-relevant-rank as primary wherever |gold| > 1.

    Returns None when the question has no gold chunk.
    """
    _check_k(retrieved, k)
    gold = set(gold)
    if not gold:
        return None
    return _hits_in_top_k(retrieved, gold, k) / len(gold)


def precision_at_k(retrieved: list[str], gold: Collection[str], k: int) -> float | None:
    """Fraction of the top k that is gold.

    Denominator is k, not the size of the gold set. Every non-gold chunk in the
    top k is something the user reads and discards, and it counts against the
    result whether or not the question had that many right answers to find. The
    consequence, worth stating because it looks like a bug in the Day 8 table:
    a question with one gold chunk retrieved at rank 1 scores precision@3 = 1/3,
    which is the maximum possible for that question and looks like a failure.

    Returns None when the question has no gold chunk.
    """
    _check_k(retrieved, k)
    gold = set(gold)
    if not gold:
        return None
    return _hits_in_top_k(retrieved, gold, k) / k


def first_relevant_rank(retrieved: list[str], gold: Collection[str]) -> int | None:
    """1-indexed rank of the first gold chunk, or None if there is none.

    1-indexed to match the ranked tables in notes/hand-computed.md, which start
    at rank 1. This searches the whole list rather than a top k, which is what
    makes it worth having: with 20 ranks stored, "the gold chunk was at 14" and
    "the gold chunk was nowhere" are different failures, and every k-truncated
    metric reports them identically.

    None covers both the unanswerable case and the retrieved-nothing case.
    They are genuinely the same answer here, and hand-computed.md already says
    "blank if none" for both.
    """
    gold = set(gold)
    if not gold:
        return None
    for position, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in gold:
            return position
    return None


def reciprocal_rank(retrieved: list[str], gold: Collection[str]) -> float | None:
    """1 / the rank of the first gold chunk. 0.0 if none was retrieved.

    0.0 rather than None for a miss, deliberately, and it is the difference
    between an honest MRR and a flattering one. Half the answerable questions
    return no gold chunk in the top 10; dropping those instead of scoring them
    zero would average only over the questions that worked.

    Returns None only when the question has no gold chunk to find.
    """
    if not gold:
        return None
    rank = first_relevant_rank(retrieved, gold)
    return 0.0 if rank is None else 1.0 / rank
