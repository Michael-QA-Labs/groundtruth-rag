"""Tests for the judge-pool sampler.

Three of these matter more than the rest, because they catch errors that
produce a sampler that runs, emits 100 plausible-looking pairs, and quietly
destroys the measurement:

`test_pool_order_does_not_encode_gold_status` catches an unshuffled pool. Gold
chunks are assembled before negatives, so the natural implementation emits them
first every time. A judge that learns "the early ones are the answer" scores
well for a reason that has nothing to do with D5, and kappa then measures
position, not judgment.

`test_negatives_are_drawn_only_from_that_questions_own_retrieved_chunks`
catches negatives pulled from the wrong question, or from the whole index. Both
versions produce the right *counts*, and both replace the hard near-misses the
design depends on with chunks that are trivially irrelevant, which inflates
agreement.

`test_every_pool_contains_all_of_its_questions_gold_chunks` catches a pool that
cannot answer the question it asks. The judge is asked for a minimal sufficient
subset; if the gold is not all present, no subset is sufficient and the task is
unanswerable rather than hard.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import build_judge_pools                                          # noqa: E402


SEED = 20260813


# ------------------------------------------------------------------ fixtures --

def tiny_gold():
    """Three questions, one of them unanswerable.

    Gold counts differ (Q01 has 2, Q02 has 1, Q04 has 3), which is what the
    scaling rule keys on.
    """
    return {
        "questions": [
            {"id": "Q01", "answerable": True,
             "gold_chunks": ["doc-01:c001", "doc-01:c002"],
             "question": "how do i install it",
             "gold_answer": "Run the install script."},
            {"id": "Q02", "answerable": True,
             "gold_chunks": ["doc-02:c001"],
             "question": "where do settings live",
             "gold_answer": "In settings.json."},
            {"id": "Q03", "answerable": False,
             "gold_chunks": [],
             "question": "what is the roadmap",
             "gold_answer": None},
            {"id": "Q04", "answerable": True,
             "gold_chunks": ["doc-04:c001", "doc-04:c002", "doc-04:c003"],
             "question": "how do i extract json",
             "gold_answer": "Pipe the output through a schema."},
        ]
    }


def tiny_retrieval():
    """Mirrors results/retrieval-baseline.json: `retrieved` holds dicts with
    rank/chunk_id/score, not bare id strings. Gold is deliberately not rank 1
    for Q02."""

    def ranked(*ids):
        return [{"rank": i, "chunk_id": c, "score": 0.9 - i / 100}
                for i, c in enumerate(ids, 1)]

    return {
        "questions": [
            {"id": "Q01", "answerable": True,
             "gold_chunks": ["doc-01:c001", "doc-01:c002"],
             "retrieved": ranked("doc-01:c001", "doc-09:c001", "doc-09:c002",
                                 "doc-01:c002", "doc-09:c003", "doc-09:c004")},
            {"id": "Q02", "answerable": True,
             "gold_chunks": ["doc-02:c001"],
             "retrieved": ranked("doc-08:c001", "doc-02:c001", "doc-08:c002",
                                 "doc-08:c003")},
            {"id": "Q03", "answerable": False,
             "gold_chunks": [],
             "retrieved": ranked("doc-07:c001", "doc-07:c002")},
            {"id": "Q04", "answerable": True,
             "gold_chunks": ["doc-04:c001", "doc-04:c002", "doc-04:c003"],
             "retrieved": ranked("doc-04:c001", "doc-06:c001", "doc-04:c002",
                                 "doc-06:c002", "doc-06:c003", "doc-04:c003",
                                 "doc-06:c004", "doc-06:c005")},
        ]
    }


# ------------------------------------------------------------- what is built --

def test_only_answerable_questions_get_a_pool():
    """Q03 is unanswerable, so there is no gold answer to be sufficient for."""
    pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                          seed=SEED, min_negatives=2)

    assert [p["id"] for p in pools] == ["Q01", "Q02", "Q04"]


def test_every_pool_contains_all_of_its_questions_gold_chunks():
    """Sufficiency by construction: a minimal subset must exist to be found."""
    pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                          seed=SEED, min_negatives=2)
    by_id = {p["id"]: p for p in pools}

    assert set(by_id["Q01"]["candidates"]) >= {"doc-01:c001", "doc-01:c002"}
    assert set(by_id["Q02"]["candidates"]) >= {"doc-02:c001"}


# --------------------------------------------------------------- the negatives --

def test_pool_size_is_a_questions_gold_count_plus_its_negatives():
    """Pool size is that question's gold count plus its negative allocation."""
    pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                          seed=SEED, min_negatives=2)
    by_id = {p["id"]: p for p in pools}

    assert len(by_id["Q01"]["candidates"]) == 2 + 2
    assert len(by_id["Q02"]["candidates"]) == 1 + 2


