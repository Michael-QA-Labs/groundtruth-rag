"""Tests for the Day 8 aggregation.

Synthetic fixtures again, and for a sharper reason than in test_metrics.py.
The aggregation is where a wrong answer is least visible: `metrics.py` returns
a number you can check against one ranked list you can read, but a mean over
24 questions looks equally plausible at 0.36 and 0.28. The only way to know
which is right is to average a set small enough to verify by eye.

The fixture below is 4 questions, 3 answerable and 1 not, with numbers chosen
so every aggregate has an exact value.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import report                                                     # noqa: E402


def question(qid, answerable, gold, ranked):
    return {
        "id": qid,
        "question": f"question {qid}",
        "answerable": answerable,
        "gold_chunks": gold,
        "retrieved": [{"chunk_id": c, "rank": i + 1, "score": 0.5}
                      for i, c in enumerate(ranked)],
    }


# Ten ranks each, so k=10 is legal. A1 has gold at rank 1, A2 at rank 5,
# A3 has none at all, U1 is unanswerable.
TEN = [f"doc-01:c{i:03d}" for i in range(10)]


@pytest.fixture
def questions():
    return [
        question("A1", True, ["doc-01:c000"], TEN),
        question("A2", True, ["doc-01:c004"], TEN),
        question("A3", True, ["doc-09:c999"], TEN),
        question("U1", False, [], TEN),
    ]


# ------------------------------------------------------- the SDK doc set --

INDEX_SNIPPET = """
| doc-01 | `overview` | https://code.claude.com/docs/en/overview.md | 100 | 2026-07-29 |
| doc-23 | `output-styles` | https://code.claude.com/docs/en/output-styles.md | 100 | 2026-07-29 |
| doc-24 | `agent-sdk/overview` | https://code.claude.com/docs/en/agent-sdk/overview.md | 100 | 2026-07-29 |
| doc-29 | `agent-sdk/cost-tracking` | https://code.claude.com/docs/en/agent-sdk/cost-tracking.md | 100 | 2026-07-29 |
"""


def test_sdk_docs_are_read_from_the_index_not_hardcoded():
    """The reason this is parsed rather than typed as a range.

    An earlier pass at Day 8 assumed the SDK pages were doc-20 to doc-27 and
    counted doc-23 `output-styles`, a CLI page, as a product-surface confusion
    while missing doc-28 to doc-30 entirely. D7's whole free failure category
    depends on this set being exactly the seven agent-sdk pages.
    """
    assert report.parse_sdk_docs(INDEX_SNIPPET) == {"doc-24", "doc-29"}


def test_a_cli_page_whose_name_merely_contains_sdk_is_not_counted():
    text = "| doc-05 | `sdk-comparison` | https://x/sdk-comparison.md | 1 | d |"
    assert report.parse_sdk_docs(text) == set()


# ------------------------------------------------------------- per row --

def test_answerable_row_carries_gold_size_next_to_the_score(questions):
    """D5b's requirement, enforced in the data rather than in the prose.
    Recall is unreadable without |gold| beside it."""
    row = report.score(questions[0], sdk_docs=set())
    assert row["n_gold"] == 1
    assert row["recall_at_10"] == 1.0
    assert row["first_relevant_rank"] == 1


def test_unanswerable_row_has_no_scores(questions):
    row = report.score(questions[3], sdk_docs=set())
    assert row["recall_at_10"] is None
    assert row["precision_at_3"] is None
    assert row["n_gold"] == 0


def test_sdk_hits_counts_only_the_top_ten(questions):
    """Rank 11 and beyond are stored for diagnosis, not for this count."""
    q = question("A4", True, ["doc-01:c000"],
                 TEN[:9] + ["doc-24:c000"] + ["doc-24:c001"])
    row = report.score(q, sdk_docs={"doc-24"})
    assert row["sdk_hits"] == 1


# ---------------------------------------------------------- aggregates --

def test_means_are_taken_over_answerable_questions_only(questions):
    """A1 = 1.0, A2 = 1.0, A3 = 0.0, and U1 is not a zero, it is excluded.

    Mean over 3 is 2/3. Mean over 4, counting the unanswerable as a miss,
    is 0.5. The 6 real unanswerable questions are 20% of this gold set, so
    this is the difference between 0.36 and 0.29 on the real data.
    """
    rows = [report.score(q, sdk_docs=set()) for q in questions]
    agg = report.aggregate(rows)
    assert agg["n_answerable"] == 3
    assert agg["n_unanswerable"] == 1
    assert agg["mean_recall_at_10"] == pytest.approx(2 / 3)


def test_a_retrieved_nothing_question_is_a_zero_not_an_exclusion(questions):
    """A3 has gold and none of it was found. Dropping it would report the
    mean over the questions that worked, which is the flattering error D8
    exists to prevent."""
    rows = [report.score(q, sdk_docs=set()) for q in questions]
    agg = report.aggregate(rows)
    assert agg["n_no_gold_in_top_10"] == 1
    assert agg["mrr"] == pytest.approx((1.0 + 0.2 + 0.0) / 3)


def test_counts_of_the_two_extremes(questions):
    rows = [report.score(q, sdk_docs=set()) for q in questions]
    agg = report.aggregate(rows)
    assert agg["n_gold_at_rank_1"] == 1


def test_aggregate_refuses_an_empty_answerable_set():
    """A results file with no answerable questions would otherwise divide by
    zero and report a mean of nan, which prints as a number."""
    rows = [report.score(question("U1", False, [], TEN), sdk_docs=set())]
    with pytest.raises(ValueError):
        report.aggregate(rows)


# ------------------------------------------------------------- rendering --

def test_rendered_report_names_the_corpus_and_index_it_describes(questions):
    """Every number in the file is a function of these two hashes. A report
    that does not carry them cannot be checked later against the index that
    produced it."""
    rows = [report.score(q, sdk_docs=set()) for q in questions]
    text = report.render(
        rows, report.aggregate(rows),
        meta={"corpus_sha256": "abc123", "vectors_sha256": "def456",
              "model": "test-model", "variant": "test-variant", "top": 10},
        date="2026-08-06",
    )
    assert "abc123"[:16] in text
    assert "test-variant" in text
    for q in questions:
        assert q["id"] in text


def test_rendered_report_shows_undefined_rather_than_a_dash_for_unanswerable(questions):
    rows = [report.score(q, sdk_docs=set()) for q in questions]
    text = report.render(
        rows, report.aggregate(rows),
        meta={"corpus_sha256": "a", "vectors_sha256": "b", "model": "m",
              "variant": "v", "top": 10},
        date="2026-08-06",
    )
    u1_line = [l for l in text.splitlines() if l.startswith("| U1 ")][0]
    assert "undefined" in u1_line
