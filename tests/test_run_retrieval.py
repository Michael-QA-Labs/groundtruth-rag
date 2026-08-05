"""Tests for the retrieval run.

No model is loaded here, following test_search.py: the ranking convention is
testable with synthetic arrays, and the saved results file is testable as data.
The one thing these cannot check is that the batch encoder agrees with
search.search(), which needs the model. That was verified by hand on 2026-08-05
against Q01, Q16 and Q19, all matching on the full top 10.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import run_retrieval                                              # noqa: E402
from show import load_chunks                                      # noqa: E402


@pytest.fixture(scope="module")
def results():
    return json.loads(run_retrieval.DEFAULT_OUT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def gold():
    from build_gold import OUT
    return json.loads(OUT.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- the ranking --

def test_ties_break_by_index_order():
    """Four groups of chunks in this corpus are byte-identical and score
    identically. An unstable sort would let their order vary between runs and
    make every metric computed from this file irreproducible."""
    scores = np.array([0.5, 0.9, 0.9, 0.1], dtype=np.float32)
    assert list(run_retrieval.rank(scores, 4)) == [1, 2, 0, 3]
    for _ in range(20):
        assert list(run_retrieval.rank(scores, 4)) == [1, 2, 0, 3]


def test_rank_returns_the_highest_scores_first():
    scores = np.array([0.1, 0.4, 0.2, 0.3], dtype=np.float32)
    assert list(run_retrieval.rank(scores, 2)) == [1, 3]


# ------------------------------------------------------------ the saved file --

def test_every_question_has_a_full_contiguous_ranking(results):
    top = results["top"]
    assert len(results["questions"]) == 30
    for q in results["questions"]:
        ranks = [r["rank"] for r in q["retrieved"]]
        assert ranks == list(range(1, top + 1)), f"{q['id']} ranking is not 1..{top}"


def test_no_chunk_is_returned_twice_for_one_question(results):
    """A duplicate would inflate precision and is the shape a broken argsort
    slice takes."""
    for q in results["questions"]:
        seen = [r["chunk_id"] for r in q["retrieved"]]
        assert len(set(seen)) == len(seen), f"{q['id']} returned a chunk twice"


def test_scores_are_monotonically_non_increasing(results):
    for q in results["questions"]:
        scores = [r["score"] for r in q["retrieved"]]
        assert scores == sorted(scores, reverse=True), f"{q['id']} is not ranked"


def test_every_retrieved_chunk_exists(results):
    ids = {c["id"] for c in load_chunks()}
    for q in results["questions"]:
        for r in q["retrieved"]:
            assert r["chunk_id"] in ids, f"{q['id']} returned unknown {r['chunk_id']}"


def test_results_were_run_against_the_labeled_corpus(results, gold):
    """D1: a label is only valid against the snapshot it was written from.
    Scoring a run from one corpus against labels from another still produces
    numbers, which is exactly why this is asserted rather than assumed."""
    assert results["corpus_sha256"] == gold["corpus_sha256"]


def test_gold_chunks_in_results_match_the_gold_set(results, gold):
    """The results file copies gold_chunks for convenience, so it can go stale
    the moment a label moves. Eight labels moved during Day 5."""
    expected = {q["id"]: q["gold_chunks"] for q in gold["questions"]}
    for q in results["questions"]:
        assert q["gold_chunks"] == expected[q["id"]], (
            f"{q['id']} gold differs from gold-set.json. Re-run src/run_retrieval.py")


def test_unanswerable_questions_were_run_too(results):
    """Recall is undefined for them, but Day 8 scores abstention and needs to
    see what a question with no correct answer brings back."""
    unanswerable = [q for q in results["questions"] if not q["answerable"]]
    assert len(unanswerable) == 6
    assert all(q["retrieved"] for q in unanswerable)


def test_no_metrics_are_stored(results):
    """Day 6 computes recall and precision by hand from this file and Day 7
    checks code against those numbers. A metric stored here would quietly
    become the thing both days are checked against."""
    blob = json.dumps(results).lower()
    for word in ("recall", "precision", "mrr", "reciprocal"):
        assert word not in blob, f"{word} appears in the results file"
