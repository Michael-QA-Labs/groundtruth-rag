"""Tests for the gold-set JSON build.

The staleness test is the one that matters. Eight labels moved during Day 5, and
a committed JSON beside a hand-edited markdown is two copies of the same facts
where only one gets updated.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import build_gold                                                 # noqa: E402
from show import load_chunks                                      # noqa: E402


@pytest.fixture(scope="module")
def built():
    return build_gold.build()


@pytest.fixture(scope="module")
def committed():
    return json.loads(build_gold.OUT.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ staleness --

def test_committed_json_matches_the_markdown(built, committed):
    """The failure this whole file exists to catch: a label edited in the
    markdown and never rebuilt into the JSON that Day 6 onward actually reads.
    Fix by running src/build_gold.py, never by editing the JSON."""
    assert committed == built, "gold/gold-set.json is stale. Run src/build_gold.py"


def test_output_is_byte_stable(built):
    """Two builds of the same input must be identical, or --check can never
    distinguish stale from merely regenerated. This is why the payload carries
    no timestamp."""
    first = json.dumps(built, indent=2, ensure_ascii=False)
    second = json.dumps(build_gold.build(), indent=2, ensure_ascii=False)
    assert first == second


# ----------------------------------------------------------------- invariants --

def test_shape_of_the_set(built):
    c = built["counts"]
    assert c["questions"] == 30
    assert c["answerable"] == 24
    assert c["unanswerable"] == 6
    assert c["answerable"] + c["unanswerable"] == c["questions"]


def test_authorship_totals_reconcile(built):
    """The counts that were wrong in three places before being made a parsed
    field. Answer authorship must account for every question, with 'none'
    exactly covering the unanswerable ones."""
    c = built["counts"]
    assert sum(c["question_author"].values()) == 30
    assert sum(c["answer_author"].values()) == 30
    assert c["answer_author"]["none"] == c["unanswerable"]
    assert c["answer_author"]["author"] == 9
    assert c["answer_author"]["claude"] == 15


def test_every_gold_chunk_exists_in_the_index(built):
    ids = {c["id"] for c in load_chunks()}
    for q in built["questions"]:
        for cid in q["gold_chunks"]:
            assert cid in ids, f"{q['id']} cites missing chunk {cid}"


def test_gold_docs_are_derived_from_gold_chunks(built):
    """Doc-level metrics fall out of chunk labels for free (template rule 1).
    Precomputing them is only safe if they cannot disagree."""
    for q in built["questions"]:
        assert q["gold_docs"] == sorted({c.split(":")[0] for c in q["gold_chunks"]})


def test_unanswerable_entries_carry_evidence_and_no_answer(built):
    """Template rule 5: unanswerable means demonstrably not covered, not "I
    couldn't find it". The evidence is the label."""
    for q in built["questions"]:
        if not q["answerable"]:
            assert not q["gold_chunks"]
            assert q["gold_answer"] is None
            assert q["not_covered_because"]
            assert q["answer_author"] == "none"


def test_answerable_entries_have_an_answer_and_no_n_a_string(built):
    """"n/a" is the template's prose for not-applicable. Leaking it through as
    a string gives a consumer a truthy value where null is meant."""
    for q in built["questions"]:
        if q["answerable"]:
            assert q["gold_answer"]
            assert q["gold_chunks"]
            assert q["not_covered_because"] is None


def test_provenance_matches_the_frozen_index(built):
    """D1: a gold label is only valid against the snapshot it was written from.
    A JSON that does not name that snapshot is not reproducible."""
    manifest = json.loads(build_gold.MANIFEST.read_text(encoding="utf-8"))
    assert built["corpus_sha256"] == manifest["corpus_sha256"]
    assert built["index"]["n_chunks"] == manifest["n_chunks"] == len(load_chunks())


# --------------------------------------------------------------- known labels --

def test_the_labels_day_5_moved_are_present(built):
    """Pins the five label changes made on Day 5, so a future re-parse that
    silently drops one fails here rather than in a metric."""
    by_id = {q["id"]: q for q in built["questions"]}
    assert set(by_id["Q14"]["gold_chunks"]) == {"doc-03:c016", "doc-05:c010", "doc-06:c006"}
    assert set(by_id["Q26"]["gold_chunks"]) == {"doc-03:c016", "doc-08:c006"}
    assert "doc-19:c008" in by_id["Q04"]["gold_chunks"]
    assert by_id["Q07"]["gold_chunks"] == ["doc-10:c004"]        # doc-26:c023 rejected, D7
    assert by_id["Q24"]["question"].startswith("How do i reinstate or resume")
