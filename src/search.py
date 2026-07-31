"""Search the index.

Run:  .venv/bin/python src/search.py "how do I stop Claude asking before every edit?"
      .venv/bin/python src/search.py "..." --top 20 --show-text
      .venv/bin/python src/search.py "..." --docs

HOW THE SEARCH WORKS
--------------------
Three lines of actual work:

    1. turn the question into 384 numbers, scaled to length 1
    2. multiply it against all 1,662 chunk vectors -> one score per chunk
    3. take the highest scores

Step 2 is a dot product, and it equals cosine similarity ONLY because embed.py
normalised everything to unit length. That is the whole reason normalisation
happened there rather than being skipped as a detail.

This is deliberately the crudest retriever that works. No reranking, no query
expansion, no keyword matching (that arrives on Days 9-10). A weak retriever
produces the failures that Days 6-11 exist to measure - a good one would teach
you nothing about measurement.

--show-text EXISTS FOR DAY 4
----------------------------
Five of the thirty gold questions have to be UNANSWERABLE, and "I searched and
couldn't find it" is not evidence of absence. Reading the top 20 chunks lets you
confirm a judgement you formed another way, rather than mistaking your own
failure to search for the corpus's failure to cover something.
"""

import argparse
import json
import sys

import numpy as np

from chunk import INDEX_DIR, MODEL_NAME


def load_index() -> tuple[np.ndarray, np.ndarray, dict[str, dict], dict]:
    """Load vectors, ids, chunk records and the manifest, checking they agree."""
    if not (INDEX_DIR / "vectors.npz").exists():
        sys.exit("index/vectors.npz not found - run src/embed.py first")

    # allow_pickle=False: we only ever store plain arrays, and refusing pickle
    # means a tampered index file cannot execute code on load.
    data = np.load(INDEX_DIR / "vectors.npz", allow_pickle=False)
    ids, vectors = data["ids"], data["vectors"]

    manifest = json.loads((INDEX_DIR / "manifest.json").read_text(encoding="utf-8"))

    with (INDEX_DIR / "chunks.jsonl").open(encoding="utf-8") as fh:
        chunks = {r["id"]: r for r in map(json.loads, fh)}

    # The three files have to describe the same index. Any mismatch means a
    # partial rebuild, and searching a half-updated index produces results that
    # look completely normal.
    if len(ids) != len(vectors):
        sys.exit(f"index corrupt: {len(ids)} ids vs {len(vectors)} vectors")
    if manifest["model"] != MODEL_NAME:
        sys.exit(f"model mismatch: index built with {manifest['model']}, "
                 f"this code uses {MODEL_NAME} - re-run src/embed.py")
    missing = [i for i in ids[:50] if i not in chunks]
    if missing:
        sys.exit(f"ids in vectors.npz missing from chunks.jsonl: {missing[:5]}")

    return ids, vectors, chunks, manifest


def search(query: str, ids, vectors, manifest, top: int) -> list[tuple[str, float]]:
    """Return (chunk_id, score) for the best `top` chunks."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    q = model.encode(
        [manifest["query_prefix"] + query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype(np.float32)[0]

    # Both sides are unit length, so this dot product IS cosine similarity.
    scores = vectors @ q

    # Ties are real: 4 groups of chunks in this corpus have identical text, so
    # they get identical scores. argsort's default is not stable, which would
    # let their order vary between runs and make metrics irreproducible.
    # kind="stable" preserves the existing order, and ids are already in
    # document order - so ties break by chunk ID, deterministically.
    order = np.argsort(-scores, kind="stable")[:top]
    return [(str(ids[i]), float(scores[i])) for i in order]


def to_docs(hits: list[tuple[str, float]], top: int) -> list[tuple[str, float]]:
    """Collapse chunk hits to distinct documents, keeping rank order.

    The gold set records labels at both granularities. Doc-level metrics are the
    safety net: they survive any future re-chunking, because they never referred
    to chunk boundaries in the first place. "Top 3 docs" means the first three
    DISTINCT documents in the ranked list - defined here so that Day 6's hand
    arithmetic and Day 7's code cannot quietly disagree about it.
    """
    seen: dict[str, float] = {}
    for chunk_id, score in hits:
        doc = chunk_id.split(":")[0]
        if doc not in seen:
            seen[doc] = score
    return list(seen.items())[:top]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the chunk index.")
    parser.add_argument("query", help="the question, phrased as a user would")
    parser.add_argument("--top", type=int, default=10, help="how many to return")
    parser.add_argument("--show-text", action="store_true",
                        help="print each chunk's text (for Day 4 and Day 8)")
    parser.add_argument("--docs", action="store_true",
                        help="collapse to distinct documents")
    args = parser.parse_args()

    ids, vectors, chunks, manifest = load_index()
    hits = search(args.query, ids, vectors, manifest, args.top)

    print(f'query: "{args.query}"')
    print(f"index: {manifest['n_chunks']:,} chunks · {manifest['model']}\n")

    if args.docs:
        for rank, (doc, score) in enumerate(to_docs(hits, args.top), start=1):
            slug = next(c["slug"] for c in chunks.values() if c["doc_id"] == doc)
            print(f"{rank:>3}. {score:.4f}  {doc}  {slug}")
        return

    for rank, (chunk_id, score) in enumerate(hits, start=1):
        c = chunks[chunk_id]
        print(f"{rank:>3}. {score:.4f}  {chunk_id:16} {c['slug']:28} "
              f"{c['block_type']:11} {c['tokens_embed']:>4}tok")
        if args.show_text:
            body = c["text_embed"].strip()
            body = body if len(body) <= 600 else body[:600] + " ..."
            print("     " + body.replace("\n", "\n     ") + "\n")


if __name__ == "__main__":
    main()
