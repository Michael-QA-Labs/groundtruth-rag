"""Run the keyword and hybrid variants over the same 30 gold questions.

Run:  .venv/bin/python src/run_hybrid.py

Writes two files, from one model load:

    results/bm25.json     BM25 alone
    results/hybrid.json   dense and BM25 fused with RRF, k=60

WHY BM25 ALONE IS SAVED TOO, WHEN DAY 9 ONLY ASKS FOR THE HYBRID
----------------------------------------------------------------
Without it, a hybrid that beats the dense baseline cannot be explained. "The
keyword side found things the dense side missed" and "the keyword side is
simply better on this corpus" predict the same hybrid number and imply
completely different next steps. It costs nothing: the BM25 ranking has to be
computed to fuse it, so saving it is one extra file write.

WHAT THIS ASSERTS BEFORE IT WRITES ANYTHING
-------------------------------------------
1. The gold set and the index agree on the corpus hash, same guard as
   run_retrieval.py. A run against a corpus the labels were not written for
   produces numbers that all compute and all mean nothing.
2. The dense half of the fusion reproduces `results/retrieval-baseline.json`
   rank for rank, top 20, on all 30 questions. This is the check that matters
   for Day 11: if the dense side drifted, every difference between baseline
   and hybrid would be partly a difference between two dense retrievers, and
   the confidence interval would be attributing it to the keyword side.

Both are hard failures rather than warnings. A warning printed at the top of a
minute-long run is a warning nobody reads.

WHY THE LISTS FUSED ARE FULL DEPTH
----------------------------------
All 1,637 chunks from each side, not the top 20. Fusing truncated lists makes
"absent from this list" ambiguous between "ranked 21st" and "ranked last",
and those are different pieces of evidence. It costs nothing here: the dense
scores are one matrix multiply and BM25 scores every chunk anyway.
"""

import argparse
import json
from pathlib import Path

import numpy as np

import fuse
import search
from build_gold import OUT as GOLD_JSON
from keyword_search import BM25Index
from run_retrieval import display_path, encode_queries, rank

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "results" / "retrieval-baseline.json"
DEFAULT_TOP = 20


def stored_rankings(path: Path) -> dict[str, list[str]]:
    """The top-20 chunk IDs per question from an existing results file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {q["id"]: [r["chunk_id"] for r in q["retrieved"]]
            for q in data["questions"]}


def check_dense_matches_baseline(qid: str, dense_top: list[str],
                                 baseline: dict[str, list[str]]) -> None:
    """Fail loudly if this run's dense half disagrees with the baseline.

    The likely causes are all silent: a different query prefix, a re-embedded
    index, a model version bump, a tie broken the other way. Every one of them
    still produces a plausible ranking.
    """
    expected = baseline.get(qid)
    if expected is None:
        return
    if dense_top[:len(expected)] != expected:
        first = next(i for i, (a, b) in enumerate(zip(dense_top, expected)) if a != b)
        raise SystemExit(
            f"{qid}: dense ranking differs from results/retrieval-baseline.json "
            f"at rank {first + 1}: this run has {dense_top[first]}, the baseline "
            f"has {expected[first]}. The hybrid cannot be compared against a "
            f"baseline it does not reproduce.")


def as_payload(results: list[dict], manifest: dict, top: int,
               variant: str, note: str) -> dict:
    return {
        "corpus_sha256": manifest["corpus_sha256"],
        "vectors_sha256": manifest["vectors_sha256"],
        "model": manifest["model"],
        "top": top,
        "variant": variant,
        "note": note,
        "questions": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the BM25 and hybrid variants.")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP)
    parser.add_argument("--k", type=int, default=fuse.K,
                        help=f"RRF constant (default: {fuse.K})")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    gold = json.loads(GOLD_JSON.read_text(encoding="utf-8"))
    ids, vectors, chunks, manifest = search.load_index()

    if gold["corpus_sha256"] != manifest["corpus_sha256"]:
        raise SystemExit(
            f"corpus mismatch: gold set was labeled against "
            f"{gold['corpus_sha256'][:12]}, index is {manifest['corpus_sha256'][:12]}")

    baseline = stored_rankings(BASELINE) if BASELINE.exists() else {}
    bm25 = BM25Index([chunks[str(i)] for i in ids])

    questions = [q["question"] for q in gold["questions"]]
    query_vectors = encode_queries(questions, manifest)

    bm25_results, hybrid_results = [], []
    for entry, qv in zip(gold["questions"], query_vectors):
        dense_full = [str(ids[i]) for i in rank(vectors @ qv, len(ids))]
        check_dense_matches_baseline(entry["id"], dense_full, baseline)

        keyword_full = bm25.search(entry["question"], top=None)
        fused = fuse.fuse([dense_full, keyword_full], k=args.k, top=args.top)
        scores = bm25.score(entry["question"])

        common = {"id": entry["id"], "question": entry["question"],
                  "answerable": entry["answerable"],
                  "gold_chunks": entry["gold_chunks"]}
        bm25_results.append({**common, "retrieved": [
            {"rank": r + 1, "chunk_id": cid, "score": round(scores[cid], 6)}
            for r, cid in enumerate(keyword_full[:args.top])]})
        hybrid_results.append({**common, "retrieved": [
            {"rank": r + 1, "chunk_id": cid} for r, cid in enumerate(fused)]})

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, results, variant, note in [
        ("bm25.json", bm25_results, "bm25",
         "BM25 Okapi, k1=1.2, b=0.75, over text_embed. Ranked chunk IDs only."),
        ("hybrid.json", hybrid_results, f"hybrid-rrf{args.k}",
         f"Dense and BM25 fused with reciprocal rank fusion, k={args.k}, over "
         "full-depth lists. No score is stored: RRF scores are not comparable "
         "across questions and nothing downstream reads them."),
    ]:
        path = args.out_dir / name
        payload = as_payload(results, manifest, args.top, variant, note)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {display_path(path)}: {len(results)} questions, top {args.top}")


if __name__ == "__main__":
    main()
