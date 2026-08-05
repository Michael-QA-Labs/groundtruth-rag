"""Run the retriever over every gold question and save the ranked results.

Run:  .venv/bin/python src/run_retrieval.py
      .venv/bin/python src/run_retrieval.py --top 20 --out results/baseline.json

WHY THIS EXISTS RATHER THAN A SHELL LOOP OVER search.py
-------------------------------------------------------
`search.search()` constructs a SentenceTransformer on every call, so thirty
questions would load the model thirty times. This loads it once and encodes all
thirty queries in a single batch, which is also the only way to be certain every
question was scored by identical model state.

The cost is that the scoring and tie-breaking lines are duplicated from
search.py, so the two could drift apart and produce different rankings from the
same index. tests/test_run_retrieval.py pins the tie-break convention, and the
run itself is cross-checked against `search.search()` on real questions before
the output is trusted.

WHY IT STORES 20 AND METRICS READ 10
------------------------------------
Every metric named for Days 6-8 is at k <= 10. The extra ten ranks cost nothing
and exist for Day 8, which asks for a written diagnosis of the five worst
questions. "The gold chunk was at rank 12" and "the gold chunk was nowhere" are
different failures with different fixes, and truncating at 10 makes them look
identical.

WHY UNANSWERABLE QUESTIONS ARE RUN TOO
--------------------------------------
Recall is undefined for them, but Day 8 scores abstention and needs to see what
came back. A question with no correct answer still returns ten confident-looking
chunks, and that is the thing being measured.

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
No metrics. Day 6 computes recall and precision BY HAND from this file, and Day 7
writes the code and checks it against the hand numbers. A metric computed here
would remove the only independent check those two days have.
"""

import argparse
import json
from pathlib import Path

import numpy as np

import search
from build_gold import OUT as GOLD_JSON

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "results" / "retrieval-baseline.json"
DEFAULT_TOP = 20


def rank(scores: np.ndarray, top: int) -> np.ndarray:
    """Indices of the highest `top` scores, ties broken deterministically.

    Identical to search.py's ordering and for the same reason: four groups of
    chunks in this corpus have byte-identical text and therefore identical
    scores. numpy's default sort is not stable, so their order would vary
    between runs and every metric computed from them would be irreproducible.
    Stable sort preserves index order, and ids are stored in document order, so
    ties break by chunk ID.
    """
    return np.argsort(-scores, kind="stable")[:top]


def encode_queries(questions: list[str], manifest: dict) -> np.ndarray:
    """One model load, one batch, unit-length vectors.

    The query prefix comes from the manifest rather than being hardcoded,
    because a prefix mismatch between index time and query time degrades results
    in a way that looks like a bad retriever rather than a bug.
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(search.MODEL_NAME)
    return model.encode(
        [manifest["query_prefix"] + q for q in questions],
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retrieve for every gold question and save ranked results.")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP,
                        help=f"ranks to store per question (default: {DEFAULT_TOP})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    gold = json.loads(GOLD_JSON.read_text(encoding="utf-8"))
    ids, vectors, _, manifest = search.load_index()

    # A run against a different corpus than the labels were written for is
    # meaningless, and the failure is silent: every number still computes. D1
    # froze the corpus precisely so this check is possible.
    if gold["corpus_sha256"] != manifest["corpus_sha256"]:
        raise SystemExit(
            f"corpus mismatch: gold set was labeled against "
            f"{gold['corpus_sha256'][:12]}, index is {manifest['corpus_sha256'][:12]}")

    questions = [q["question"] for q in gold["questions"]]
    query_vectors = encode_queries(questions, manifest)

    results = []
    for entry, q in zip(gold["questions"], query_vectors):
        # Unit-length on both sides, so this dot product is cosine similarity.
        scores = vectors @ q
        order = rank(scores, args.top)
        results.append({
            "id": entry["id"],
            "question": entry["question"],
            "answerable": entry["answerable"],
            "gold_chunks": entry["gold_chunks"],
            "retrieved": [{"rank": r + 1,
                           "chunk_id": str(ids[i]),
                           "score": round(float(scores[i]), 6)}
                          for r, i in enumerate(order)],
        })

    payload = {
        "corpus_sha256": manifest["corpus_sha256"],
        "vectors_sha256": manifest["vectors_sha256"],
        "model": manifest["model"],
        "top": args.top,
        "variant": "dense-baseline",
        "note": "Ranked chunk IDs only. Metrics are computed by hand on Day 6 "
                "and in code on Day 7; nothing here is scored.",
        "questions": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {args.out.relative_to(ROOT)}: {len(results)} questions, "
          f"top {args.top}, model {manifest['model']}")


if __name__ == "__main__":
    main()
