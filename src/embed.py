"""Embed the chunks into vectors.

Run:  .venv/bin/python src/embed.py

Reads  index/chunks.jsonl
Writes index/vectors.npz      ids + float32 matrix
       index/manifest.json    everything needed to reproduce or invalidate them

WHAT A VECTOR IS, BRIEFLY
-------------------------
The model turns each chunk into a list of 384 numbers. Chunks about similar
things end up pointing in similar directions. Searching is then just: turn the
question into 384 numbers too, and find the chunks pointing most nearly the
same way.

WHY WE NORMALISE
----------------
Cosine similarity is the angle between two vectors, ignoring their lengths.
Computing it properly means dividing by both magnitudes:

    cos(a, b) = (a . b) / (|a| * |b|)

If instead every vector is scaled to length 1 up front, both magnitudes are 1
and the formula collapses to just `a . b` - a plain dot product. That makes
search a single matrix multiply, and removes a whole class of silent bug where
you write `a @ b`, call it cosine similarity, and quietly get rankings weighted
by chunk length. The rankings would still look plausible; nothing would alert
you.

So: normalise once, here, and assert it held.

WHAT THE MANIFEST IS FOR
------------------------
corpus/INDEX.md pins the DATA with a hash. requirements.txt pins the CODE.
manifest.json ties a specific set of vectors to both, plus the model and the git
commit that produced them. On Day 12 a number in the README can then be traced
to every input that produced it, instead of being a number you hope is current.
"""

import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from chunk import INDEX_DIR, MODEL_NAME, TOKEN_LIMIT
from fetch_corpus import CORPUS_DIR, PAGES

# MiniLM is symmetric: questions and documents go through the model the same
# way. Some other models (E5, BGE) require "query: " / "passage: " prefixes, and
# forgetting them silently halves retrieval quality. Recorded in the manifest so
# a future model swap has to confront the question rather than inherit a default.
QUERY_PREFIX = ""
PASSAGE_PREFIX = ""


def corpus_hash() -> str:
    """Re-derive the corpus fingerprint from the files on disk."""
    digest = hashlib.sha256()
    for i in range(1, len(PAGES) + 1):
        digest.update((CORPUS_DIR / f"doc-{i:02d}.md").read_bytes())
    return digest.hexdigest()


def recorded_corpus_hash() -> str:
    """The hash corpus/INDEX.md claims, so we can prove they still agree."""
    import re
    text = (CORPUS_DIR / "INDEX.md").read_text(encoding="utf-8")
    return re.search(r"sha256: `([0-9a-f]{64})`", text).group(1)


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
            cwd=Path(__file__).resolve().parent.parent,
        ).stdout.strip()
    except Exception:
        return "unknown"


def load_chunks() -> list[dict]:
    path = INDEX_DIR / "chunks.jsonl"
    if not path.exists():
        sys.exit("index/chunks.jsonl not found - run src/chunk.py first")
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def duplicate_groups(chunks: list[dict]) -> list[list[str]]:
    """Chunks whose normalised text is identical, grouped.

    Measured during design: 8 substantial blocks appear in more than one
    document. That matters on Day 4 - if an answer lives in two places and only
    one is labelled gold, retrieving the other scores as a failure when it was
    actually correct. Surfacing the groups lets both get labelled.
    """
    by_hash: dict[str, list[str]] = defaultdict(list)
    for c in chunks:
        by_hash[c["sha256_norm"]].append(c["id"])
    return [sorted(ids) for ids in by_hash.values() if len(ids) > 1]


