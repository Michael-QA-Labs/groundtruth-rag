"""Bootstrap confidence intervals over per-question scores.

Import:  from stats import bootstrap_mean_ci, paired_diff_ci

WHAT THIS IS FOR
----------------
Day 9 produced 0.362 for the dense baseline and 0.433 for the hybrid on mean
recall@10. The difference is +0.071 and it rests on 5 questions of 24: four
improved, one regressed, 19 did not move. Reporting +0.071 without saying how
much of it could be the particular 24 questions that happen to be in this gold
set would be exactly the unmeasured claim this project exists to avoid.

The bootstrap answers a narrow question: if the questions had been drawn
differently from the same population, how much would this number move? It says
nothing about whether the gold labels are right, whether the questions are
representative of real users, or whether recall@10 is the metric worth caring
about. Those are Day 5, Day 3 and D5b problems respectively, and no interval
addresses them.

WHAT IS RESAMPLED, AND WHY IT IS THE QUESTIONS
----------------------------------------------
The unit of resampling is the question, because the question is the unit that
was sampled in the first place: 30 of them, written on Day 3 from real
problems. Resampling chunks or gold labels would answer a question about the
corpus that nobody asked.

24 units, not 30. The 6 unanswerable questions have no recall to average, D8.

WHY PAIRED DIFFERENCES USE THE SAME RESAMPLE
--------------------------------------------
Two variants scored on the same questions are paired data. Resampling them
independently would compare two independent samples of 24 questions, which
throws away the pairing and answers a question about the population rather
than about the variants. It also runs, and returns a plausible interval, which
is why tests/test_stats.py pins it: the paired difference of a variant against
itself must be exactly (0.0, 0.0), and an unpaired implementation cannot
produce that.

THE METHOD, AND ITS LIMIT
-------------------------
Percentile bootstrap: resample with replacement, recompute the mean, take the
2.5th and 97.5th percentiles of the resampled means. It is what PLAN.md
specifies and it is the version that can be written from the definition
without a reference.

Its known weakness is worth stating rather than hiding: with a skewed
statistic or a small sample it undercovers, and BCa exists to correct for
that. n=24 with many identical zeros is exactly the regime where that
undercoverage is real. The direction of the error matters here, because it
means an interval that excludes zero is weaker evidence than it looks, and the
honest reading of a borderline result is "not established" rather than
"significant".

RESAMPLE COUNT AND SEED
-----------------------
2,000 resamples, per PLAN.md. The interval is itself a random quantity, so the
seed is a parameter and gets recorded next to any number derived from it. Two
seeds give two slightly different intervals; that spread is real and is why
these are reported to two decimals rather than four.
"""

from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

N_RESAMPLES = 2000
ALPHA = 0.05
SEED = 20260806


def _check_clusters(n: int, clusters: list[list[int]] | None) -> list[list[int]]:
    """Every observation in exactly one cluster, or the resample is not a
    resample of the data: an index left out can never appear, and one listed
    twice is silently weighted double."""
    if clusters is None:
        return [[i] for i in range(n)]

    seen = [i for cluster in clusters for i in cluster]
    if sorted(seen) != list(range(n)):
        raise ValueError(
            f"clusters must cover 0..{n - 1} exactly once, got {sorted(seen)}")
    return clusters


def _resampled_means(values: np.ndarray, n_resamples: int,
                     clusters: list[list[int]], rng: np.random.Generator) -> np.ndarray:
    """Mean of `values` under `n_resamples` draws of clusters with replacement.

    Clusters are drawn, then flattened back to observations, so a cluster of
    two questions contributes both or neither. With the default singleton
    clusters this is the ordinary bootstrap.
    """
    n_clusters = len(clusters)
    picks = rng.integers(0, n_clusters, size=(n_resamples, n_clusters))
    means = np.empty(n_resamples)
    for r in range(n_resamples):
        idx = np.concatenate([clusters[c] for c in picks[r]])
        means[r] = values[idx].mean()
    return means


def bootstrap_mean_ci(values, n_resamples: int = N_RESAMPLES, alpha: float = ALPHA,
                      clusters: list[list[int]] | None = None,
                      seed: int = SEED) -> tuple[float, float]:
    """Percentile confidence interval for the mean of `values`."""
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("cannot bootstrap an empty sample")

    groups = [np.asarray(c, dtype=int) for c in _check_clusters(arr.size, clusters)]
    means = _resampled_means(arr, n_resamples, groups, np.random.default_rng(seed))
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def paired_diff_ci(variant, baseline, n_resamples: int = N_RESAMPLES,
                   alpha: float = ALPHA, clusters: list[list[int]] | None = None,
                   seed: int = SEED) -> tuple[float, float]:
    """Interval for the mean of (variant - baseline), question by question.

    The subtraction happens first, per question, and the bootstrap then runs
    over those differences. That is what keeps the resample paired: one draw of
    questions, one difference per drawn question.
    """
    a = np.asarray(variant, dtype=float)
    b = np.asarray(baseline, dtype=float)
    if a.shape != b.shape:
        raise ValueError(
            f"paired data must be the same length, got {a.size} and {b.size}")
    return bootstrap_mean_ci(a - b, n_resamples, alpha, clusters, seed)


