"""Aggregate a results file into results/baseline.md.

Run:  .venv/bin/python src/report.py
      .venv/bin/python src/report.py --results results/hybrid.json \
                                     --out results/hybrid.md

WHY THE PER-QUESTION TABLE IS THE POINT, NOT THE MEANS
------------------------------------------------------
Four means is what a baseline usually is, and on this gold set four means are
close to unreadable. Gold-set size ranges from 1 to 5 chunks, so the recall@3
ceiling ranges from 1.00 down to 0.20 before the retriever does anything at
all. A question scoring 0.20 may have been answered outright at rank 4, and a
question scoring 1.00 may have made the user scroll to rank 6 first. Both
happen here; they are Q04 and Q25.

So every row carries |gold| and first-relevant-rank next to the score, and D5b
says to read those first wherever |gold| > 1. The means are for comparing
variants against each other on Day 9, which is the one job they can do
honestly, since both variants face the same denominators.

WHY UNANSWERABLE QUESTIONS ARE IN THE TABLE BUT NOT IN THE MEANS
----------------------------------------------------------------
D8. Recall on a question with no gold chunk is 0/0, and folding those 6 in as
zeros would pull every mean down by a fifth on questions that cannot be
failed. They appear as rows reading `undefined`, because what they retrieved
is still worth looking at: they are the abstention cases, and a generator
handed three confident wrong chunks is the failure Day 12 has to describe.

WHY THE SDK PAGE SET IS PARSED FROM THE INDEX
---------------------------------------------
D7: no gold chunk in the set comes from the seven `agent-sdk/*` pages, so any
SDK chunk in a top 10 is a product-surface confusion by construction, counted
for free. That property is worth exactly as much as the doc-ID set is correct.
A first pass at this file assumed the SDK pages were doc-20 to doc-27, which
counted `output-styles` as a confusion and missed three real SDK pages. The
set is read from corpus/INDEX.md now, where it cannot drift from the corpus.
"""

import argparse
import json
import re
from datetime import date as date_cls
from pathlib import Path

import metrics

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS = ROOT / "results" / "retrieval-baseline.json"
DEFAULT_OUT = ROOT / "results" / "baseline.md"
INDEX_MD = ROOT / "corpus" / "INDEX.md"

# Rows look like:  | doc-24 | `agent-sdk/overview` | https://... | 9,069 | date |
INDEX_ROW = re.compile(r"^\|\s*(doc-\d+)\s*\|\s*`([^`]+)`", re.M)


def parse_sdk_docs(index_text: str) -> set[str]:
    """Doc IDs whose page name is under `agent-sdk/`.

    Matches on the path prefix rather than on the substring "sdk", so a CLI
    page that merely mentions the SDK in its name is not swept in.
    """
    return {
        doc_id
        for doc_id, page in INDEX_ROW.findall(index_text)
        if page.startswith("agent-sdk/")
    }


def score(question: dict, sdk_docs: set[str]) -> dict:
    """One row of the per-question table.

    Carries the inputs to the metric, not only its output: |gold| because
    recall is unreadable without it, and first-relevant-rank because it is the
    only column that distinguishes "found at rank 12" from "not found".
    """
    ranked = [r["chunk_id"] for r in question["retrieved"]]
    gold = question["gold_chunks"]
    return {
        "id": question["id"],
        "question": question["question"],
        "answerable": question["answerable"],
        "n_gold": len(set(gold)),
        "recall_at_3": metrics.recall_at_k(ranked, gold, 3),
        "recall_at_10": metrics.recall_at_k(ranked, gold, 10),
        "precision_at_3": metrics.precision_at_k(ranked, gold, 3),
        "reciprocal_rank": metrics.reciprocal_rank(ranked, gold),
        "first_relevant_rank": metrics.first_relevant_rank(ranked, gold),
        "sdk_hits": sum(1 for c in ranked[:10] if c.split(":")[0] in sdk_docs),
    }