def main() -> None:
    from sentence_transformers import SentenceTransformer

    chunks = load_chunks()
    print(f"loaded {len(chunks):,} chunks")

    # 1. The corpus must not have moved under us. Vectors built against a
    #    different corpus than the one INDEX.md names would be undetectably
    #    wrong later, which is precisely the Day 1 drift problem one layer up.
    actual, recorded = corpus_hash(), recorded_corpus_hash()
    if actual != recorded:
        sys.exit(f"CORPUS DRIFT\n  INDEX.md: {recorded}\n  on disk:  {actual}")
    print(f"corpus hash verified: {actual[:16]}...")

    print(f"loading {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    # 2. Prove nothing truncates, using the model's own tokenizer rather than a
    #    chars-per-token estimate. The chunker already enforces this, so it
    #    should never fire - but "should never fire" is the reason to check,
    #    since the failure it guards against is invisible in the output.
    texts = [PASSAGE_PREFIX + c["text_embed"] for c in chunks]
    over = [
        (chunks[i]["id"], n)
        for i, n in enumerate(
            len(model.tokenizer.encode(t, add_special_tokens=False)) for t in texts
        )
        if n > TOKEN_LIMIT
    ]
    if over:
        sys.exit(f"{len(over)} chunks would TRUNCATE (limit {TOKEN_LIMIT}): {over[:5]}")
    print(f"truncation check passed: 0 of {len(chunks):,} chunks exceed {TOKEN_LIMIT} tokens")

    # 3. Embed. normalize_embeddings=True is what makes search a dot product.
    print("embedding ...")
    vectors = model.encode(
        texts,
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).astype(np.float32)          # float32 is what the model emits; float64
                                  # would double the file to buy nothing

    # 4. Confirm the normalisation actually happened. If this drifts, every
    #    similarity score downstream is subtly wrong in a way that still looks
    #    like a plausible ranking.
    norms = np.linalg.norm(vectors, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-4):
        sys.exit(f"vectors not unit length: min={norms.min():.5f} max={norms.max():.5f}")
    print(f"norms verified: all within 1e-4 of 1.0")

    ids = np.array([c["id"] for c in chunks])

    # 5. Store ids ALONGSIDE the matrix. search.py then joins chunks to vectors
    #    by ID rather than by row position - two files silently drifting out of
    #    row order is exactly the class of bug this whole design keeps refusing
    #    to reintroduce.
    INDEX_DIR.mkdir(exist_ok=True)
    np.savez(INDEX_DIR / "vectors.npz", ids=ids, vectors=vectors)

    per_doc: dict[str, int] = defaultdict(int)
    for c in chunks:
        per_doc[c["doc_id"]] += 1
    dupes = duplicate_groups(chunks)

    manifest = {
        "corpus_sha256": actual,
        "vectors_sha256": hashlib.sha256(vectors.tobytes()).hexdigest(),
        "git_sha": git_sha(),
        "model": MODEL_NAME,
        "embedding_dim": int(vectors.shape[1]),
        "normalized": True,
        "query_prefix": QUERY_PREFIX,
        "passage_prefix": PASSAGE_PREFIX,
        "token_limit": TOKEN_LIMIT,
        "n_chunks": len(chunks),
        "chunks_per_doc": dict(sorted(per_doc.items())),
        "duplicate_groups": dupes,
        "versions": _versions(),
    }
    (INDEX_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"\nwrote {INDEX_DIR / 'vectors.npz'}  "
          f"({vectors.shape[0]:,} x {vectors.shape[1]}, {vectors.nbytes / 1e6:.1f} MB)")
    print(f"wrote {INDEX_DIR / 'manifest.json'}")

    top = sorted(per_doc.items(), key=lambda kv: -kv[1])[:3]
    print(f"top 3 docs: " + ", ".join(f"{k}({v})" for k, v in top) +
          f"  = {100 * sum(v for _, v in top) / len(chunks):.0f}% of chunks")
    print(f"duplicate chunk groups: {len(dupes)}"
          + (f"  e.g. {dupes[0]}" if dupes else ""))


def _versions() -> dict[str, str]:
    """Pin the libraries that can change embedding values under us."""
    import importlib.metadata as md
    out = {}
    for pkg in ("sentence-transformers", "torch", "transformers", "numpy"):
        try:
            out[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            out[pkg] = "unknown"
    return out


if __name__ == "__main__":
    main()
