# Confidence intervals

2000 bootstrap resamples over the 24 answerable questions, percentile method, seed `20260806`. The 6 unanswerable questions have no recall to average and are excluded, D8.

The unit resampled is the question, because the question is what was sampled in the first place. Paired comparisons subtract per question first and bootstrap the differences, so both variants always face the same drawn questions.

## Each variant on its own

| Metric | Variant | Mean | 95% CI |
|---|---|---:|---|
| recall@3 | dense | 0.181 | [0.056, 0.326] |
| recall@3 | bm25 | 0.167 | [0.042, 0.312] |
| recall@3 | hybrid | 0.286 | [0.132, 0.454] |
| recall@10 | dense | 0.362 | [0.203, 0.536] |
| recall@10 | bm25 | 0.453 | [0.293, 0.625] |
| recall@10 | hybrid | 0.433 | [0.271, 0.607] |
| precision@3 | dense | 0.083 | [0.028, 0.153] |
| precision@3 | bm25 | 0.069 | [0.014, 0.125] |
| precision@3 | hybrid | 0.139 | [0.069, 0.208] |
| MRR | dense | 0.215 | [0.111, 0.340] |
| MRR | bm25 | 0.203 | [0.106, 0.323] |
| MRR | hybrid | 0.288 | [0.164, 0.425] |

These overlap heavily and are the less useful half of the file. Two overlapping intervals do not imply the difference is indistinguishable from zero; that question is answered per question, below.

## Paired differences

| Metric | Comparison | Difference | 95% CI | Excludes zero |
|---|---|---:|---|---|
| recall@3 | hybrid - dense | +0.106 | [-0.042, +0.281] | no |
| recall@3 | bm25 - dense | -0.014 | [-0.236, +0.201] | no |
| recall@3 | hybrid - bm25 | +0.119 | [-0.065, +0.299] | no |
| recall@10 | hybrid - dense | +0.071 | [-0.075, +0.217] | no |
| recall@10 | bm25 - dense | +0.090 | [-0.132, +0.306] | no |
| recall@10 | hybrid - bm25 | -0.019 | [-0.181, +0.142] | no |
| precision@3 | hybrid - dense | +0.056 | [+0.000, +0.125] | no |
| precision@3 | bm25 - dense | -0.014 | [-0.111, +0.069] | no |
| precision@3 | hybrid - bm25 | +0.069 | [-0.014, +0.153] | no |
| MRR | hybrid - dense | +0.072 | [-0.054, +0.217] | no |
| MRR | bm25 - dense | -0.013 | [-0.190, +0.157] | no |
| MRR | hybrid - bm25 | +0.085 | [-0.060, +0.223] | no |

**0 of 12 comparisons exclude zero.**

On this gold set, at this sample size, none of the three variants is distinguishable from the others on any of the four metrics. That is the result. It is not a failed experiment and it is not a reason to report the point estimates as if the intervals did not exist.

## Sensitivity

**The closest comparison, precision@3 hybrid minus dense, under different seeds.** Its lower bound is exactly 0.000, so the question is whether that is an artifact of one resample.

| Seed | 95% CI |
|---:|---|
| 1 | [+0.000, +0.125] |
| 2 | [+0.000, +0.125] |
| 3 | [+0.000, +0.125] |
| 4 | [+0.000, +0.125] |
| 5 | [+0.000, +0.111] |
| 6 | [+0.000, +0.111] |
| 7 | [+0.000, +0.125] |
| 8 | [+0.000, +0.125] |

The bound holds. It is not noise: 18 of the 24 questions are unchanged and every difference is a multiple of 1/3, so a resample drawing the one regression against the five improvements lands on exactly zero.

**Clustering the one correlated pair.** Q06 and Q30 both cite `doc-05:c032`, flagged since Day 4, so they are resampled as a single unit here: both enter a draw or neither does.

| Metric | Plain | Q06+Q30 clustered |
|---|---|---|
| recall@3 | [-0.042, +0.281] | [-0.041, +0.284] |
| recall@10 | [-0.075, +0.217] | [-0.069, +0.217] |
| precision@3 | [+0.000, +0.125] | [+0.000, +0.120] |
| MRR | [-0.054, +0.217] | [-0.057, +0.205] |

The change is negligible, which is the expected result for one correlated pair in 24 and is worth having checked rather than assumed.

**How many questions would settle it.** For the headline comparison, hybrid minus dense on recall@10, the observed effect and the spread of the per-question differences imply roughly **106 questions** before a 95% interval would exclude zero, by normal approximation. This gold set has 24.

That is the number to quote when someone asks why the project stops here. Going from 24 to about 106 hand-labeled questions is not a tuning exercise, it is the majority of the project again, and it would buy the ability to distinguish two retrievers that differ by 0.07.