def aggregate(rows: list[dict]) -> dict:
    """Means over the answerable questions only, plus the counts worth stating.

    A mean is not the honest summary of this run and the counts are, which is
    why they are computed here rather than left to be eyeballed off the table.
    "12 of 24 questions return no gold chunk in the top 10" says what happened;
    "mean recall@10 is 0.36" invites the reader to imagine every question
    scoring about a third.
    """
    answerable = [r for r in rows if r["answerable"]]
    if not answerable:
        raise ValueError("no answerable questions; every mean would be undefined")

    def mean(key):
        return sum(r[key] for r in answerable) / len(answerable)

    return {
        "n_questions": len(rows),
        "n_answerable": len(answerable),
        "n_unanswerable": len(rows) - len(answerable),
        "mean_recall_at_3": mean("recall_at_3"),
        "mean_recall_at_10": mean("recall_at_10"),
        "mean_precision_at_3": mean("precision_at_3"),
        "mrr": mean("reciprocal_rank"),
        "n_no_gold_in_top_10": sum(1 for r in answerable if r["recall_at_10"] == 0),
        "n_no_gold_at_all": sum(1 for r in answerable
                                if r["first_relevant_rank"] is None),
        "n_gold_at_rank_1": sum(1 for r in answerable
                                if r["first_relevant_rank"] == 1),
        "sdk_hits": sum(r["sdk_hits"] for r in answerable),
        "sdk_slots": 10 * len(answerable),
    }


def _cell(value, places: int = 2) -> str:
    if value is None:
        return "undefined"
    return f"{value:.{places}f}"


def render(rows: list[dict], agg: dict, meta: dict, date: str) -> str:
    """The markdown that lands in results/baseline.md."""
    out = [
        f"# Baseline, {meta['variant']}",
        "",
        f"Run {date}. Corpus `{meta['corpus_sha256'][:16]}` · "
        f"index `{meta['vectors_sha256'][:16]}` · model `{meta['model']}` · "
        f"top {meta['top']} stored.",
        "",
        "Means are over the "
        f"{agg['n_answerable']} answerable questions only. The "
        f"{agg['n_unanswerable']} unanswerable ones have no gold chunk, so "
        "recall and precision on them are 0/0, not 0. See D8.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| mean recall@3 | {agg['mean_recall_at_3']:.3f} |",
        f"| mean recall@10 | {agg['mean_recall_at_10']:.3f} |",
        f"| mean precision@3 | {agg['mean_precision_at_3']:.3f} |",
        f"| MRR | {agg['mrr']:.3f} |",
        "",
        "The counts say more than the means:",
        "",
        f"- **{agg['n_no_gold_in_top_10']} of {agg['n_answerable']} answerable "
        "questions return no gold chunk in the top 10.**",
        f"- {agg['n_no_gold_at_all']} return none in the top {meta['top']} either.",
        f"- {agg['n_gold_at_rank_1']} put a gold chunk at rank 1.",
        f"- SDK chunks take {agg['sdk_hits']} of {agg['sdk_slots']} answerable "
        f"top-10 slots ({100 * agg['sdk_hits'] / agg['sdk_slots']:.1f}%). No gold "
        "chunk comes from those 7 pages, so every one of them is a "
        "product-surface confusion by construction (D7).",
        "",
        "## Per question",
        "",
        "`|gold|` is the size of the gold set and the ceiling on recall@3 when "
        "one chunk is retrieved. `first` is the rank of the first gold chunk. "
        "Read those two before the scores wherever `|gold| > 1` (D5b).",
        "",
        "| Q | \\|gold\\| | recall@3 | recall@10 | precision@3 | RR | first | SDK@10 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        first = r["first_relevant_rank"]
        out.append(
            f"| {r['id']} | {r['n_gold'] or ''} | {_cell(r['recall_at_3'])} | "
            f"{_cell(r['recall_at_10'])} | {_cell(r['precision_at_3'])} | "
            f"{_cell(r['reciprocal_rank'], 3)} | "
            f"{first if first else ''} | {r['sdk_hits']} |"
        )
    out += [
        "",
        "Rows reading `undefined` are the unanswerable questions. They are "
        "excluded from every mean above and their retrieved chunks are the "
        "material for the abstention question, not for recall.",
        "",
    ]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    data = json.loads(args.results.read_text())
    sdk_docs = parse_sdk_docs(INDEX_MD.read_text())
    rows = [score(q, sdk_docs) for q in data["questions"]]
    agg = aggregate(rows)
    text = render(rows, agg, data, date_cls.today().isoformat())
    args.out.write_text(text)

    print(f"wrote {args.out}: {agg['n_answerable']} answerable, "
          f"{agg['n_unanswerable']} unanswerable, "
          f"mean recall@10 {agg['mean_recall_at_10']:.3f}")


if __name__ == "__main__":
    main()
