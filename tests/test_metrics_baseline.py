"""Pin the ten scored questions against results/retrieval-baseline.json.

WHAT THESE ARE, AND WHAT THEY ARE NOT
-------------------------------------
Day 7's plan was for this comparison to check `metrics.py` against ten numbers
computed by hand, independently of the code. That is not what happened. The
values in notes/hand-computed.md were produced by `metrics.py` itself on
2026-08-06, so asserting them here cannot detect a wrong metric: the code
agrees with numbers it generated.

They are regression pins, and as pins they are worth having. Days 9 and 10 add
a keyword variant and fuse two ranked lists; Day 11 resamples per-question
scores. Any of those can quietly change how the baseline is scored, and a
changed baseline invalidates every comparison drawn against it. These 37
assertions fail loudly when that happens.

The real check on `metrics.py` is tests/test_metrics.py, which is synthetic,
was written before this file existed, and reads nothing from the results file.
Keep them in separate files so that stays true and stays visible.

They also pin the results file itself. Every value here depends on the corpus
hash, the index and the model, all three asserted below, so a silent re-fetch
or re-embed shows up as a metric change rather than as nothing at all.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import metrics                                                    # noqa: E402

BASELINE = ROOT / "results" / "retrieval-baseline.json"

# The frozen inputs every number below is a function of.
CORPUS_SHA = "a887366bab9778b59129493073c38a116d55ff8e6657b191be1f9d5678473737"
VECTORS_SHA = "f0587a0e188318e00dcc811a453f45d9a5985ced426ab6c36483bdf5ef596f5f"

# (recall@3, recall@10, precision@3, first relevant rank), from
# notes/hand-computed.md. Written as fractions rather than decimals so a
# failure message shows which denominator moved.
EXPECTED = {
    "Q04": (0 / 5, 1 / 5, 0 / 3, 4),
    "Q01": (1 / 3, 2 / 3, 1 / 3, 2),
    "Q02": (0 / 3, 0 / 3, 0 / 3, 20),
    "Q14": (0 / 3, 1 / 3, 0 / 3, 8),
    "Q23": (0 / 2, 1 / 2, 0 / 3, 7),
    "Q25": (0 / 2, 2 / 2, 0 / 3, 6),
    "Q26": (1 / 2, 1 / 2, 1 / 3, 2),
    "Q16": (1 / 1, 1 / 1, 1 / 3, 1),
    "Q10": (0 / 1, 0 / 1, 0 / 3, None),
    "Q11": (None, None, None, None),
}


@pytest.fixture(scope="module")
def baseline():
    return json.loads(BASELINE.read_text())


@pytest.fixture(scope="module")
def questions(baseline):
    return {q["id"]: q for q in baseline["questions"]}


def test_baseline_was_built_from_the_frozen_corpus_and_index(baseline):
    """If either hash moves, every number in this file is about a different
    retriever and the pins below are meaningless rather than wrong."""
    assert baseline["corpus_sha256"] == CORPUS_SHA
    assert baseline["vectors_sha256"] == VECTORS_SHA


@pytest.mark.parametrize("qid", sorted(EXPECTED))
def test_scores_match_the_worksheet(qid, questions):
    q = questions[qid]
    ranked = [r["chunk_id"] for r in q["retrieved"]]
    gold = q["gold_chunks"]
    r3, r10, p3, frr = EXPECTED[qid]

    assert metrics.recall_at_k(ranked, gold, 3) == pytest.approx(r3)
    assert metrics.recall_at_k(ranked, gold, 10) == pytest.approx(r10)
    assert metrics.precision_at_k(ranked, gold, 3) == pytest.approx(p3)
    assert metrics.first_relevant_rank(ranked, gold) == frr


def test_no_precision_at_3_in_the_worksheet_exceeds_one_third():
    """The documented gap, asserted rather than asserted-to-be-true in prose.

    No question in the gold set has two gold chunks inside its top 3, so the
    real data cannot exercise a precision numerator above 1. If this test ever
    fails, a re-labeling has changed that and the synthetic case in
    test_metrics.py has stopped being the only coverage of it.
    """
    values = [p3 for _, _, p3, _ in EXPECTED.values() if p3 is not None]
    assert max(values) == pytest.approx(1 / 3)


def test_unanswerable_questions_score_none_across_the_whole_set(questions):
    """Not just Q11. All 6 of them, so a re-labeling that gives an
    unanswerable question a gold chunk fails here instead of silently
    entering Day 8's mean."""
    unanswerable = [q for q in questions.values() if not q["answerable"]]
    assert len(unanswerable) == 6
    for q in unanswerable:
        ranked = [r["chunk_id"] for r in q["retrieved"]]
        assert q["gold_chunks"] == []
        assert metrics.recall_at_k(ranked, q["gold_chunks"], 10) is None
        assert metrics.precision_at_k(ranked, q["gold_chunks"], 3) is None
        assert metrics.reciprocal_rank(ranked, q["gold_chunks"]) is None