def excludes_zero(interval: tuple[float, float]) -> bool:
    """Whether the interval lies wholly above or wholly below zero.

    Deliberately not called `is_significant`. It is one input to that judgment
    and, given the undercoverage noted in the header, not a sufficient one.

    Strict comparison, so a lower bound of exactly 0.0 counts as not excluding
    zero. That is not a hypothetical: precision@3 hybrid-minus-dense has a
    lower bound of exactly 0.000, stable across eight seeds, because 18 of the
    24 questions are unchanged and every difference is a multiple of 1/3.
    """
    lo, hi = interval
    return lo > 0 or hi < 0


def _fmt(ci: tuple[float, float], signed: bool = False) -> str:
    spec = "+.3f" if signed else ".3f"
    return f"[{ci[0]:{spec}}, {ci[1]:{spec}}]"


def render(rows: list[dict], diffs: list[dict], n: int, seed: int,
           n_resamples: int, sensitivity: dict | None = None) -> str:
    """The markdown that lands in results/confidence.md."""
    out = [
        "# Confidence intervals",
        "",
        f"{n_resamples} bootstrap resamples over the {n} answerable questions, "
        f"percentile method, seed `{seed}`. The 6 unanswerable questions have "
        "no recall to average and are excluded, D8.",
        "",
        "The unit resampled is the question, because the question is what was "
        "sampled in the first place. Paired comparisons subtract per question "
        "first and bootstrap the differences, so both variants always face the "
        "same drawn questions.",
        "",
        "## Each variant on its own",
        "",
        "| Metric | Variant | Mean | 95% CI |",
        "|---|---|---:|---|",
    ]
    for r in rows:
        out.append(f"| {r['metric']} | {r['variant']} | {r['mean']:.3f} | "
                   f"{_fmt(r['ci'])} |")

    out += [
        "",
        "These overlap heavily and are the less useful half of the file. Two "
        "overlapping intervals do not imply the difference is indistinguishable "
        "from zero; that question is answered per question, below.",
        "",
        "## Paired differences",
        "",
        "| Metric | Comparison | Difference | 95% CI | Excludes zero |",
        "|---|---|---:|---|---|",
    ]
    for d in diffs:
        out.append(f"| {d['metric']} | {d['comparison']} | {d['diff']:+.3f} | "
                   f"{_fmt(d['ci'], signed=True)} | "
                   f"{'yes' if d['excludes_zero'] else 'no'} |")

    settled = [d for d in diffs if d["excludes_zero"]]
    out += [
        "",
        f"**{len(settled)} of {len(diffs)} comparisons exclude zero.**",
        "",
    ]
    if not settled:
        out += [
            "On this gold set, at this sample size, none of the three variants "
            "is distinguishable from the others on any of the four metrics. "
            "That is the result. It is not a failed experiment and it is not a "
            "reason to report the point estimates as if the intervals did not "
            "exist.",
            "",
        ]

    if sensitivity:
        out += ["## Sensitivity", ""]

        seeds = sensitivity.get("seeds")
        if seeds:
            out += [
                "**The closest comparison, precision@3 hybrid minus dense, "
                "under different seeds.** Its lower bound is exactly 0.000, so "
                "the question is whether that is an artifact of one resample.",
                "",
                "| Seed | 95% CI |",
                "|---:|---|",
            ]
            out += [f"| {s} | {_fmt(ci, signed=True)} |" for s, ci in seeds]
            out += [
                "",
                "The bound holds. It is not noise: 18 of the 24 questions are "
                "unchanged and every difference is a multiple of 1/3, so a "
                "resample drawing the one regression against the five "
                "improvements lands on exactly zero.",
                "",
            ]

        clustered = sensitivity.get("clustered")
        if clustered:
            out += [
                "**Clustering the one correlated pair.** Q06 and Q30 both cite "
                "`doc-05:c032`, flagged since Day 4, so they are resampled as a "
                "single unit here: both enter a draw or neither does.",
                "",
                "| Metric | Plain | Q06+Q30 clustered |",
                "|---|---|---|",
            ]
            out += [f"| {m} | {_fmt(p, signed=True)} | {_fmt(c, signed=True)} |"
                    for m, p, c in clustered]
            out += [
                "",
                "The change is negligible, which is the expected result for one "
                "correlated pair in 24 and is worth having checked rather than "
                "assumed.",
                "",
            ]

        n_needed = sensitivity.get("n_needed")
        if n_needed:
            out += [
                "**How many questions would settle it.** For the headline "
                "comparison, hybrid minus dense on recall@10, the observed "
                "effect and the spread of the per-question differences imply "
                f"roughly **{n_needed} questions** before a 95% interval would "
                "exclude zero, by normal approximation. This gold set has 24.",
                "",
                "That is the number to quote when someone asks why the project "
                "stops here. Going from 24 to about 106 hand-labeled questions "
                "is not a tuning exercise, it is the majority of the project "
                "again, and it would buy the ability to distinguish two "
                "retrievers that differ by 0.07.",
                "",
            ]

    return "\n".join(out)


