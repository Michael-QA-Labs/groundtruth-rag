"""Build the 24 judge pools the LLM judge and the human both label.

Run:  .venv/bin/python src/build_judge_pools.py

See docs/day-13-judge-design.md for why the judge grades pools rather than
pairs. In short: D5 necessity is a property of a chunk *relative to the
alternatives*, so a chunk judged alone cannot be judged at all.
"""

import json
import random
from pathlib import Path

SEED = 20260813
MIN_NEGATIVES = 2


def build_pools(gold, retrieval, seed, min_negatives=2):
    """Return one pool per answerable question.

    Each pool carries the question, its gold answer, and the candidate chunks
    the rater chooses a minimal sufficient subset from.
    """
    # 1. Refuse if the labels and the retrieval run were taken against
    #    different corpus snapshots. They would still join cleanly on chunk id,
    #    because ids are stable across rebuilds, and some of the resulting
    #    pairs would point at text that has since moved. Same refusal
    #    src/run_retrieval.py makes, for the same reason.
    gold_corpus = gold.get("corpus_sha256")
    retrieval_corpus = retrieval.get("corpus_sha256")
    if gold_corpus and retrieval_corpus and gold_corpus != retrieval_corpus:
        raise ValueError(
            f"corpus mismatch: gold set is {gold_corpus[:12]}, "
            f"retrieval run is {retrieval_corpus[:12]}. Rebuild one of them."
        )

    # 2. Unanswerable questions are excluded. The task asks for the minimal
    #    subset that supports the gold answer, and these have no gold answer,
    #    so there is nothing for a subset to be sufficient for.
    answerable = [q for q in gold["questions"] if q["answerable"]]

    # 3. Index the retrieval run by question id so each question can be given
    #    negatives drawn from its *own* ranked list. Negatives borrowed from
    #    another question would still produce 100 pairs, and would replace the
    #    hard near-misses this design depends on with chunks nobody could
    #    mistake for gold.
    #    Rank and score are dropped deliberately. Which negatives get drawn
    #    must not depend on how confident the retriever was, or the pool would
    #    be built from the same signal it is meant to audit.
    ranked_by_id = {q["id"]: [r["chunk_id"] for r in q["retrieved"]]
                    for q in retrieval["questions"]}

    pools = []
    for question in answerable:
        # 4. Every gold chunk goes in. This is what makes the pool sufficient
        #    by construction: a minimal subset exists to be found, so a wrong
        #    answer means the rater misjudged rather than that the task was
        #    impossible.
        gold_chunks = list(question["gold_chunks"])

        # 5. One negative per gold chunk, with a floor of two.
        #
        #    The rater is asked for the *minimal sufficient* subset, so the
        #    ratio inside a pool changes what a good answer looks like. A pool
        #    that is mostly gold rewards answering "nearly all of them"; a pool
        #    with one gold punishes exactly that. Matching negatives to gold
        #    keeps every pool at worst an even split, so no single question
        #    drives kappa with a shape none of the others share.
        #
        #    The floor matters at the bottom: a 1-gold question drawn against
        #    one distractor is barely a choice.
        #
        #    Seeding per question rather than once for the whole run means
        #    adding or dropping a question does not reshuffle every other
        #    question's draw, so a pool stays stable across rebuilds.
        pool_rng = random.Random(f"{seed}:{question['id']}")
        eligible = [c for c in ranked_by_id[question["id"]]
                    if c not in set(gold_chunks)]
        negatives = pool_rng.sample(eligible,
                                    max(min_negatives, len(gold_chunks)))

        # 6. Shuffle, or position becomes the label. Gold is assembled first,
        #    so an unshuffled pool lists it at the front of every question, and
        #    both raters can score well by reading order rather than by
        #    applying D5. That would not look like a bug in the output: the
        #    pools are the right size, the right chunks are present, and the
        #    agreement number comes out high.
        candidates = gold_chunks + negatives
        pool_rng.shuffle(candidates)

        # 7. Note what is absent: nothing here records which candidates are
        #    gold. This file is what the human labels against, and a field
        #    naming the gold chunks would turn labelling into transcription.
        #    The answer key is built separately, by build_key below.
        pools.append({
            "id": question["id"],
            "question": question["question"],
            "gold_answer": question["gold_answer"],
            "candidates": candidates,
        })

    return pools


def attach_text(pools, chunks):
    """Return the pools with each candidate id replaced by {id, text}.

    Uses `text_raw`, the verbatim slice of the corpus file, never `text_embed`.
    `text_embed` is the transformed rendering built for the embedding model;
    judging against it would mean judging text that does not appear in the
    corpus. Day 2 separated the two fields precisely so a rendering change
    could never reach a label.
    """
    raw_by_id = {c["id"]: c["text_raw"] for c in chunks}

    attached = []
    for pool in pools:
        # A missing id means the pools and the index disagree, which can only
        # happen if one was rebuilt without the other. Skipping it quietly
        # would emit a short pool that still looks well-formed.
        candidates = [{"id": chunk_id, "text": raw_by_id[chunk_id]}
                      for chunk_id in pool["candidates"]]
        attached.append(dict(pool, candidates=candidates))

    return attached


def build_key(pools, gold):
    """Return one row per (question, chunk) pair, marking D5 gold status.

    Kept apart from the pools so the file you label against can be read
    without seeing the answers.
    """
    gold_by_id = {q["id"]: set(q["gold_chunks"]) for q in gold["questions"]}

    return [
        {
            "question_id": pool["id"],
            "chunk_id": chunk_id,
            "gold": chunk_id in gold_by_id[pool["id"]],
        }
        for pool in pools
        for chunk_id in pool["candidates"]
    ]


def main():
    root = Path(__file__).resolve().parent.parent

    gold = json.loads((root / "gold" / "gold-set.json").read_text())
    retrieval = json.loads(
        (root / "results" / "retrieval-baseline.json").read_text())
    chunks = [json.loads(line) for line
              in (root / "index" / "chunks.jsonl").read_text().splitlines()
              if line.strip()]

    pools = build_pools(gold, retrieval, seed=SEED,
                        min_negatives=MIN_NEGATIVES)
    key = build_key(pools, gold)
    with_text = attach_text(pools, chunks)

    out_dir = root / "judge"
    out_dir.mkdir(exist_ok=True)

    # Provenance travels with the pools, the way it does on every other
    # artefact in results/. A pool set whose seed is not recorded cannot be
    # rebuilt, and the hand labels are made against exactly this draw.
    (out_dir / "pools.json").write_text(json.dumps({
        "corpus_sha256": gold.get("corpus_sha256"),
        "seed": SEED,
        "min_negatives": MIN_NEGATIVES,
        "rule": "negatives per question = max(min_negatives, gold count)",
        "note": "Candidates are shuffled. Nothing here marks gold status; "
                "see pools-key.json.",
        "pools": with_text,
    }, indent=2) + "\n")

    (out_dir / "pools-key.json").write_text(json.dumps({
        "corpus_sha256": gold.get("corpus_sha256"),
        "seed": SEED,
        "note": "D5 gold status per pair. Do not open before hand-labelling.",
        "key": key,
    }, indent=2) + "\n")

    golds = sum(1 for row in key if row["gold"])
    print(f"pools:      {len(pools)}")
    print(f"pairs:      {len(key)}  ({golds} gold, {len(key) - golds} negative)")
    print(f"pool sizes: "
          f"min {min(len(p['candidates']) for p in pools)}, "
          f"max {max(len(p['candidates']) for p in pools)}")
    print(f"written:    judge/pools.json, judge/pools-key.json")


if __name__ == "__main__":
    main()
