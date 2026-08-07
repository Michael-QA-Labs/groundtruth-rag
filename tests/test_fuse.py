"""Tests for reciprocal rank fusion.

RRF is three lines and the three lines are the entire Day 9 claim, so the
numbers below are written out rather than asserted as inequalities. An
implementation using 1/rank instead of 1/(60 + rank), or summing scores
instead of ranks, produces a plausible ranking and a different answer.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import fuse                                                       # noqa: E402


def test_score_of_a_single_appearance_is_one_over_sixty_plus_rank():
    """Rank 1 in one list of one: 1/(60 + 1) = 0.016393."""
    assert fuse.rrf_scores([["a"]])["a"] == pytest.approx(1 / 61)


def test_scores_from_both_lists_add():
    """Rank 1 in both: 1/61 + 1/61 = 0.032787."""
    assert fuse.rrf_scores([["a"], ["a"]])["a"] == pytest.approx(2 / 61)


def test_agreeing_at_rank_two_beats_winning_one_list_and_losing_the_other():
    """The behaviour the whole method exists for, computed by hand.

    A is rank 1 in the dense list and rank 10 in the keyword list:
        1/61 + 1/70 = 0.016393 + 0.014286 = 0.030679
    B is rank 2 in both:
        1/62 + 1/62 = 0.016129 + 0.016129 = 0.032258
    B wins. Nothing about B is the best result in either list, and that is
    exactly the Q21 shape: the "Related resources" link block wins the dense
    list outright while the actual instructions rank moderately in both.
    """
    dense = ["A", "B"] + [f"x{i}" for i in range(8)]
    keyword = ["z", "B"] + [f"y{i}" for i in range(7)] + ["A"]
    scores = fuse.rrf_scores([dense, keyword])
    assert scores["A"] == pytest.approx(1 / 61 + 1 / 70)
    assert scores["B"] == pytest.approx(2 / 62)
    assert fuse.fuse([dense, keyword])[0] == "B"


def test_a_chunk_in_only_one_list_still_ranks():
    """Half the point of fusing full-depth lists. A chunk the keyword side
    never matched is not disqualified, it is merely unsupported."""
    scores = fuse.rrf_scores([["a", "b"], ["b"]])
    assert scores["a"] == pytest.approx(1 / 61)
    assert scores["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert fuse.fuse([["a", "b"], ["b"]]) == ["b", "a"]


def test_rank_position_is_per_list_not_global():
    """b is rank 2 in the first list and rank 1 in the second."""
    scores = fuse.rrf_scores([["a", "b"], ["b", "a"]])
    assert scores["a"] == pytest.approx(1 / 61 + 1 / 62)
    assert scores["a"] == pytest.approx(scores["b"])


def test_ties_break_by_chunk_id():
    """Same convention as both retrievers. With equal scores the order must
    not depend on which list happened to be passed first."""
    assert fuse.fuse([["doc-09:c001", "doc-02:c003"],
                      ["doc-02:c003", "doc-09:c001"]]) == [
        "doc-02:c003", "doc-09:c001"]


def test_k_is_sixty_by_default_and_can_be_changed():
    """60 is what PLAN.md specifies and what the original paper uses. It is a
    parameter rather than a literal so Day 11 can show the comparison does not
    hinge on it, but it is not tuned: tuning it against these 24 questions
    would fit the variant to its own evaluation set."""
    assert fuse.rrf_scores([["a"]], k=0)["a"] == pytest.approx(1.0)
    assert fuse.rrf_scores([["a"]], k=59)["a"] == pytest.approx(1 / 60)


def test_fusing_no_lists_raises():
    with pytest.raises(ValueError):
        fuse.rrf_scores([])


def test_fusing_a_single_list_reproduces_its_order():
    """A sanity property with teeth: if this fails, any difference measured
    between the baseline and the hybrid could be the fusion reordering things
    on its own rather than the keyword side contributing anything."""
    ranked = [f"doc-01:c{i:03d}" for i in range(20)]
    assert fuse.fuse([ranked]) == ranked
