# Five failures, read chunk by chunk

Day 8, 2026-08-06. Baseline `dense-baseline`, corpus `a887366bab9778b5`,
index `f0587a0e188318e0`. Numbers from `results/baseline.md`.

## How these five were chosen

Not by lowest recall. On this gold set that would select the questions with
the most D5a alternatives, since retrieving one sufficient chunk of five
scores 0.20 (D5b). It would also be a nine-way tie: **12 of 24 answerable
questions return no gold chunk in the top 10, and 9 return none in the top 20
either.** Every one of those nine scores exactly 0.00 on every metric.

So the tie was broken by re-running the retriever at full depth over all
1,637 chunks and asking **how deep the first gold chunk actually sits**. That
run reproduces the stored top 20 for all 30 questions exactly, so it describes
the same retriever, and it turns a nine-way tie into a severity ordering.

```
.venv/bin/python src/run_retrieval.py --top 1637 --out /tmp/full-depth.json
```

The output is scratch and deliberately not in `results/`: it is 5.4 MB, it is
derivable from the frozen index in about a minute, and the only numbers worth
keeping from it are in the table below.

| Q | first gold chunk, rank of 1,637 | all gold ranks |
|---|---:|---|
| Q10 | 916 | 916 |
| Q22 | 192 | 192, 260 |
| Q21 | 160 | 160 |
| Q06 | 89 | 89, 189 |
| Q29 | 71 | 71 |
| Q08 | 69 | 69, 312 |
| Q18 | 43 | 43, 60, 67 |
| Q05 | 36 | 36 |
| Q30 | 22 | 22, 44 |

**Q10 is excluded, and it is the worst number in the set.** Its Day 5 ruling
stands: the question has no determinate answer, its label is correct, and a
gold chunk at rank 916 is a fact about a question that admits many readings
rather than a retrieval defect. Writing it up as a miss would be the third
time this project has had to un-learn that. Read the Day 5 entry, not this
file.

That leaves Q22, Q21, Q06, Q29 and Q08.

---

## F1 — Q22: the question's vocabulary belongs to another product surface

**"how do we check for token usage"** · gold `doc-03:c011`, `doc-03:c013`
(`how-claude-code-works`) at ranks 192 and 260 · **7 of the top 10 are
`agent-sdk/cost-tracking`**, and rank 1 is `doc-29:c001`.

The gold answer is one line: run `/context` to see what is using space in the
context window. The retriever returned a page about counting API spend.

Both are literally about tokens, which is the problem. "Token usage" is the
vocabulary of billing, and there is a whole page in this corpus about billing.
The user's meaning, "what is filling my context window", is expressed in the
docs with the word `/context` and the word "space", neither of which appears
in the question. Nothing about the retrieval is broken; the query means two
things and the corpus answers the other one.

**This is the strongest live instance of D7.** No gold chunk anywhere in the
set comes from the seven `agent-sdk/*` pages, so those 7 hits are
product-surface confusion by construction, and they are 7 of the 21 such hits
in the entire answerable set. One question holds a third of them.

**What would fix it:** nothing in the retriever, at k=10. The gold is at 192.
Hybrid retrieval will not close a 192-rank gap on a query whose keywords
genuinely match the wrong page better. The honest fix is a query the user
would also plausibly type, and Day 9 should check whether BM25 on `/context`
does anything at all here. Expect it not to.

---

## F2 — Q21: a list of links outranks the instructions it links to

**"how do we create a skill for the agent"** · gold `doc-12:c006` (`skills`)
at rank 160 · 5 of the top 10 are from `doc-12`, the right page.

Rank 1 is `doc-12:c076`, which is the "Related resources" block at the bottom
of the skills page: eight bullet points, each one a link with a short gloss,
containing the words skill, skills, skill-creation, skill authoring, subagents,
plugins, hooks, memory, commands and permissions.

The gold chunk is the part of the page that actually answers the question:
`mkdir -p ~/.claude/skills/summarize-changes`, then write a `SKILL.md` with
frontmatter. It sits at 160.

**The page was found and the chunk was not.** A navigation block is nothing but
high-value terms with no prose diluting them, so it looks like a dense match
for almost any query about its own page. The instructional chunk spends most of
its tokens on English sentences and a code block, which the embedding treats as
less on-topic than a list of link labels.

**What would fix it:** this one is tractable and worth trying. Chunks that are
mostly link list are identifiable structurally, and either down-weighting them
or excluding them from the index is a small, testable change. It is also
exactly the kind of change that needs Day 11's confidence interval before
anyone claims it helped, because it will move a handful of questions.

---

## F3 — Q06 and Q08: the page that answers "when should I use X" is not in the corpus

