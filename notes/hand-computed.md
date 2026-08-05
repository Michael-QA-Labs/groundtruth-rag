# Hand-computed metrics, Day 6

Corpus `a887366bab9778b5` · index `f0587a0e188318e0` · model `sentence-transformers/all-MiniLM-L6-v2`
Source: `results/retrieval-baseline.json`, variant `dense-baseline`.

**Compute these by hand from the ranked lists below.** Do not run code, and
do not read the counts off the case table in the session transcript, which
gives the answers away. Day 7 writes `src/metrics.py` and checks it against
this file, so a number copied from anywhere else removes the only
independent check those two days have.

Definitions, so the arithmetic is unambiguous:

- `recall@k` = (gold chunks in the top k) / (total gold chunks)
- `precision@k` = (gold chunks in the top k) / k
- `first relevant rank` = rank of the first gold chunk, blank if none

Show the fraction, not just the decimal. The working is the point: Day 7
compares code against it and one of the two will be wrong.

---

## Why these ten

Chosen to span the gold-set size range (1, 2, 3 and 5; no question has 4)
and to cover each distinct arithmetic case exactly once.

| Q | Why it is here |
|---|---|
| Q04 | |gold| = 5, the largest denominator in the set |
| Q01 | |gold| = 3, gold found both inside and outside the top 3 |
| Q02 | |gold| = 3, nothing in the top 10, but not nothing in the top 20 |
| Q14 | |gold| = 3, gold appears only below rank 3 |
| Q23 | |gold| = 2, gold appears only below rank 3 |
| Q25 | |gold| = 2, every gold chunk is inside the top 10 |
| Q26 | |gold| = 2, gold near the top and gold missing, together |
| Q16 | |gold| = 1, gold at rank 1, the best case in the set |
| Q10 | |gold| = 1, no gold chunk anywhere in the top 20 |
| Q11 | unanswerable. Recall and precision are undefined. Highest top-1 score of the six (0.558), so it is the easiest to answer confidently and wrongly |

**Known gap: precision@3 can only come out 0 or 1/3 here.** No question in
the whole set has two gold chunks inside its top 3, so no hand number will
ever exercise a precision numerator above 1. Day 7 must cover that with a
synthetic unit test, because this file cannot.

---

## Q04

**Question:** How can i extract a json using claude code

**Gold chunks (5):** `doc-08:c000`, `doc-01:c011`, `doc-04:c016`, `doc-05:c028`, `doc-19:c008`

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 1 | `doc-19:c009` | headless | 0.517 | |
| 2 | `doc-19:c010` | headless | 0.517 | |
| 3 | `doc-13:c041` | hooks-guide | 0.475 | |
| 4 | `doc-19:c008` | headless | 0.472 | |
| 5 | `doc-14:c108` | hooks | 0.467 | |
| 6 | `doc-13:c003` | hooks-guide | 0.464 | |
| 7 | `doc-19:c007` | headless | 0.461 | |
| 8 | `doc-13:c061` | hooks-guide | 0.454 | |
| 9 | `doc-26:c005` | agent-sdk/custom-tools | 0.444 | |
| 10 | `doc-25:c104` | agent-sdk/python | 0.439 | |

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q01

**Question:** How do i set-up claude code in my CLI

**Gold chunks (3):** `doc-02:c005`, `doc-01:c001`, `doc-02:c001`

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 1 | `doc-01:c000` | overview | 0.714 | |
| 2 | `doc-01:c001` | overview | 0.699 | |
| 3 | `doc-02:c000` | quickstart | 0.668 | |
| 4 | `doc-19:c000` | headless | 0.650 | |
| 5 | `doc-03:c008` | how-claude-code-works | 0.646 | |
| 6 | `doc-10:c005` | permissions | 0.643 | |
| 7 | `doc-07:c004` | settings | 0.640 | |
| 8 | `doc-05:c000` | best-practices | 0.635 | |
| 9 | `doc-02:c001` | quickstart | 0.629 | |
| 10 | `doc-03:c000` | how-claude-code-works | 0.621 | |

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q02

**Question:** How do i import a plugin

