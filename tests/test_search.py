"""Tests for search.

Deliberately avoids loading the embedding model: these check the ranking maths
and the integrity of the built index, both of which are testable without
spending seconds per run on model weights.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import search                                                    # noqa: E402
from chunk import INDEX_DIR                                      # noqa: E402


# ------------------------------------------------------------ ranking maths --

def test_dot_product_ranks_by_angle_when_normalised():
    """The premise search.py rests on: with unit-length vectors, a dot product
    IS cosine similarity, so the nearest direction scores highest."""
    vectors = np.array([
        [1.0, 0.0],      # identical direction to the query
        [0.7071, 0.7071],  # 45 degrees away
        [0.0, 1.0],      # perpendicular
        [-1.0, 0.0],     # opposite
    ], dtype=np.float32)
    query = np.array([1.0, 0.0], dtype=np.float32)

    scores = vectors @ query
    assert list(np.argsort(-scores, kind="stable")) == [0, 1, 2, 3]
    assert scores[0] == pytest.approx(1.0)
    assert scores[2] == pytest.approx(0.0)
    assert scores[3] == pytest.approx(-1.0)


def test_ties_break_deterministically_by_position():
    """4 groups of chunks in this corpus have identical text and therefore
    identical scores. An unstable sort would let their order vary between runs,
    making every metric irreproducible."""
    vectors = np.array([[1.0, 0.0]] * 5, dtype=np.float32)   # all identical
    query = np.array([1.0, 0.0], dtype=np.float32)
    scores = vectors @ query

    first = list(np.argsort(-scores, kind="stable"))
    for _ in range(20):
        assert list(np.argsort(-scores, kind="stable")) == first
    assert first == [0, 1, 2, 3, 4]


# --------------------------------------------------- doc-level collapsing --

def test_to_docs_keeps_first_occurrence_and_rank_order():
    hits = [
        ("doc-05:c010", 0.9),
        ("doc-05:c011", 0.8),      # same doc, must not take a second slot
        ("doc-10:c003", 0.7),
        ("doc-02:c000", 0.6),
    ]
    assert search.to_docs(hits, 3) == [("doc-05", 0.9), ("doc-10", 0.7), ("doc-02", 0.6)]


def test_to_docs_top_means_distinct_docs_not_chunks():
    """'Top 3 docs' = the first 3 DISTINCT documents. Fixing this definition in
    code is what stops Day 6's hand arithmetic and Day 7's implementation from
    disagreeing about a non-bug."""
    hits = [(f"doc-07:c{i:03d}", 0.9 - i / 100) for i in range(5)]
    hits.append(("doc-11:c000", 0.4))
    assert search.to_docs(hits, 3) == [("doc-07", 0.9), ("doc-11", 0.4)]


# ------------------------------------------------------- index integrity --

@pytest.fixture(scope="module")
def built_index():
    if not (INDEX_DIR / "vectors.npz").exists():
        pytest.skip("index not built - run src/embed.py")
    data = np.load(INDEX_DIR / "vectors.npz", allow_pickle=False)
    with (INDEX_DIR / "chunks.jsonl").open(encoding="utf-8") as fh:
        chunks = {r["id"]: r for r in map(json.loads, fh)}
    manifest = json.loads((INDEX_DIR / "manifest.json").read_text(encoding="utf-8"))
    return data["ids"], data["vectors"], chunks, manifest


def test_every_vector_has_a_matching_chunk(built_index):
    """Joining by ID only helps if every ID actually resolves."""
    ids, vectors, chunks, _ = built_index
    assert len(ids) == len(vectors)
    assert len(set(ids)) == len(ids), "duplicate ids in vectors.npz"
    assert not [i for i in ids if i not in chunks]


def test_vectors_are_unit_length(built_index):
    """If this drifts, dot products stop being cosine similarity and every
    ranking is subtly wrong while still looking plausible."""
    _, vectors, _, _ = built_index
    norms = np.linalg.norm(vectors, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-4)


def test_manifest_matches_the_built_index(built_index):
    ids, vectors, chunks, manifest = built_index
    assert manifest["n_chunks"] == len(chunks) == len(ids)
    assert manifest["embedding_dim"] == vectors.shape[1]
    assert manifest["normalized"] is True
    assert sum(manifest["chunks_per_doc"].values()) == len(chunks)


def test_manifest_records_what_produced_the_vectors(built_index):
    """Traceability: a Day 12 README number must be attributable to a corpus, a
    model and a commit, not merely hoped to be current."""
    *_, manifest = built_index
    for key in ("corpus_sha256", "vectors_sha256", "git_sha", "model", "versions"):
        assert manifest.get(key), f"manifest missing {key}"
    assert len(manifest["corpus_sha256"]) == 64
