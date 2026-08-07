# Baseline, hybrid-rrf60

Run 2026-08-06. Corpus `a887366bab9778b5` · index `f0587a0e188318e0` · model `sentence-transformers/all-MiniLM-L6-v2` · top 20 stored.

Means are over the 24 answerable questions only. The 6 unanswerable ones have no gold chunk, so recall and precision on them are 0/0, not 0. See D8.

| Metric | Value |
|---|---:|
| mean recall@3 | 0.286 |
| mean recall@10 | 0.433 |
| mean precision@3 | 0.139 |
| MRR | 0.288 |

The counts say more than the means:

- **10 of 24 answerable questions return no gold chunk in the top 10.**
- 8 return none in the top 20 either.
- 3 put a gold chunk at rank 1.
- SDK chunks take 21 of 240 answerable top-10 slots (8.8%). No gold chunk comes from those 7 pages, so every one of them is a product-surface confusion by construction (D7).

## Per question

`|gold|` is the size of the gold set and the ceiling on recall@3 when one chunk is retrieved. `first` is the rank of the first gold chunk. Read those two before the scores wherever `|gold| > 1` (D5b).

| Q | \|gold\| | recall@3 | recall@10 | precision@3 | RR | first | SDK@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Q01 | 3 | 0.33 | 0.67 | 0.33 | 0.333 | 3 | 1 |
| Q02 | 3 | 0.00 | 0.00 | 0.00 | 0.000 |  | 0 |
| Q03 | 1 | 0.00 | 0.00 | 0.00 | 0.056 | 18 | 1 |
| Q04 | 5 | 0.20 | 0.40 | 0.33 | 0.333 | 3 | 2 |
| Q05 | 1 | 0.00 | 0.00 | 0.00 | 0.000 |  | 2 |
| Q06 | 2 | 0.00 | 0.00 | 0.00 | 0.053 | 19 | 0 |
| Q07 | 1 | 0.00 | 0.00 | 0.00 | 0.000 |  | 4 |
| Q08 | 2 | 0.00 | 0.50 | 0.00 | 0.100 | 10 | 0 |
| Q09 | 1 | 1.00 | 1.00 | 0.33 | 1.000 | 1 | 1 |
| Q10 | 1 | 0.00 | 0.00 | 0.00 | 0.000 |  | 0 |
| Q11 |  | undefined | undefined | undefined | undefined |  | 6 |
| Q12 | 1 | 1.00 | 1.00 | 0.33 | 0.333 | 3 | 0 |
| Q13 |  | undefined | undefined | undefined | undefined |  | 3 |
| Q14 | 3 | 0.33 | 0.33 | 0.33 | 1.000 | 1 | 0 |
| Q15 | 2 | 0.50 | 0.50 | 0.33 | 0.500 | 2 | 0 |
| Q16 | 1 | 1.00 | 1.00 | 0.33 | 0.500 | 2 | 0 |
| Q17 |  | undefined | undefined | undefined | undefined |  | 4 |
| Q18 | 3 | 0.00 | 0.00 | 0.00 | 0.000 |  | 2 |
| Q19 |  | undefined | undefined | undefined | undefined |  | 0 |
| Q20 |  | undefined | undefined | undefined | undefined |  | 0 |
| Q21 | 1 | 0.00 | 0.00 | 0.00 | 0.000 |  | 0 |
| Q22 | 2 | 0.00 | 0.00 | 0.00 | 0.000 |  | 6 |
| Q23 | 2 | 0.00 | 0.50 | 0.00 | 0.250 | 4 | 1 |
| Q24 | 1 | 1.00 | 1.00 | 0.33 | 0.500 | 2 | 0 |
| Q25 | 2 | 0.00 | 1.00 | 0.00 | 0.250 | 4 | 0 |
| Q26 | 2 | 0.50 | 0.50 | 0.33 | 0.500 | 2 | 0 |
| Q27 |  | undefined | undefined | undefined | undefined |  | 0 |
| Q28 | 1 | 1.00 | 1.00 | 0.33 | 1.000 | 1 | 0 |
| Q29 | 1 | 0.00 | 1.00 | 0.00 | 0.200 | 5 | 0 |
| Q30 | 2 | 0.00 | 0.00 | 0.00 | 0.000 |  | 1 |

Rows reading `undefined` are the unanswerable questions. They are excluded from every mean above and their retrieved chunks are the material for the abstention question, not for recall.