**Gold chunks (3):** `doc-05:c020`, `doc-12:c056`, `doc-16:c003`

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 1 | `doc-18:c024` | plugins | 0.561 | |
| 2 | `doc-18:c003` | plugins | 0.535 | |
| 3 | `doc-18:c002` | plugins | 0.510 | |
| 4 | `doc-18:c009` | plugins | 0.509 | |
| 5 | `doc-18:c025` | plugins | 0.504 | |
| 6 | `doc-18:c020` | plugins | 0.501 | |
| 7 | `doc-18:c026` | plugins | 0.472 | |
| 8 | `doc-18:c007` | plugins | 0.459 | |
| 9 | `doc-07:c145` | settings | 0.443 | |
| 10 | `doc-18:c018` | plugins | 0.436 | |

Ranks 11-20, for the diagnosis only. Not part of any metric at k<=10:

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 11 | `doc-07:c135` | settings | 0.434 | |
| 12 | `doc-18:c019` | plugins | 0.432 | |
| 13 | `doc-18:c005` | plugins | 0.422 | |
| 14 | `doc-18:c027` | plugins | 0.421 | |
| 15 | `doc-18:c028` | plugins | 0.420 | |
| 16 | `doc-18:c008` | plugins | 0.414 | |
| 17 | `doc-18:c016` | plugins | 0.412 | |
| 18 | `doc-18:c001` | plugins | 0.409 | |
| 19 | `doc-18:c021` | plugins | 0.405 | |
| 20 | `doc-16:c003` | mcp | 0.392 | |

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q14

**Question:** starting a project in claude code

**Gold chunks (3):** `doc-03:c016`, `doc-05:c010`, `doc-06:c006`

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 1 | `doc-01:c000` | overview | 0.697 | |
| 2 | `doc-05:c037` | best-practices | 0.655 | |
| 3 | `doc-05:c000` | best-practices | 0.650 | |
| 4 | `doc-02:c000` | quickstart | 0.645 | |
| 5 | `doc-02:c012` | quickstart | 0.618 | |
| 6 | `doc-03:c000` | how-claude-code-works | 0.606 | |
| 7 | `doc-01:c001` | overview | 0.604 | |
| 8 | `doc-06:c006` | memory | 0.575 | |
| 9 | `doc-03:c008` | how-claude-code-works | 0.574 | |
| 10 | `doc-04:c002` | common-workflows | 0.569 | |

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q23

**Question:** how do we switch between models in the cli

**Gold chunks (2):** `doc-03:c002`, `doc-07:c015`

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 1 | `doc-07:c049` | settings | 0.466 | |
| 2 | `doc-07:c076` | settings | 0.432 | |
| 3 | `doc-13:c004` | hooks-guide | 0.430 | |
| 4 | `doc-25:c130` | agent-sdk/python | 0.416 | |
| 5 | `doc-25:c040` | agent-sdk/python | 0.408 | |
| 6 | `doc-08:c029` | cli-reference | 0.401 | |
| 7 | `doc-03:c002` | how-claude-code-works | 0.399 | |
| 8 | `doc-11:c009` | checkpointing | 0.395 | |
| 9 | `doc-07:c000` | settings | 0.392 | |
| 10 | `doc-15:c028` | sub-agents | 0.390 | |

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q25

**Question:** how do i stop repeating the same setup instructions to claude every time

**Gold chunks (2):** `doc-06:c001`, `doc-06:c003`

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 1 | `doc-06:c006` | memory | 0.582 | |
| 2 | `doc-06:c036` | memory | 0.550 | |
| 3 | `doc-05:c000` | best-practices | 0.550 | |
| 4 | `doc-23:c000` | output-styles | 0.549 | |
| 5 | `doc-03:c001` | how-claude-code-works | 0.540 | |
| 6 | `doc-06:c001` | memory | 0.536 | |
| 7 | `doc-06:c003` | memory | 0.529 | |
| 8 | `doc-06:c000` | memory | 0.529 | |
| 9 | `doc-05:c020` | best-practices | 0.526 | |
| 10 | `doc-05:c023` | best-practices | 0.525 | |

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q26