**"when to use auto mode in claude code"** · gold `doc-05:c015`,
`doc-05:c032` (`best-practices`) at ranks 189 and 89.
**"when to use plan mode in claude code"** · gold `doc-04:c015`
(`common-workflows`) at 69 and `doc-03:c018` at 312.

Both return the same shape of wrong answer. Q06's top 3 are all
`cli-reference` table rows, including the row documenting
`claude auto-mode reset`. Q08's rank 1 is the `cli-reference` row for
`--permission-mode`, listing `default`, `acceptEdits`, `plan`, `auto`,
`dontAsk`, `bypassPermissions`. Both are precisely on topic and neither
answers "when".

**The cause is a corpus gap, not a ranking failure.**
`permission-modes` is the canonical page for both questions and **it was never
fetched**. It is linked from 29 chunks across 11 of the 30 pages, including
from the very rows that got returned.

The gap itself is not news. The README has listed six cited-but-absent pages
since Day 4, `permission-modes` among them, found while labeling. What is new
is the cost: it is now the direct cause of **two of the five worst failures in
the baseline**, and the Day 4 note that "four questions survive only because
another page happens to restate the material" understated it. Surviving as a
label and surviving as a retrieval target are different things. Q23 hit the
same hole at `model-config`, linked from 32 chunks across 10 pages.

With the canonical page missing, the gold had to be assembled from the best
available mentions, which are a paragraph of best-practices prose (`doc-05:c032`,
one sentence on the classifier model that reviews commands) and a section of
common-workflows (`doc-04:c015`, "Plan before editing"). Those are genuinely
the right labels for this corpus. They are also short, incidental passages
competing against a reference table that names the exact feature.

**What would fix it, and why not to do it:** fetching `permission-modes` would
fix both questions and would break the corpus freeze, D1, invalidating the
index hash, every stored result and the gold set's chunk IDs. Not worth it for
two questions. Record it as a limitation, say so in the README, and fetch it in
a v2 that re-labels from scratch. **What is worth doing now** is counting how
many of the other 22 questions have this shape, because "the answer isn't in
the corpus" and "the retriever missed it" are different projects.

---

## F4 — Q29: the right section, two chunks away, at rank 71

**"what can i do before a long session summarises itself"** · gold
`doc-09:c063` (`context-window`) at rank 71 · rank 3 is `doc-09:c061`, the same
page, two chunks earlier.

`doc-09:c063` is the answer verbatim: compact with a focus, `/clear` between
tasks, delegate large reads to a subagent. It begins "You can also act before
the automatic pass runs", which is the question restated.

`doc-09:c061`, retrieved at rank 3, is the "What survives compaction" table:
what happens to the system prompt, the output style, and CLAUDE.md when a
session compacts. It names the mechanism repeatedly and answers a different
question.

**The retriever preferred the chunk that names the machinery over the chunk
that tells the user what to do.** The question is phrased entirely in user
language, "before a long session summarises itself", with none of the words
`/compact`, `/clear`, or "context window" in it. The mechanism-naming chunk
wins on the words that are shared, and the actionable chunk loses by 68 ranks.

This is the same failure as F2 seen from a different angle: within the right
page, the chunk that reads like documentation beats the chunk that reads like
an answer.

---

## What the five have in common

**Three of the five never had a chance at k=10.** Q22's gold is at 192,
Q21's at 160, Q06's at 89. No reranking of a top-50 candidate list touches
them, which means the top-of-funnel is the constraint, not the ordering.
Any Day 9 or Day 13 claim about improvement should say which of these it could
possibly have moved before it says what it measured.

**Two are the same bug at different scales.** F2 and F4 are both cases where
the correct page ranked well and the correct chunk did not, beaten by a chunk
whose text is denser in topic words and lighter in content. That is a chunking
and weighting problem, it is the most tractable thing in this file, and it is
the one I would take to Day 9 first.

**One is not a retrieval failure at all.** F3 is a corpus decision from Day 1
surfacing five days later, and the honest response is to write it down rather
than to tune anything.

**The user's words and the documentation's words are different words.** Every
one of these five questions was written with the docs closed, per Day 3, and
that is exactly why they expose this. "Token usage" against `/context`.
"Summarises itself" against "compaction". "When to use" against a flag table.
The vocabulary-leak check on Day 5 found 0 of 24 questions sharing rare words
with their own gold chunks, and it was treated then as a clean bill of health.
Read next to this file it is better understood as a measurement of the gap the
retriever has to cross, and on the evidence here it does not cross it.

## One thing to check on Day 9 before anything else

Of the 24 answerable questions, how many are F3-shaped, where the best
available gold is an incidental mention because the canonical page is outside
the corpus? Q06, Q08 and Q23 are three. If that number is large, the baseline
of 0.362 is partly a measurement of the corpus and the whole Day 9 comparison
should be read on the subset where it is not.