def test_negatives_are_drawn_only_from_that_questions_own_retrieved_chunks():
    """The design depends on negatives being near-misses this retriever made.

    Drawing from another question, or from the whole index, yields the right
    count and the wrong chunks: trivially irrelevant text that both raters
    dismiss instantly, which inflates agreement.
    """
    pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                          seed=SEED, min_negatives=2)
    by_id = {p["id"]: p for p in pools}

    q01_negatives = set(by_id["Q01"]["candidates"]) - {"doc-01:c001", "doc-01:c002"}
    q02_negatives = set(by_id["Q02"]["candidates"]) - {"doc-02:c001"}

    assert q01_negatives <= {"doc-09:c001", "doc-09:c002", "doc-09:c003", "doc-09:c004"}
    assert q02_negatives <= {"doc-08:c001", "doc-08:c002", "doc-08:c003"}


def test_negatives_scale_with_gold_so_no_pool_is_ever_gold_majority():
    """A pool where most candidates are required is a different task.

    The rater is asked for the minimal sufficient subset, so a 5-gold pool with
    3 distractors rewards answering "nearly all of them" while a 1-gold pool
    punishes it. Drawing one negative per gold chunk keeps every pool at worst
    an even split, so no single question can drive kappa with a shape none of
    the others have.
    """
    pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                          seed=SEED, min_negatives=2)

    for pool in pools:
        gold_here = {"Q01": 2, "Q02": 1, "Q04": 3}[pool["id"]]
        assert gold_here <= len(pool["candidates"]) - gold_here


def test_a_question_with_three_gold_chunks_draws_three_negatives():
    """The floor of two only binds below three gold."""
    pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                          seed=SEED, min_negatives=2)
    by_id = {p["id"]: p for p in pools}

    assert len(by_id["Q04"]["candidates"]) == 3 + 3


def test_a_single_gold_question_still_gets_the_floor_of_two_negatives():
    """Without a floor a 1-gold question would be judged against one
    distractor, which is barely a choice at all."""
    pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                          seed=SEED, min_negatives=2)
    by_id = {p["id"]: p for p in pools}

    assert len(by_id["Q02"]["candidates"]) == 1 + 2


# ------------------------------------------------------- order and stability --

def test_pool_order_does_not_encode_gold_status():
    """Gold is assembled before negatives, so the unshuffled pool lists it
    first every single time.

    A judge that picks up on "the early ones are the answer" scores well for a
    reason unrelated to D5, and kappa then measures position rather than
    judgment. The same trap catches the human rater.
    """
    first_gold_positions = set()
    for seed in range(40):
        pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                              seed=seed, min_negatives=2)
        q01 = next(p for p in pools if p["id"] == "Q01")
        gold = {"doc-01:c001", "doc-01:c002"}
        first_gold_positions.add(
            next(i for i, c in enumerate(q01["candidates"]) if c in gold))

    # An unshuffled pool puts gold first on every seed, giving {0}.
    assert first_gold_positions != {0}


