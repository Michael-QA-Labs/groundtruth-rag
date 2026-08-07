"""Tests for the hybrid run: its guard, and the two files it produced.

The guard is the important half. `run_hybrid.py` refuses to proceed unless its
dense half reproduces results/retrieval-baseline.json rank for rank, and on the
real run it stayed silent, which is exactly the state in which a broken guard
and a working one look identical. Everything below the guard section validates
the artifacts the way tests/test_run_retrieval.py validates the baseline.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import run_hybrid                                                 # noqa: E402

BASELINE = ROOT / "results" / "retrieval-baseline.json"
BM25 = ROOT / "results" / "bm25.json"
HYBRID = ROOT / "results" / "hybrid.json"


# ------------------------------------------------------------------ guard --

def test_guard_accepts_a_dense_ranking_that_matches():
    baseline = {"Q01": ["a", "b", "c"]}
    run_hybrid.check_dense_matches_baseline("Q01", ["a", "b", "c", "d"], baseline)


def test_guard_rejects_a_dense_ranking_that_drifted():
    """A re-embedded index, a changed query prefix or a bumped model version
    all produce a plausible ranking. Without this, the Day 11 interval would
    attribute a dense-side change to the keyword side."""
    baseline = {"Q01": ["a", "b", "c"]}
    with pytest.raises(SystemExit) as exc:
        run_hybrid.check_dense_matches_baseline("Q01", ["a", "x", "c", "d"], baseline)
    assert "rank 2" in str(exc.value)


def test_guard_reports_the_first_rank_that_differs():
    baseline = {"Q05": ["a", "b", "c", "d"]}
    with pytest.raises(SystemExit) as exc:
        run_hybrid.check_dense_matches_baseline("Q05", ["a", "b", "z", "d"], baseline)
    message = str(exc.value)
    assert "rank 3" in message and "z" in message


def test_guard_passes_when_there_is_no_baseline_to_compare_against():
    """First run of a fresh clone. Absence of a baseline is not a mismatch."""
    run_hybrid.check_dense_matches_baseline("Q01", ["a"], {})


# -------------------------------------------------------------- artifacts --

@pytest.fixture(scope="module")
def runs():
    return {name: json.loads(p.read_text())
            for name, p in [("bm25", BM25), ("hybrid", HYBRID),
                            ("baseline", BASELINE)]}


@pytest.mark.parametrize("variant", ["bm25", "hybrid"])
def test_variant_was_built_from_the_same_corpus_and_index(runs, variant):
    """The comparison is only a comparison if both sides face the same index."""
    assert runs[variant]["corpus_sha256"] == runs["baseline"]["corpus_sha256"]
    assert runs[variant]["vectors_sha256"] == runs["baseline"]["vectors_sha256"]


@pytest.mark.parametrize("variant", ["bm25", "hybrid"])
def test_variant_answers_the_same_questions_in_the_same_order(runs, variant):
    """Day 11 pairs per-question scores between variants. Paired statistics on
    lists that are ordered differently would silently compare Q04 against Q05."""
    assert ([q["id"] for q in runs[variant]["questions"]]
            == [q["id"] for q in runs["baseline"]["questions"]])


@pytest.mark.parametrize("variant", ["bm25", "hybrid"])
def test_variant_carries_the_current_gold_labels(runs, variant):
    expected = {q["id"]: q["gold_chunks"] for q in runs["baseline"]["questions"]}
    for q in runs[variant]["questions"]:
        assert q["gold_chunks"] == expected[q["id"]], (
            f"{q['id']} gold differs. Re-run src/run_hybrid.py")


@pytest.mark.parametrize("variant", ["bm25", "hybrid"])
def test_variant_stores_twenty_ranks_per_question(runs, variant):
    for q in runs[variant]["questions"]:
        assert len(q["retrieved"]) == 20
        assert [r["rank"] for r in q["retrieved"]] == list(range(1, 21))


def test_hybrid_stores_no_score(runs):
    """RRF scores are sums of 1/(60+rank) and are not comparable across
    questions. Storing them would invite exactly that comparison."""
    for q in runs["hybrid"]["questions"]:
        assert all("score" not in r for r in q["retrieved"])


def test_no_metrics_are_stored_in_either_variant(runs):
    """Same rule as the baseline file: scoring belongs to metrics.py, so a
    results file must not contain a number anything downstream could mistake
    for one.

    Scoped to `questions` rather than the whole file, unlike the baseline's
    version of this test. The hybrid's `note` field describes the method and
    therefore contains the words "reciprocal rank fusion", which is a name and
    not a metric. Checking the whole blob fails on the description of the
    variant while a per-question score would still slip through if it were
    called something else.
    """
    for variant in ("bm25", "hybrid"):
        blob = json.dumps(runs[variant]["questions"]).lower()
        for word in ("recall", "precision", "mrr", "reciprocal"):
            assert word not in blob


def test_the_variants_are_actually_different_rankings(runs):
    """A fusion bug that returned the dense list unchanged would produce a
    perfectly valid file and a comparison of the baseline against itself."""
    same = sum(1 for a, b in zip(runs["hybrid"]["questions"],
                                 runs["baseline"]["questions"])
               if [r["chunk_id"] for r in a["retrieved"]]
               == [r["chunk_id"] for r in b["retrieved"]])
    assert same == 0
