"""Tests for the D5a restatement sweep.

The first section is a regression guard, not a unit test, and it is the reason
this file exists. Three versions of sweep.py were written before either known
defect was used to check it, and the first two would have reported both Q14 and
Q26 clean. An instrument whose output nobody can falsify is worth nothing, so
the two labels it missed are pinned here.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import leakage                                                    # noqa: E402
import sweep                                                      # noqa: E402
from show import load_chunks                                      # noqa: E402


@pytest.fixture(scope="module")
def corpus():
    chunks = load_chunks()
    vocab = leakage.build_vocabulary(chunks)
    return chunks, vocab, leakage.document_frequency(chunks, vocab)


@pytest.fixture(scope="module")
def answers():
    return sweep.parse_answers(leakage.GOLD_FILE.read_text(encoding="utf-8"))


# ------------------------------------------------------- the regression guard --

@pytest.mark.parametrize("qid, old_gold, missed", [
    # Q14 was labeled with doc-03:c016 alone. /init is documented three times.
    ("Q14", {"doc-03:c016"}, {"doc-05:c010", "doc-06:c006"}),
    # Q26 was labeled with doc-03:c016 alone. claude doctor answers it too.
    ("Q26", {"doc-03:c016"}, {"doc-08:c006"}),
])
def test_surfaces_the_known_defects(corpus, answers, qid, old_gold, missed):
    """Given each question's pre-fix gold set, the sweep must surface the chunks
    that were actually missing. Both are real labeling defects found by hand on
    2026-08-05, so this is the one case where the right answer is known."""
    chunks, vocab, df = corpus
    keys = sweep.answer_keys(answers[qid], df, vocab)
    found = {c["id"] for c in sweep.restatement_candidates(chunks, old_gold, keys)}
    assert missed <= found, f"{qid}: sweep would have missed {sorted(missed - found)}"


# ------------------------------------------------------------------- the keys --

def test_identifiers_are_taken_from_prose_not_only_backticks(corpus):
    """Q14's answer writes "a CLAUDE.md" unbackticked, and that token is what
    separates a real restatement from a chunk mentioning `system/init`. Read
    only the backticks and the key set is just /init, which matches 28 chunks."""
    _, vocab, df = corpus
    keys = sweep.answer_keys(
        "Run `/init`, which walks you through creating a CLAUDE.md.", df, vocab)
    assert keys == {"/init", "CLAUDE.md"}


def test_backticked_english_words_are_not_keys(corpus):
    """Real answers backtick `Bash` and `description`, which match 279 and 347
    chunks. Treating those as identifiers buries the signal."""
    _, vocab, df = corpus
    keys = sweep.answer_keys("A bare tool name like `Bash` with a `description`.",
                             df, vocab)
    assert "Bash" not in keys and "description" not in keys


def test_flags_and_camel_case_survive(corpus):
    _, vocab, df = corpus
    keys = sweep.answer_keys(
        "Use `--fork-session`, and change it with `cleanupPeriodDays`.", df, vocab)
    assert {"--fork-session", "cleanupPeriodDays"} <= keys


def test_multi_word_command_spans_are_dropped(corpus):
    """`claude mcp serve` as a literal matches only the chunk it was copied
    from. Its identifier-shaped parts are picked up separately, so nothing is
    lost by skipping the whole span."""
    _, vocab, df = corpus
    assert "claude mcp serve" not in sweep.answer_keys(
        "Run it with `claude mcp serve`.", df, vocab)


# --------------------------------------------------------------- the matching --

def test_every_key_must_match(corpus):
    """Requiring any one key returned 883 candidates across the set, mostly
    chunks that name a command while documenting something else."""
    chunks, _, _ = corpus
    both = sweep.restatement_candidates(chunks, set(), {"/init", "CLAUDE.md"})
    init_only = sweep.restatement_candidates(chunks, set(), {"/init"})
    assert len(both) < len(init_only)
    assert all("claude.md" in c["text_raw"].lower() for c in both)


def test_gold_chunks_are_excluded_not_ranked(corpus):
    """The answer was written from its gold chunks, so they match by
    construction and are not what the sweep is looking for."""
    chunks, _, _ = corpus
    found = {c["id"] for c in
             sweep.restatement_candidates(chunks, {"doc-03:c016"}, {"/init", "CLAUDE.md"})}
    assert "doc-03:c016" not in found


# ------------------------------------------------------------------ the parser --

def test_answers_parse_for_every_answerable_question(answers):
    """A silently empty answer yields no keys, which the tool reports as NO KEY.
    That reads as a limitation of the question rather than a parser bug."""
    for e in leakage.parse_gold(leakage.GOLD_FILE):
        if e["answerable"]:
            assert answers[e["id"]].strip(), f"{e['id']} parsed to an empty answer"