def test_the_same_seed_rebuilds_byte_identical_pools():
    """The pools are committed and hand-labelled against. A rebuild that moved
    them would silently invalidate labels already made."""
    first = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                          seed=SEED, min_negatives=2)
    second = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                           seed=SEED, min_negatives=2)

    assert first == second


def test_a_different_seed_draws_different_negatives():
    """Guards against a seed that is accepted and then ignored, which would
    make every 'reproducible' claim about the draw vacuous."""
    drawn = set()
    for seed in (1, 2, 3, 4, 5):
        pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                              seed=seed, min_negatives=2)
        q01 = next(p for p in pools if p["id"] == "Q01")
        drawn.add(tuple(sorted(set(q01["candidates"])
                               - {"doc-01:c001", "doc-01:c002"})))

    assert len(drawn) > 1


# ---------------------------------------------------------- the answer key --

def test_pools_carry_nothing_that_marks_which_candidates_are_gold():
    """The pools file is what you label against. Any field naming the gold
    chunks turns the labelling exercise into a transcription exercise."""
    pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                          seed=SEED, min_negatives=2)

    for pool in pools:
        assert set(pool) == {"id", "question", "gold_answer", "candidates"}


def test_key_records_gold_status_for_every_candidate_in_every_pool():
    """One row per pair, which is what kappa is computed over."""
    pools = build_judge_pools.build_pools(tiny_gold(), tiny_retrieval(),
                                          seed=SEED, min_negatives=2)
    key = build_judge_pools.build_key(pools, tiny_gold())

    assert len(key) == sum(len(p["candidates"]) for p in pools)

    gold_rows = {(r["question_id"], r["chunk_id"]) for r in key if r["gold"]}
    assert gold_rows == {("Q01", "doc-01:c001"),
                         ("Q01", "doc-01:c002"),
                         ("Q02", "doc-02:c001"),
                         ("Q04", "doc-04:c001"),
                         ("Q04", "doc-04:c002"),
                         ("Q04", "doc-04:c003")}


# ------------------------------------------------------------- the hash gate --

def test_pools_refuse_to_build_when_the_two_inputs_disagree_on_the_corpus():
    """The same refusal `run_retrieval.py` makes.

    Gold labels and a retrieval run taken against different corpus snapshots
    would still join cleanly on chunk id and produce 100 pairs, some of which
    point at text that has since moved.
    """
    gold = dict(tiny_gold(), corpus_sha256="aaa")
    retrieval = dict(tiny_retrieval(), corpus_sha256="bbb")

    with pytest.raises(ValueError, match="corpus"):
        build_judge_pools.build_pools(gold, retrieval, seed=SEED,
                                      min_negatives=2)


# ----------------------------------------------------------- attaching text --

def test_attached_chunk_text_is_the_raw_slice_not_the_embedding_rendering():
    """`text_embed` is the transformed rendering the retriever sees. Labelling
    against it would judge a chunk by text that is not in the corpus, which is
    the mistake notes/chunk-inspection.md exists to prevent.
    """
    pools = [{"id": "Q01", "question": "q", "gold_answer": "a",
              "candidates": ["doc-01:c001"]}]
    chunks = [{"id": "doc-01:c001",
               "text_raw": "| Mode | Effect |\n| acceptEdits | auto-approves |",
               "text_embed": "Mode Effect acceptEdits auto-approves"}]

    attached = build_judge_pools.attach_text(pools, chunks)

    assert attached[0]["candidates"][0]["text"] == chunks[0]["text_raw"]


def test_attaching_text_fails_loudly_on_a_chunk_id_the_index_does_not_have():
    """A silent skip would emit a pool with fewer candidates than the key
    expects, and the mismatch would not surface until kappa."""
    pools = [{"id": "Q01", "question": "q", "gold_answer": "a",
              "candidates": ["doc-99:c999"]}]

    with pytest.raises(KeyError, match="doc-99:c999"):
        build_judge_pools.attach_text(pools, [])
