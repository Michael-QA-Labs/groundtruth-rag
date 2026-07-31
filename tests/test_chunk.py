"""Tests for the chunker.

The headline test is `test_chunks_reconstruct_every_document`. Everything else
protects a specific failure we either hit or measured.
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import chunk as chunker                                          # noqa: E402
from fetch_corpus import CORPUS_DIR, PAGES                       # noqa: E402


@pytest.fixture(scope="module")
def all_chunks():
    """Chunk the whole corpus once and share it across tests.

    Module-scoped because loading the tokenizer and chunking 30 documents takes
    a few seconds, and every test below wants the same result.
    """
    out = []
    for i, (_, slug) in enumerate(PAGES, start=1):
        doc_id = f"doc-{i:02d}"
        out.extend(chunker.chunk_document(CORPUS_DIR / f"{doc_id}.md", doc_id, slug))
    return out


# ------------------------------------------------------- the core invariant --

def test_chunks_reconstruct_every_document(all_chunks):
    """Chunks TILE each document: contiguous, non-overlapping, complete.

    This is the guarantee that makes gold labels safe. If a chunk ever dropped
    or duplicated content, this fails - it cannot pass 'by accident'.
    """
    by_doc: dict[str, list] = {}
    for c in all_chunks:
        by_doc.setdefault(c.doc_id, []).append(c)

    for doc_id, chunks in by_doc.items():
        original = (CORPUS_DIR / f"{doc_id}.md").read_text(encoding="utf-8")
        assert "".join(c.text_raw for c in chunks) == original, f"{doc_id} lost content"


def test_chunk_spans_are_contiguous(all_chunks):
    """Each chunk starts exactly where the previous one ended - no gaps, no
    overlaps. Reconstruction alone could in principle hide a swap; this cannot."""
    by_doc: dict[str, list] = {}
    for c in all_chunks:
        by_doc.setdefault(c.doc_id, []).append(c)

    for doc_id, chunks in by_doc.items():
        assert chunks[0].start == 0
        for prev, nxt in zip(chunks, chunks[1:]):
            assert prev.end == nxt.start, f"{doc_id}: gap or overlap at {prev.end}"


# --------------------------------------------------------- the token budget --

def test_no_chunk_exceeds_the_token_limit(all_chunks):
    """Exceeding it is not an error at embed time - the surplus is silently
    discarded - so it has to be caught here."""
    over = [(c.id, c.tokens) for c in all_chunks if c.tokens > chunker.TOKEN_LIMIT]
    assert not over, f"chunks over {chunker.TOKEN_LIMIT} tokens: {over[:5]}"


def test_chunks_are_not_wastefully_small(all_chunks):
    """Guards the opposite failure: a packing bug that flushes after every unit
    would still satisfy every test above while quadrupling the chunk count."""
    mean = sum(c.tokens for c in all_chunks) / len(all_chunks)
    assert mean > chunker.TOKEN_LIMIT * 0.6, f"mean {mean:.0f} tokens is too low"


# ------------------------------------------------------------------- IDs --

def test_ids_are_unique_sequential_and_zero_padded(all_chunks):
    seen = set()
    per_doc: dict[str, list[int]] = {}
    for c in all_chunks:
        assert c.id not in seen, f"duplicate id {c.id}"
        seen.add(c.id)
        assert re.fullmatch(r"doc-\d{2}:c\d{3}", c.id), f"bad id shape {c.id}"
        per_doc.setdefault(c.doc_id, []).append(c.index)

    for doc_id, indices in per_doc.items():
        assert indices == list(range(len(indices))), f"{doc_id} indices not sequential"


def test_ids_sort_lexicographically_in_document_order(all_chunks):
    """Three-digit padding exists so `sort` matches reading order when you grep
    these by hand on Day 4. Two digits would put c100 before c99."""
    ids = [c.id for c in all_chunks if c.doc_id == "doc-14"]
    assert ids == sorted(ids)


# ------------------------------------------------------- rendering quality --

def test_split_code_is_not_double_spaced(all_chunks):
    """Regression: pack() used to join every unit with a blank line, so an
    oversized code fence split into per-line units came out double-spaced -
    unreadable, and every blank line costing real tokens."""
    for c in all_chunks:
        if c.block_type != "code":
            continue
        assert "\n\n\n" not in c.text_embed, f"{c.id} has runaway blank lines"


def test_no_build_comments_reach_the_embedded_text(all_chunks):
    """Regression: the equivalent test in test_mdx.py passed while 104 build
    comments still reached the index, because table cells are rendered by
    tables.py and never passed through mdx.transform. Testing a module is not
    the same as testing the pipeline that uses it."""
    leaked = [c.id for c in all_chunks if "{/*" in c.text_embed]
    assert not leaked, f"{len(leaked)} chunks carry build comments: {leaked[:5]}"


def test_mdx_tags_never_reach_the_embedded_text(all_chunks):
    """Same class of gap, checked for tags rather than comments."""
    import re
    pattern = re.compile(r"</?(Tabs?|Steps?|Note|Tip|Warning|Card\w*|Accordion\w*)\b")
    leaked = [c.id for c in all_chunks
              if c.block_type != "code" and pattern.search(c.text_embed)]
    assert not leaked, f"chunks carrying MDX tags: {leaked[:5]}"


def test_every_chunk_has_embeddable_text(all_chunks):
    """A chunk whose text_embed is empty would occupy an ID and a vector slot
    while being unretrievable - dead weight in every metric."""
    empty = [c.id for c in all_chunks if not c.text_embed.strip()]
    assert not empty, f"chunks with no embeddable text: {empty[:5]}"


def test_table_rows_keep_their_column_labels(all_chunks):
    """Rendering happens at table level so a row still knows its column names
    even when the header row landed in a previous chunk."""
    table_chunks = [c for c in all_chunks if c.block_type == "table_row"]
    assert table_chunks, "expected some table chunks"
    labelled = [c for c in table_chunks if re.search(r"^\w[^\n]*: ", c.text_embed, re.M)]
    assert len(labelled) > len(table_chunks) * 0.8


# ------------------------------------------------------------ fence safety --

def test_fences_with_blank_lines_are_not_shredded():
    """18% of this corpus's fences contain a blank line. If blank-line splitting
    ran before fence extraction they would be torn up and misclassified."""
    text = (
        "Intro paragraph.\n\n"
        "```python\n"
        "first = 1\n"
        "\n"                       # the blank line that breaks naive splitting
        "second = 2\n"
        "```\n\n"
        "Closing paragraph.\n"
    )
    units = chunker.build_units(text)
    code = [u for u in units if u.kind == "code"]
    assert len(code) == 1
    assert "first = 1" in code[0].rendered
    assert "second = 2" in code[0].rendered


def test_units_tile_a_synthetic_document():
    """The tiling property, checked on hand-written input where the expected
    result is obvious rather than on real docs where it is not."""
    text = "Para one.\n\n| A | B |\n|---|---|\n| x | y |\n\n```\ncode\n```\n\nEnd.\n"
    units = chunker.build_units(text)
    assert "".join(text[u.start:u.end] for u in units) == text
