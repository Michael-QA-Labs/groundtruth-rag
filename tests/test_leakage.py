"""Tests for the vocabulary-leak check.

The unit tests use a hand-built four-document corpus rather than the real one,
so that every expected number can be counted by eye in the fixture. The last
section then asserts against the real gold set, because a parser that works on
invented markdown and not on the file it exists to read is worth nothing.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import leakage                                                    # noqa: E402
from show import load_chunks                                      # noqa: E402


def chunk(chunk_id: str, doc_id: str, text: str) -> dict:
    """Only the three fields leakage.py reads. Everything else is noise here."""
    return {"id": chunk_id, "doc_id": doc_id, "text_raw": text}


@pytest.fixture
def corpus():
    return [
        chunk("doc-01:c000", "doc-01", "Rewind undoes edits. Rewind is a hook."),
        chunk("doc-01:c001", "doc-01", "Hooks run shell commands."),
        chunk("doc-02:c000", "doc-02", "A hook fires on tool use. See settings."),
        chunk("doc-03:c000", "doc-03", "Hooks and settings.json live together."),
        chunk("doc-04:c000", "doc-04", "The hook reference: acceptEdits, 5, ok."),
    ]


@pytest.fixture
def vocab(corpus):
    return leakage.build_vocabulary(corpus)


# ------------------------------------------------------------ tokenisation --

def test_splits_on_punctuation_not_just_whitespace():
    """The decision the whole check rests on. The corpus writes `settings.json`
    and `claude-code`; a user types "settings json" and "claude code". If only
    one side is split, the two vocabularies can never intersect and the check
    reports zero leaks no matter what the gold set looks like."""
    assert leakage.tokenise("settings.json and claude-code") == [
        "settings", "json", "and", "claude", "code"]


def test_drops_short_tokens_and_bare_numbers():
    """"i" and "a" carry no evidence, and sharing the number 5 with a chunk is
    not a sign you copied anything."""
    assert leakage.tokenise("I ran it 5 times in a row") == ["ran", "times", "row"]


def test_case_is_folded_so_code_identifiers_meet_prose():
    assert leakage.tokenise("acceptEdits") == ["acceptedits"]
    assert leakage.tokenise("AcceptEdits") == leakage.tokenise("acceptedits")


# ------------------------------------------------------------- normalisation --

def test_plural_folds_only_when_the_singular_is_in_the_corpus(vocab):
    """"hooks" and "hook" are one borrowed word, so they must count as one term.
    But the fold has to be conservative: a general stemmer would happily invent
    relationships between words that only look alike."""
    assert leakage.normalise("hooks", vocab) == "hook"
    # "command" never appears in the fixture in the singular, so nothing folds.
    assert leakage.normalise("commands", vocab) == "commands"


def test_short_words_ending_in_s_are_left_alone(vocab):
    """Folding "was" to "wa" would create a term that is rare because it is not
    a word, which is exactly the kind of phantom rarity this check must not
    manufacture."""
    assert leakage.normalise("was", vocab) == "was"


# --------------------------------------------------------- document frequency --

def test_frequency_counts_documents_not_occurrences(corpus, vocab):
    """"Rewind" appears twice in one chunk of doc-01 and nowhere else, so its
    frequency is 1 page. Counting occurrences would make a term that is repeated
    on a single page look widespread, and widespread terms are the ones this
    check ignores."""
    df = leakage.document_frequency(corpus, vocab)
    assert df["rewind"] == 1
    # "hook" is on doc-01 (twice, in two chunks), doc-02, doc-03 and doc-04.
    assert df["hook"] == 4


def test_frequency_folds_plurals_before_counting(corpus, vocab):
    """doc-03 says "Hooks", doc-02 says "hook". If the fold happened after
    counting, they would be two terms at 1 and 2 pages instead of one at 4, and
    a ubiquitous word would be classified as rare."""
    df = leakage.document_frequency(corpus, vocab)
    assert "hooks" not in df


# ----------------------------------------------------------------- the check --

def test_shared_terms_are_a_set_not_a_tally(corpus, vocab):
    """Saying "rewind" three times in one question is one borrowed word. A tally
    would let a single repeated term trip the 3-word threshold on its own."""
    df = leakage.document_frequency(corpus, vocab)
    shared = leakage.shared_rare_terms(
        "rewind rewind rewind", "Rewind undoes edits.", df, vocab, df_max=2)
    assert shared == [("rewind", 1)]


def test_common_terms_are_excluded_by_the_threshold(corpus, vocab):
    """"hook" is on 4 of 4 pages here. Sharing it with a chunk is evidence of
    nothing, which is the whole reason rarity gates the count."""
    df = leakage.document_frequency(corpus, vocab)
    shared = leakage.shared_rare_terms(
        "what is a hook", "A hook fires on tool use.", df, vocab, df_max=2)
    assert shared == []


def test_results_come_back_rarest_first(corpus, vocab):
    """The output is a reading list. A term on 1 page of 4 is far more
    incriminating than one on 3, so it has to be the first thing you see."""
    df = leakage.document_frequency(corpus, vocab)
    shared = leakage.shared_rare_terms(
        "rewind the settings hook",
        "Rewind undoes edits. Hooks and settings.json live together.",
        df, vocab, df_max=4)
    assert [t for t, _ in shared] == ["rewind", "settings", "hook"]


def test_a_question_sharing_nothing_scores_zero(corpus, vocab):
    df = leakage.document_frequency(corpus, vocab)
    assert leakage.shared_rare_terms(
        "how do i deploy to production", "A hook fires on tool use.",
        df, vocab, df_max=4) == []


# ------------------------------------------------------- against the real set --

def test_parses_the_real_gold_set_without_the_worked_example():
    """The template opens with a worked example that is deliberately not one of
    the 30. It has the same field structure, so a looser parser would swallow it
    and report 31 questions into a 30-question tally."""
    entries = leakage.parse_gold(leakage.GOLD_FILE)
    assert len(entries) == 30
    assert [e["id"] for e in entries] == [f"Q{n:02d}" for n in range(1, 31)]

    answerable = [e for e in entries if e["answerable"]]
    assert len(answerable) == 24
    assert len(entries) - len(answerable) == 6


def test_every_answerable_question_has_gold_chunks_that_exist():
    """A typo in a chunk ID would silently give that question an empty gold text
    and a guaranteed zero shared terms, which reads as a clean question."""
    by_id = {c["id"] for c in load_chunks()}
    for e in leakage.parse_gold(leakage.GOLD_FILE):
        if e["answerable"]:
            assert e["gold_chunks"], f"{e['id']} is answerable with no gold chunks"
            for cid in e["gold_chunks"]:
                assert cid in by_id, f"{e['id']} cites missing chunk {cid}"
        else:
            assert not e["gold_chunks"], f"{e['id']} is unanswerable but cites chunks"