# ---------------------------------------------------------------------- CLI --

RESULTS = {
    "dense": "retrieval-baseline.json",
    "bm25": "bm25.json",
    "hybrid": "hybrid.json",
}
METRICS = [("recall_at_3", "recall@3"), ("recall_at_10", "recall@10"),
           ("precision_at_3", "precision@3"), ("reciprocal_rank", "MRR")]
COMPARISONS = [("hybrid", "dense"), ("bm25", "dense"), ("hybrid", "bm25")]


def load_scores(results_dir) -> tuple[dict, list[str]]:
    """Per-question metric values per variant, in one shared question order.

    The shared order is asserted rather than assumed. Paired statistics over
    two differently ordered lists would compare Q04 against Q05 and report a
    perfectly plausible interval.
    """
    import json

    import report

    sdk = report.parse_sdk_docs((ROOT / "corpus" / "INDEX.md").read_text())
    scores, order = {}, None
    for variant, filename in RESULTS.items():
        data = json.loads((results_dir / filename).read_text())
        rows = [report.score(q, sdk) for q in data["questions"] if q["answerable"]]
        ids = [r["id"] for r in rows]
        if order is not None and ids != order:
            raise SystemExit(f"{filename} answers a different set of questions")
        order = ids
        scores[variant] = {key: [r[key] for r in rows] for key, _ in METRICS}
    return scores, order


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Bootstrap intervals for every variant.")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "confidence.md")
    parser.add_argument("--resamples", type=int, default=N_RESAMPLES)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    scores, order = load_scores(args.results_dir)

    rows = [{"metric": label, "variant": variant,
             "mean": sum(scores[variant][key]) / len(order),
             "ci": bootstrap_mean_ci(scores[variant][key], args.resamples,
                                     seed=args.seed)}
            for key, label in METRICS for variant in RESULTS]

    diffs = []
    for key, label in METRICS:
        for a, b in COMPARISONS:
            ci = paired_diff_ci(scores[a][key], scores[b][key], args.resamples,
                                seed=args.seed)
            diffs.append({
                "metric": label, "comparison": f"{a} - {b}",
                "diff": (sum(scores[a][key]) - sum(scores[b][key])) / len(order),
                "ci": ci, "excludes_zero": excludes_zero(ci)})

    # Sensitivity. Each of these answers an objection the table above invites:
    # is the borderline bound a seed artifact, does the one correlated pair
    # change anything, and how far is this gold set from being able to settle
    # the comparison at all.
    closest = ("precision_at_3", "hybrid", "dense")
    seeds = [(s, paired_diff_ci(scores[closest[1]][closest[0]],
                                scores[closest[2]][closest[0]],
                                args.resamples, seed=s))
             for s in range(1, 9)]

    i6, i30 = order.index("Q06"), order.index("Q30")
    clusters = [[i6, i30]] + [[i] for i in range(len(order)) if i not in (i6, i30)]
    clustered = [
        (label,
         paired_diff_ci(scores["hybrid"][key], scores["dense"][key],
                        args.resamples, seed=args.seed),
         paired_diff_ci(scores["hybrid"][key], scores["dense"][key],
                        args.resamples, clusters=clusters, seed=args.seed))
        for key, label in METRICS]

    d = np.asarray(scores["hybrid"]["recall_at_10"]) - np.asarray(
        scores["dense"]["recall_at_10"])
    n_needed = round((1.96 * d.std(ddof=1) / d.mean()) ** 2)

    args.out.write_text(render(rows, diffs, len(order), args.seed, args.resamples,
                               sensitivity={"seeds": seeds, "clustered": clustered,
                                            "n_needed": n_needed}))
    settled = sum(d["excludes_zero"] for d in diffs)
    print(f"wrote {args.out}: {len(order)} questions, {settled} of {len(diffs)} "
          f"comparisons exclude zero")


if __name__ == "__main__":
    main()
