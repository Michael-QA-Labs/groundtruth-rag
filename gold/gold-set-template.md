# Gold set — Exercise 1

Corpus: _(fill in — see corpus.md)_
Built on: _(date)_

---

## Q01 — WORKED EXAMPLE (leave this one, it's your reference)

**Question:** How do I stop Claude asking me before every single file edit?

**Type:** configuration
**Answerable:** yes
**Gold chunks:** `doc-04`
**Gold answer:** Permission prompts are controlled by the permissions settings
in `settings.json`; adding tools to the allow list lets them run without a
prompt.

**Why this question is good:** the user's phrasing shares no rare vocabulary
with the gold chunk. The chunk talks about "permissions" and "allowedTools";
the user says "stop asking me before every edit." A retriever has to bridge
that gap semantically, which is exactly what you want to measure.

**Retrieved top 10:** `doc-11, doc-04, doc-02, doc-19, doc-07, doc-03, doc-15, doc-01, doc-22, doc-08`

| Metric | Value | Working |
|---|---|---|
| recall@3 | 1.0 | doc-04 is at rank 2, and it's the only gold chunk → 1/1 |
| recall@10 | 1.0 | same |
| precision@3 | 0.333 | 1 gold in the top 3 → 1/3 |
| first relevant rank | 2 | |

---

## Q02

**Question:**

**Type:**
**Answerable:**
**Gold chunks:**
**Gold answer:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q03

**Question:**

**Type:**
**Answerable:**
**Gold chunks:**
**Gold answer:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q04

**Question:**

**Type:**
**Answerable:**
**Gold chunks:**
**Gold answer:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q05

**Question:**

**Type:**
**Answerable:**
**Gold chunks:**
**Gold answer:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q06

**Question:**

**Type:**
**Answerable:**
**Gold chunks:**
**Gold answer:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q07

**Question:**

**Type:**
**Answerable:**
**Gold chunks:**
**Gold answer:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q08

**Question:**

**Type:**
**Answerable:**
**Gold chunks:**
**Gold answer:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q09

**Question:**

**Type:**
**Answerable:**
**Gold chunks:**
**Gold answer:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

## Q10 — make this one multi-hop (two or more gold chunks)

**Question:**

**Type:** multi_hop
**Answerable:** yes
**Gold chunks:**
**Gold answer:**

**Retrieved top 10:**

| Metric | Value | Working |
|---|---|---|
| recall@3 | | |
| recall@10 | | |
| precision@3 | | |
| first relevant rank | | |

---

# Averages

| Metric | Mean across 10 questions |
|---|---|
| recall@3 | |
| recall@10 | |
| precision@3 | |

**Questions where no gold chunk was retrieved at all (first rank = —):** ___ / 10

That last count is your hard ceiling. Those questions are unanswerable by your
generator no matter what you do to the prompt.