**Question:** how do we scan for the health of claude's environment

**Gold chunks (2):** `doc-03:c016`, `doc-08:c006`

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 1 | `doc-01:c000` | overview | 0.484 | |
| 2 | `doc-08:c006` | cli-reference | 0.470 | |
| 3 | `doc-03:c003` | how-claude-code-works | 0.457 | |
| 4 | `doc-05:c000` | best-practices | 0.439 | |
| 5 | `doc-17:c026` | tools-reference | 0.427 | |
| 6 | `doc-05:c010` | best-practices | 0.422 | |
| 7 | `doc-03:c000` | how-claude-code-works | 0.417 | |
| 8 | `doc-15:c002` | sub-agents | 0.411 | |
| 9 | `doc-15:c069` | sub-agents | 0.409 | |
| 10 | `doc-19:c000` | headless | 0.405 | |

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q16

**Question:** does rewind undo edits i made by hand outside claude

**Gold chunks (1):** `doc-11:c007`

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 1 | `doc-11:c007` | checkpointing | 0.550 | |
| 2 | `doc-11:c005` | checkpointing | 0.528 | |
| 3 | `doc-11:c006` | checkpointing | 0.521 | |
| 4 | `doc-11:c002` | checkpointing | 0.516 | |
| 5 | `doc-05:c023` | best-practices | 0.492 | |
| 6 | `doc-21:c026` | code-review | 0.489 | |
| 7 | `doc-11:c001` | checkpointing | 0.489 | |
| 8 | `doc-03:c009` | how-claude-code-works | 0.478 | |
| 9 | `doc-07:c051` | settings | 0.460 | |
| 10 | `doc-17:c032` | tools-reference | 0.450 | |

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q10

**Question:** what are the best practices when prompting in claude code

**Gold chunks (1):** `doc-02:c011`

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 1 | `doc-20:c030` | github-actions | 0.650 | |
| 2 | `doc-05:c020` | best-practices | 0.623 | |
| 3 | `doc-05:c000` | best-practices | 0.620 | |
| 4 | `doc-05:c037` | best-practices | 0.607 | |
| 5 | `doc-23:c000` | output-styles | 0.594 | |
| 6 | `doc-13:c001` | hooks-guide | 0.590 | |
| 7 | `doc-01:c000` | overview | 0.580 | |
| 8 | `doc-06:c006` | memory | 0.580 | |
| 9 | `doc-02:c012` | quickstart | 0.578 | |
| 10 | `doc-05:c001` | best-practices | 0.570 | |

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q11

**Question:** can task monitor tell if a background task will finish or loop forever?

**Gold chunks:** none. Unanswerable.

| Rank | Chunk | Page | Score | Gold? |
|---:|---|---|---:|---|
| 1 | `doc-17:c028` | tools-reference | 0.558 | |
| 2 | `doc-25:c134` | agent-sdk/python | 0.544 | |
| 3 | `doc-25:c136` | agent-sdk/python | 0.533 | |
| 4 | `doc-16:c028` | mcp | 0.521 | |
| 5 | `doc-16:c029` | mcp | 0.517 | |
| 6 | `doc-25:c100` | agent-sdk/python | 0.502 | |
| 7 | `doc-05:c005` | best-practices | 0.499 | |
| 8 | `doc-19:c004` | headless | 0.498 | |
| 9 | `doc-15:c065` | sub-agents | 0.478 | |
| 10 | `doc-25:c149` | agent-sdk/python | 0.475 | |

| Check | Value | Working |
|---|---|---|
| recall@3 | undefined | no gold chunk exists |
| recall@10 | undefined | no gold chunk exists |
| precision@3 | undefined | no gold chunk exists |
| Would a generator given the top 3 decline to answer? | | |

---

## After the ten

Write down, before Day 7:

1. Which arithmetic you had to redo, and why.
2. Any question where the number felt wrong against what the retrieval
   actually did. Those are the D5b cases where recall understates a result
   that served the user.
3. Your prediction for mean recall@10 across all 24 answerable questions.
   Write it down before Day 8 computes it.

