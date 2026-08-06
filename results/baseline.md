# Baseline, dense-baseline

Run 2026-08-06. Corpus `a887366bab9778b5` · index `f0587a0e188318e0` · model `sentence-transformers/all-MiniLM-L6-v2` · top 20 stored.

Means are over the 24 answerable questions only. The 6 unanswerable ones have no gold chunk, so recall and precision on them are 0/0, not 0. See D8.

| Metric | Value |
|---|---:|
| mean recall@3 | 0.181 |
| mean recall@10 | 0.362 |
| mean precision@3 | 0.083 |
| MRR | 0.215 |

The counts say more than the means:

- **12 of 24 answerable questions return no gold chunk in the top 10.**
- 9 return none in the top 20 either.
- 2 put a gold chunk at rank 1.
- SDK chunks take 21 of 240 answerable top-10 slots (8.8%). No gold chunk comes from those 7 pages, so every one of them is a product-surface confusion by construction (D7).

## Per question

`|gold|` is the size of the gold set and the ceiling on recall@3 when one chunk is retrieved. `first` is the rank of the first gold chunk. Read those two before the scores wherever `|gold| > 1` (D5b).

| Q | \|gold\| | recall@3 | recall@10 | precision@3 | RR | first | SDK@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Q01 | 3 | 0.33 | 0.67 | 0.33 | 0.500 | 2 | 0 |
| Q02 | 3 | 0.00 | 0.00 | 0.00 | 0.050 | 20 | 0 |
| Q03 | 1 | 0.00 | 0.00 | 0.00 | 0.077 | 13 | 1 |
| Q04 | 5 | 0.00 | 0.20 | 0.00 | 0.250 | 4 | 2 |
| Q05 | 1 | 0.00 | 0.00 | 0.00 | 0.000 |  | 1 |
| Q06 | 2 | 0.00 | 0.00 | 0.00 | 0.000 |  | 0 |
| Q07 | 1 | 1.00 | 1.00 | 0.33 | 0.500 | 2 | 2 |
| Q08 | 2 | 0.00 | 0.00 | 0.00 | 0.000 |  | 0 |
| Q09 | 1 | 0.00 | 1.00 | 0.00 | 0.167 | 6 | 0 |
| Q10 | 1 | 0.00 | 0.00 | 0.00 | 0.000 |  | 0 |
| Q11 |  | undefined | undefined | undefined | undefined |  | 4 |
| Q12 | 1 | 0.00 | 0.00 | 0.00 | 0.067 | 15 | 0 |
| Q13 |  | undefined | undefined | undefined | undefined |  | 8 |
| Q14 | 3 | 0.00 | 0.33 | 0.00 | 0.125 | 8 | 0 |
| Q15 | 2 | 0.50 | 0.50 | 0.33 | 1.000 | 1 | 0 |
| Q16 | 1 | 1.00 | 1.00 | 0.33 | 1.000 | 1 | 0 |
| Q17 |  | undefined | undefined | undefined | undefined |  | 3 |
| Q18 | 3 | 0.00 | 0.00 | 0.00 | 0.000 |  | 0 |
| Q19 |  | undefined | undefined | undefined | undefined |  | 0 |
| Q20 |  | undefined | undefined | undefined | undefined |  | 0 |
| Q21 | 1 | 0.00 | 0.00 | 0.00 | 0.000 |  | 1 |
| Q22 | 2 | 0.00 | 0.00 | 0.00 | 0.000 |  | 7 |
| Q23 | 2 | 0.00 | 0.50 | 0.00 | 0.143 | 7 | 2 |
| Q24 | 1 | 0.00 | 1.00 | 0.00 | 0.125 | 8 | 0 |
| Q25 | 2 | 0.00 | 1.00 | 0.00 | 0.167 | 6 | 0 |
| Q26 | 2 | 0.50 | 0.50 | 0.33 | 0.500 | 2 | 0 |
| Q27 |  | undefined | undefined | undefined | undefined |  | 1 |
| Q28 | 1 | 1.00 | 1.00 | 0.33 | 0.500 | 2 | 3 |
| Q29 | 1 | 0.00 | 0.00 | 0.00 | 0.000 |  | 1 |
| Q30 | 2 | 0.00 | 0.00 | 0.00 | 0.000 |  | 1 |

Rows reading `undefined` are the unanswerable questions. They are excluded from every mean above and their retrieved chunks are the material for the abstention question, not for recall.
