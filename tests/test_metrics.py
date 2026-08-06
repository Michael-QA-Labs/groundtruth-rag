"""Tests for the four retrieval metrics.

Every case here is synthetic. Short invented ranked lists, gold sets of one to
three chunks, numbers small enough to check in your head. Nothing in this file
reads `results/retrieval-baseline.json`.

That is deliberate and it is the point of the file's ordering. Day 6 computes
ten of these questions by hand; Day 7 (this) writes the code. If the code were
developed against the real results, the two would stop being independent and
the Day 7 comparison could only ever agree with itself. The real-data
assertions belong in a second pass, added after the hand numbers are written
down and frozen.

The synthetic cases also reach one place the hand numbers cannot. No question
in the gold set has two gold chunks inside its top 3, so no hand-computed
precision@3 will ever have a numerator above 1. Only a made-up ranked list can
exercise that, and if the denominator were wrong the real data would never
show it.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import metrics                                                    # noqa: E402


# A ranked list of ten chunk IDs, shaped like run_retrieval.py's output but
# invented. Rank 1 is `r00`, rank 10 is `r09`, so the rank of `rNN` is NN + 1
# and every expected number below can be read off the name.
RANKED = [f"doc-01:r{i:02d}" for i in range(10)]


def at(rank: int) -> str:
    """The chunk ID sitting at 1-indexed `rank` in RANKED."""
    return RANKED[rank - 1]


# ---------------------------------------------------------------- recall@k --

def test_recall_is_one_when_every_gold_chunk_is_inside_k():
    gold = [at(1), at(3)]
    assert metrics.recall_at_k(RANKED, gold, 3) == 1.0


def test_recall_is_the_fraction_of_gold_found_not_whether_any_was():
    """Two of three gold chunks in the top 3, so 2/3.

    The failure this catches is a `return 1.0 if any(...)` implementation,
    which is what "did retrieval work?" means colloquially and is not what
    recall means. It would pass every single-gold test in this file.
    """
    gold = [at(1), at(2), "doc-09:c999"]
    assert metrics.recall_at_k(RANKED, gold, 3) == pytest.approx(2 / 3)


def test_recall_counts_a_gold_chunk_sitting_exactly_at_rank_k():
    """The off-by-one. `retrieved[:k]` includes rank k; `retrieved[:k-1]` does
    not, and both look right when you read them.
    """
    gold = [at(3)]
    assert metrics.recall_at_k(RANKED, gold, 3) == 1.0


def test_recall_ignores_a_gold_chunk_one_rank_past_k():
    gold = [at(4)]
    assert metrics.recall_at_k(RANKED, gold, 3) == 0.0


def test_recall_is_zero_when_gold_exists_but_none_was_retrieved():
    """Distinct from the undefined case below: the question has an answer and
    the retriever missed it. That is a real 0.0 and belongs in the mean.
    """
    gold = ["doc-09:c999"]
    assert metrics.recall_at_k(RANKED, gold, 10) == 0.0


def test_recall_is_undefined_for_an_unanswerable_question():
    """6 of the 30 questions have no gold chunk. 0/0 is not zero, and a 0.0
    returned here would average into Day 8's mean as a retrieval failure on a
    question that cannot be failed.
    """
    assert metrics.recall_at_k(RANKED, [], 10) is None


# ------------------------------------------------------------- precision@k --

def test_precision_denominator_is_k_not_the_size_of_the_gold_set():
    """One gold chunk, retrieved at rank 1, precision@3 = 1/3.

    Ranks 2 and 3 are wrong answers the user still has to read, so they count
    against precision. Dividing by |gold| instead would report 1.0 here and
    make precision a duplicate of recall.
    """
    gold = [at(1)]
    assert metrics.precision_at_k(RANKED, gold, 3) == pytest.approx(1 / 3)


def test_precision_numerator_can_exceed_one():
    """The case the Day 6 hand numbers structurally cannot cover.

    No question in the gold set has two gold chunks inside its top 3, so every
    hand-computed precision@3 is 0 or 1/3. An implementation that returned
    `1/k` whenever anything was found would match all ten of them and be
    wrong. This is the only test that separates the two.
    """
    gold = [at(1), at(2)]
    assert metrics.precision_at_k(RANKED, gold, 3) == pytest.approx(2 / 3)


def test_precision_is_one_when_the_whole_top_k_is_gold():
    gold = [at(1), at(2), at(3)]
    assert metrics.precision_at_k(RANKED, gold, 3) == 1.0


def test_precision_ignores_gold_below_k():
    """Gold at rank 5 does not improve precision@3. Recall@10 and precision@3
    disagreeing on the same question is the normal case, not a bug.
    """
    gold = [at(5)]
    assert metrics.precision_at_k(RANKED, gold, 3) == 0.0


def test_precision_is_undefined_for_an_unanswerable_question():
    assert metrics.precision_at_k(RANKED, [], 3) is None


# --------------------------------------------------------- reciprocal rank --

def test_reciprocal_rank_is_one_for_gold_at_rank_one():
    assert metrics.reciprocal_rank(RANKED, [at(1)]) == 1.0


def test_reciprocal_rank_is_one_over_the_rank():
    assert metrics.reciprocal_rank(RANKED, [at(4)]) == pytest.approx(0.25)


def test_reciprocal_rank_uses_the_first_gold_chunk_not_the_last():
    """Guards a loop that keeps overwriting instead of stopping. With gold at
    ranks 2 and 5 the answer is 1/2; a loop without a break returns 1/5.
    """
    gold = [at(2), at(5)]
    assert metrics.reciprocal_rank(RANKED, gold) == pytest.approx(0.5)


def test_reciprocal_rank_does_not_depend_on_the_order_gold_was_written_in():
    """gold-set.json lists chunks in labeling order, not rank order. Q01's gold
    is stored `doc-02:c005, doc-01:c001, doc-02:c001` and the retrieved list
    hits them in a different order.
    """
    assert metrics.reciprocal_rank(RANKED, [at(5), at(2)]) == pytest.approx(0.5)


def test_reciprocal_rank_is_zero_when_no_gold_was_retrieved():
    """0.0, not None. Half the answerable questions return no gold in the top
    10, and those zeros are the finding. Dropping them from the MRR would
    report the retriever as roughly twice as good as it is.
    """
    assert metrics.reciprocal_rank(RANKED, ["doc-09:c999"]) == 0.0


def test_reciprocal_rank_is_undefined_for_an_unanswerable_question():
    assert metrics.reciprocal_rank(RANKED, []) is None


# ---------------------------------------------------- first relevant rank --

def test_first_relevant_rank_is_one_indexed():
    """1-indexed because it is read against the ranked lists in
    notes/hand-computed.md, whose first row is rank 1. A 0-indexed answer
    would be off by one against every table this is checked with.
    """
    assert metrics.first_relevant_rank(RANKED, [at(1)]) == 1


def test_first_relevant_rank_returns_the_earliest_of_several():
    assert metrics.first_relevant_rank(RANKED, [at(7), at(3)]) == 3


def test_first_relevant_rank_is_none_when_no_gold_was_retrieved():
    assert metrics.first_relevant_rank(RANKED, ["doc-09:c999"]) is None


def test_first_relevant_rank_searches_the_whole_list_not_just_the_top_ten():
    """The reason run_retrieval.py stores 20. "Gold at rank 14" and "gold
    nowhere" are different failures with different fixes, and this is the
    function that tells them apart.
    """
    long_list = RANKED + [f"doc-02:x{i:02d}" for i in range(10)]
    assert metrics.first_relevant_rank(long_list, ["doc-02:x03"]) == 14


# ------------------------------------------------------------------ guards --

def test_k_beyond_the_end_of_the_ranked_list_raises():
    """precision@20 over a 10-item list is silently at most 0.5, whatever the
    retriever did. Day 9's hybrid variant is where this would bite: fuse two
    lists, forget one is short, and read the drop as a real result.
    """
    with pytest.raises(ValueError):
        metrics.precision_at_k(RANKED, [at(1)], 20)


def test_k_of_zero_raises():
    with pytest.raises(ValueError):
        metrics.precision_at_k(RANKED, [at(1)], 0)


def test_duplicate_gold_ids_do_not_inflate_recall():
    """gold-set.json is hand-written, so a chunk can be listed twice. Counting
    the list rather than the set would report recall above 1.0.
    """
    assert metrics.recall_at_k(RANKED, [at(1), at(1)], 3) == 1.0
