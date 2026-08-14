"""Tests for the hand-labeling tool.

Every test here exists for the same reason the sampler's tests do: the failure
mode that matters is not a crash, it is a tool that runs, writes 99
plausible-looking rows, and quietly destroys the measurement. You would never
see it, because the whole point of the labels is that nothing else can check
them.

`test_displayed_number_one_selects_the_first_candidate` catches the off-by-one.
The screen numbers candidates from 1 and the list is indexed from 0, so a
one-character error shifts every label by one position and kappa then measures
an offset. Nothing downstream can detect it.

`test_a_row_is_written_for_every_candidate_not_only_the_chosen_ones` catches the
natural implementation, which writes what you selected. The negatives are 55 of
the 99 pairs; a tool that only records the necessary ones silently drops them
and leaves kappa with no marginal to work against.

`test_blank_input_is_refused_rather_than_read_as_none` catches the accident.
Enter is the easiest key to hit while reading 10 chunks, and if it means "no
chunk is necessary" then a slip writes a whole pool of zeros that looks exactly
like a real judgment.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import label                                                      # noqa: E402


# ------------------------------------------------------------------ fixtures --

def tiny_pool():
    """One pool of three candidates, in the order they would be displayed."""
    return {
        "id": "Q02",
        "question": "where do settings live",
        "gold_answer": "In settings.json.",
        "candidates": [
            {"id": "doc-02:c001", "text": "settings.json holds them"},
            {"id": "doc-07:c014", "text": "most keys reload into the session"},
            {"id": "doc-02:c009", "text": "an unrelated paragraph"},
        ],
    }


# ------------------------------------------------------------------ parsing --

def test_displayed_number_one_selects_the_first_candidate():
    pool = tiny_pool()
    assert label.parse_selection("1", pool["candidates"]) == ["doc-02:c001"]


def test_two_numbers_select_two_candidates():
    pool = tiny_pool()
    assert label.parse_selection("1 3", pool["candidates"]) == [
        "doc-02:c001", "doc-02:c009"]


def test_commas_separate_as_well_as_spaces():
    pool = tiny_pool()
    assert label.parse_selection("1,3", pool["candidates"]) == [
        "doc-02:c001", "doc-02:c009"]


def test_none_selects_nothing():
    """An empty minimal set is a real judgment, and it disagrees with the gold
    set, which put at least one gold chunk in every pool. It has to be sayable,
    but only on purpose."""
    assert label.parse_selection("none", tiny_pool()["candidates"]) == []


def test_blank_input_is_refused_rather_than_read_as_none():
    with pytest.raises(ValueError):
        label.parse_selection("   ", tiny_pool()["candidates"])


def test_a_number_past_the_end_of_the_pool_is_refused():
    with pytest.raises(ValueError):
        label.parse_selection("4", tiny_pool()["candidates"])


def test_zero_is_refused_because_the_screen_counts_from_one():
    with pytest.raises(ValueError):
        label.parse_selection("0", tiny_pool()["candidates"])


def test_a_repeated_number_is_refused():
    """Typing "1 1 2" means you lost your place, not that c001 counts twice."""
    with pytest.raises(ValueError):
        label.parse_selection("1 1 2", tiny_pool()["candidates"])


def test_words_are_refused():
    with pytest.raises(ValueError):
        label.parse_selection("the first one", tiny_pool()["candidates"])


# -------------------------------------------------------------------- rows --

def test_a_row_is_written_for_every_candidate_not_only_the_chosen_ones():
    rows = label.rows_for(tiny_pool(), ["doc-02:c001"])
    assert [r["chunk_id"] for r in rows] == [
        "doc-02:c001", "doc-07:c014", "doc-02:c009"]


def test_only_the_chosen_candidates_are_marked_necessary():
    rows = label.rows_for(tiny_pool(), ["doc-02:c001", "doc-02:c009"])
    assert [r["necessary"] for r in rows] == [1, 0, 1]


def test_rows_carry_the_question_id():
    rows = label.rows_for(tiny_pool(), [])
    assert {r["question_id"] for r in rows} == {"Q02"}


# ------------------------------------------------------------------ resume --

def test_a_question_already_in_the_csv_is_not_offered_again():
    csv_text = ("question_id,chunk_id,necessary\n"
                "Q02,doc-02:c001,1\n"
                "Q02,doc-07:c014,0\n")
    assert label.labeled_questions(csv_text) == {"Q02"}


def test_the_header_row_is_not_mistaken_for_a_question():
    assert label.labeled_questions("question_id,chunk_id,necessary\n") == set()


def test_no_file_yet_means_nothing_is_labeled():
    assert label.labeled_questions("") == set()
