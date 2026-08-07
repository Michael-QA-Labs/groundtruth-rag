"""Tests for the BM25 scorer.

The corpus here is three documents of six, three and three tokens, small
enough that every score below was computed on paper first and is written into
the docstring that asserts it. That matters more than usual: BM25 has two free
parameters and four places to put a 0.5, and an implementation with the wrong
one still returns plausible-looking rankings. A ranking test alone would pass
against several wrong formulas.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import keyword_search                                             # noqa: E402


def chunk(chunk_id, text):
    return {"id": chunk_id, "text_embed": text}


@pytest.fixture
def index():
    # lengths 6, 3, 3, so avgdl = 4. Every word is 3+ characters on purpose:
    # the tokeniser drops shorter ones, and "on" would silently make the first
    # document length 5 and every hand computation below wrong.
    return keyword_search.BM25Index([
        chunk("doc-01:c000", "the cat sat upon the mat"),
        chunk("doc-01:c001", "the dog sat"),
        chunk("doc-02:c000", "cats and dogs"),
    ])


# ------------------------------------------------------------ the formula --

def test_score_of_a_rare_term_matches_the_hand_computation(index):
    """Query "cat" against doc-01:c000, by hand, k1=1.2, b=0.75.

    N=3, n(cat)=1, so IDF = ln(1 + (3 - 1 + 0.5) / (1 + 0.5))
                          = ln(1 + 2.5/1.5) = ln(2.6667) = 0.98083.
    f=1, |D|=6, avgdl=4, so the denominator is
        1 + 1.2 * (1 - 0.75 + 0.75 * 6/4) = 1 + 1.2 * 1.375 = 2.65
    and the numerator is 1 * (1.2 + 1) = 2.2.
    score = 0.98083 * 2.2 / 2.65 = 0.81427.

    "cats" in doc-02 is a different token: there is no stemmer, deliberately,
    because adding one would be a second untested change inside the variant
    Day 11 has to attribute a difference to.
    """
    scores = index.score("cat")
    assert scores["doc-01:c000"] == pytest.approx(0.81427, abs=1e-5)
    assert scores["doc-02:c000"] == 0.0


def test_a_term_in_every_document_scores_far_below_a_rare_one(index):
    """"the" is in 2 of 3 documents, "mat" in 1.

    IDF("the") = ln(1 + (3 - 2 + 0.5)/(2 + 0.5)) = ln(1.6) = 0.47000
    IDF("mat") = ln(1 + 2.5/1.5) = 0.98083

    The Okapi form keeps common terms positive rather than negative, which is
    the whole reason no stopword list is needed here. Q02's "how do i import a
    plugin" is five stopwords and two content words, and this is what stops
    the five from steering the result.
    """
    assert index.idf("the") == pytest.approx(0.47000, abs=1e-5)
    assert index.idf("mat") == pytest.approx(0.98083, abs=1e-5)
    assert index.idf("the") < index.idf("mat")


def test_the_same_term_scores_higher_in_the_shorter_document():
    """Length normalisation, which is the only reason to prefer BM25 over raw
    term frequency on this corpus. Chunks run from a few tokens to 254, and
    without b=0.75 the long ones win every query by having more words."""
    idx = keyword_search.BM25Index([
        chunk("short", "hooks"),
        chunk("long", "hooks " + " ".join(f"word{i}" for i in range(50))),
    ])
    scores = idx.score("hooks")
    assert scores["short"] > scores["long"]


def test_repeated_query_terms_are_counted_once_per_occurrence(index):
    """"sat sat" is a degenerate query, but it pins that the sum is over query
    terms rather than over the query's distinct vocabulary."""
    once = index.score("sat")["doc-01:c001"]
    twice = index.score("sat sat")["doc-01:c001"]
    assert twice == pytest.approx(2 * once)


def test_a_term_absent_from_the_corpus_contributes_nothing(index):
    assert index.score("kubernetes") == index.score("")


def test_an_empty_query_scores_every_chunk_zero(index):
    assert set(index.score("").values()) == {0.0}


# ------------------------------------------------------------- the ranking --

def test_search_returns_chunk_ids_best_first(index):
    assert index.search("dog", top=2)[0] == "doc-01:c001"


def test_ties_break_by_chunk_id_so_the_ranking_is_reproducible():
    """Four groups of chunks in the real index have byte-identical text and
    therefore identical scores. run_retrieval.py already pins this convention
    for the dense side; a different convention here would make the two lists
    disagree for reasons that have nothing to do with retrieval."""
    idx = keyword_search.BM25Index([
        chunk("doc-09:c001", "identical text"),
        chunk("doc-02:c003", "identical text"),
        chunk("doc-05:c000", "identical text"),
    ])
    assert idx.search("identical", top=3) == [
        "doc-02:c003", "doc-05:c000", "doc-09:c001"]


def test_search_can_return_the_whole_index(index):
    """Day 9 fuses full-depth lists, not top-10s. A chunk absent from one list
    entirely is different from a chunk ranked last in it, and RRF needs the
    difference."""
    assert len(index.search("cat", top=None)) == 3


def test_a_chunk_scoring_zero_still_has_a_rank(index):
    """Every chunk must appear in the full ranking. Otherwise fusion silently
    treats "no keyword match" as "not a candidate", and the dense side's
    contribution disappears for any query with a rare term."""
    ranked = index.search("cat", top=None)
    assert set(ranked) == {"doc-01:c000", "doc-01:c001", "doc-02:c000"}
    assert ranked[0] == "doc-01:c000"


# ------------------------------------------------------------ construction --

def test_index_rejects_an_empty_corpus():
    with pytest.raises(ValueError):
        keyword_search.BM25Index([])


def test_index_uses_the_same_tokeniser_as_the_leak_check():
    """`settings.json` in the docs against "settings json" from a user.

    If the two sides tokenise differently the keyword retriever cannot match
    the thing it exists to match, and D6's leak numbers would describe a
    vocabulary the retriever never sees.
    """
    idx = keyword_search.BM25Index([chunk("doc-07:c000", "edit settings.json now")])
    assert idx.score("settings")["doc-07:c000"] > 0
    assert idx.score("json")["doc-07:c000"] > 0


def test_query_terms_under_three_characters_are_dropped():
    """Inherited from leakage.tokenise, and worth pinning here because it has
    a second effect that is easy to miss.

    It is right for the leak check: sharing "an" with a chunk is not evidence.
    It is mostly right here too, since it removes "do", "i", "my" and "to"
    from questions like "how do i set-up claude code in my CLI" without a
    stopword list. But it also shortens every document, which changes avgdl
    and therefore every length-normalised score. It cost this file one wrong
    hand computation before it was noticed.

    The one real loss: `-p`, `ls` and `cd` cannot be matched. No question in
    the gold set turns on any of them.
    """
    idx = keyword_search.BM25Index([chunk("doc-01:c000", "run it in my cli now")])
    scores = idx.score("it my")
    assert scores["doc-01:c000"] == 0.0
    assert idx.score("cli")["doc-01:c000"] > 0
