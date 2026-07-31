# Day 2 — chunk, embed, search (coordinated across Days 3–12)

## Context

Day 2 turns the frozen 30-doc corpus into a searchable index. The binding
constraint is not retrieval quality — PLAN.md wants the retriever *deliberately
crude*. It is that **everything from Day 3 to Day 12 is built on Day 2's output**,
and several Day 2 choices are effectively irreversible once gold labeling starts.

Measurement during design surfaced facts that reshaped the work:

- **40% of the corpus is markdown tables** (227 tables, 707,699 chars) — table
  handling *is* the chunking design.
- Repeating table headers per chunk would make **65% of table chunk text
  boilerplate** (1,117,538 chars), starving the token budget.
- **948 table rows contain a pipe inside backticks** — character-level filtering
  of `|` would corrupt them.
- **18% of code fences contain blank lines** — blank-line splitting must not run first.
- **8 substantial blocks appear in 2+ different docs** — so an answer can live in
  more than one place.

## Three core mitigations

### 1. Separate what is LABELED from what is EMBEDDED

| Field | Content | Used for |
|---|---|---|
| `text_raw` | Verbatim slice of `corpus/doc-NN.md` | Gold labeling, verification, conservation |
| `text_embed` | Rendered (MDX transformed, table rows labeled, padding collapsed) | Embedding only |

Labels reference byte-exact source text, so a rendering bug degrades retrieval but
**cannot corrupt the gold set**. Slice raw first, render second.

### 2. Label at two granularities from one label

`gold-set-template.md` labels at doc level (`doc-04`); `PLAN.md` specifies chunk
level (`doc-04:c02`). **They disagree.** Resolution: a chunk ID contains its doc
ID, so record both.

- **Primary:** chunk-level recall/precision — more discriminating, better story.
- **Safety net:** doc-level, free, and **immune to any re-chunking**.

### 3. Measure tokenization BEFORE setting constants

Tables tokenize far denser than prose (every `|`, `---`, backtick is a token), so
a chars-per-token rule of thumb is wrong for 40% of the corpus. Measure on this
corpus's own text, set `TARGET`/`HARD_MAX` from data, chunk **once**.

**Decision rule once measured** (previously unstated — stage A would have produced
a number with no rule for acting on it):

| Measured table chars/token | Action |
|---|---|
| ≥ 3.5 | Proceed as planned (`HARD_MAX` ≈ 1,200) |
| 2.5 – 3.5 | Lower `HARD_MAX` to fit 256 tokens; accept the higher chunk count |
| < 2.5 | Stop and reconsider the model — chunks would be too small to hold a complete answer, which harms labeling more than retrieval |

## Downstream coordination — what Day 2 must guarantee

These are decisions that look like later-day problems but become expensive or
impossible if deferred.

| Day | Risk if unaddressed | Decision made now |
|---|---|---|
| **4** | 5 questions must be *unanswerable*. Verifying "no chunk answers this" across ~1,800 chunks is impossible by eye, and "I searched and didn't find it" is not evidence of absence | **Method, not just tooling:** choose unanswerable questions about topics the docs demonstrably don't cover (pricing, unrelated products, future roadmap) rather than topics you failed to locate. `search.py --top 20 --show-text` then *confirms* the judgment instead of forming it |
| **3** | `gold-set-template.md` has no `answerable` field and uses doc-level IDs, so it cannot express this design's labels | Day 3 begins by revising the template: add `Answerable: yes/no`, use chunk-level `Gold chunks`, keep the worked Q01 example. Flagged now so the mismatch isn't discovered mid-labeling |
| **4** | 8 duplicated blocks mean an answer can live in 2 docs; labeling one scores a correct retrieval as failure | `manifest.json` lists duplicate-`sha256` chunk groups so both get labeled |
| **6/7** | Hand math and code disagree over *definitions*, not bugs — PLAN says "fix whichever is wrong", burning hours on a non-bug | Fix definitions in writing now: doc-level metrics dedupe the ranked chunk list preserving order (top-3 docs = first 3 *distinct* docs); unanswerable questions are **excluded** from recall/precision means and reported separately as an abstention count |
| **6/7** | Score ties make ranks nondeterministic | Stable sort, deterministic tie-break by chunk ID |
| **8** | Failure diagnosis needs retrieved *text*, not IDs | Same `--show-text` path |
| **8/10/11** | Results written only as prose markdown; Day 11 bootstrap needs **per-question** scores and they no longer exist | Every eval run writes machine-readable `results/*.json`; markdown summaries are **derived**, never hand-typed. Minimum contract per question: `qid`, `answerable`, `gold_chunk_ids`, `gold_doc_ids`, `retrieved_ids` (ranked), plus run metadata (corpus hash, manifest hash, model, seed, git SHA). Metric *values* are recomputed from this, never stored as the only copy |
| **9/10** | BM25 run over different text than the dense retriever confounds the comparison — two variables changed | BM25 indexes `text_embed`, the identical text the dense retriever sees |
| **11** | Bootstrap CIs differ run to run | Seed the RNG and record the seed in the results file |
| **12** | A number in the README can't be traced to what produced it | Every results file records corpus hash + manifest hash + model + seed |
| **Phase 2** | Swapping embedder tempts re-chunking, renumbering every ID | **Keep chunks frozen, change only the model.** Recorded as a constraint |
| **Phase 2** | Some models need `query:`/`passage:` prefixes; MiniLM does not. Silent asymmetry ruins the ablation | `manifest.json` records a `query_prefix`/`passage_prefix` field, empty for MiniLM |

## Implementation

### Files (`~/projects/groundtruth-rag/`)

| File | Responsibility |
|---|---|
| `src/tokens.py` | Measure chars/token on sampled table + prose text; report suggested constants |
| `src/mdx.py` | Text → text. D4 per-tag rules. Knows nothing about chunks |
| `src/tables.py` | Backtick-aware cell splitter + labeled-row renderer. Never `split("\|")` |
| `src/chunk.py` | Raw doc → chunks (`text_raw` + `text_embed`) |
| `src/embed.py` | `chunks.jsonl` → `vectors.npz` + `manifest.json` |
| `src/search.py` | Query → ranked chunk IDs + doc IDs, optional text |
| `tests/test_{mdx,tables,chunk,search}.py` | See verification |
| `requirements.txt` | Pinned — the corpus is hashed; the code reading it must be pinned too |

Reuse `CORPUS_DIR` / `PAGES` from `src/fetch_corpus.py`. **Never re-run
`fetch_corpus.py`** — it hits the network and breaks the freeze.

### Chunking rules

1. Extract code fences as atomic blocks (**must precede** step 2).
2. Split remainder on blank lines, **keeping separators**, so the doc is
   partitioned rather than filtered.
3. Classify: `code` / `table` / `prose`.
4. Pack to `TARGET` measured in *rendered* length; record the raw span.

| Block | `text_embed` rendering |
|---|---|
| Code fence | Unchanged |
| Table | Row → subject line + `Label: value`. No repeated header. Padding collapsed. Backticks stripped in cells only |
| Prose | MDX transformed per D4 |

### IDs and record shape

`doc-07:c000` — three digits (`doc-07` yields ~771 chunks; three digits also sort
lexicographically for grepping).

Fields: `id`, `doc_id`, `slug`, `text_raw`, `text_embed`, `char_start`, `char_end`,
`chars_raw`, `tokens_embed`, `block_type`, `sha256`, `sha256_norm`.

**Two hashes, because they serve opposite purposes** (an ambiguity in the previous
draft: "normalized" was undefined and the single field could not do both):

- `sha256` — of `text_raw` **exactly**, byte for byte. Detects re-chunk drift. Any
  normalization here would hide a real change.
- `sha256_norm` — of `text_raw` with whitespace collapsed and case folded. Groups
  near-identical chunks across docs. Exactness here would miss duplicates that
  differ only by table padding.

### Storage

```
index/
├── chunks.jsonl     committed — gold labels point at these
├── vectors.npz      gitignored — ids[] + float32, joined by ID never row order
└── manifest.json    committed — corpus hash, params, model, versions,
                     per-doc chunk counts, duplicate groups, prefix fields,
                     vectors hash, git SHA of the code that built it
```

The git SHA closes the traceability loop: corpus hash names the input, vectors
hash names the index, git SHA names the code. Any Day 12 README number can be
traced to all three.

## Verification

| Where | Assertion |
|---|---|
| `chunk.py` | `"".join(text_raw)` per doc == the file, **byte-for-byte** (verified achievable: 30/30) |
| `chunk.py` | No chunk over `HARD_MAX`; none empty; IDs unique and sequential |
| `tables.py` | Rendered cell count == source cell count (catches the 948 pipe-in-backtick rows) |
| `embed.py` | Zero chunks truncate under the real tokenizer; corpus hash matches `corpus/INDEX.md`; norms ≈ 1.0 |
| `search.py` | Manifest model == loaded model; `len(ids) == len(vectors)` |

**Tests:** `test_tables.py` (pipe-in-backticks keeps one cell; extra cells kept;
padding collapse loses no non-space chars) · `test_mdx.py` (`<Tabs>`/`<Steps>` on
real `quickstart`; `<Note>` unwrapped; `<div>` dropped) · `test_chunk.py`
(exact-partition conservation; hard max; fence with blank lines survives) ·
`test_search.py` (cosine ranking + tie-break on synthetic vectors, no model load).

**Manual gate before Day 3:** `python src/chunk.py --inspect 10` prints a
*stratified* sample (table, code, prose, `<Tabs>`, `<Steps>`, one from `settings`,
one from `checkpointing`) showing `text_raw` and `text_embed` side by side, and
writes it to `notes/chunk-inspection.md` — evidence for the Day 12 README that
the chunks were checked before labeling, not assumed.

`requirements.txt` includes `pytest`; `tests/` does not yet exist and is created
in stage B.

## Scope and sequencing

PLAN.md budgets **5 hours** for Day 2, assuming Michael writes the code. Here
Claude writes it, so the real constraint is **review time, not writing time** —
the project rule requires Michael can explain every line tomorrow, and Day 2 is
roughly 5x Day 1's volume.

Day 2 builds the *tools* Days 3–5 need; it cannot do their work. Writing 30
questions from memory and judging which chunks answer them is irreducibly
Michael's. Each stage below ends somewhere usable, with a review pause:

| Stage | Deliverable | Cuttable? |
|---|---|---|
| A | `tokens.py`, constants set from measurement | No — prevents a re-chunk |
| B | `mdx.py` + `tables.py` + tests | No — protects the gold set |
| C | `chunk.py` + conservation assertion + `--inspect` | No — the Day 4 gate |
| D | `embed.py` + `search.py` | No — Day 2's "done when" |
| E | golden snapshot test, duplicate-group reporting | **Yes** — defer if time runs short |

Written in the teaching-comment style used in `src/fetch_corpus.py`, with a review
pause after each stage so the project rule ("every line is one you can explain")
holds for code this size.

## Done when

- `python src/tokens.py` reports measured chars/token; constants set from it
- `python src/chunk.py` writes `index/chunks.jsonl`, all assertions pass
- `python src/embed.py` writes `vectors.npz` + `manifest.json`, zero truncations
- `python src/search.py "how do I stop Claude asking before every file edit?"`
  returns 10 ranked chunk IDs with doc IDs
- `pytest` green
- `--inspect 10` output read and judged sane by Michael

## Residual risks

| Risk | Status |
|---|---|
| Chunker corrupts gold labels | **Eliminated** — labels reference byte-exact `text_raw` |
| Content silently lost | **Eliminated** — exact-partition assertion, provable |
| Re-chunking invalidates labels | **Downgraded** — doc-level metrics survive; `sha256` identifies moved labels |
| Truncation forces re-chunk | **Downgraded** — tokenization measured first |
| Metric definition drift Day 6→7 | **Closed** — definitions fixed in writing above |
| Day 11 lacks per-question data | **Closed** — JSON results from Day 8 onward |
| `torch` on Python 3.14 | **Open** — fallback: 3.12/3.13 venv, or `fastembed` (ONNX). No design impact |
| Answers straddling chunks | **Open by design** — gold format supports multiple chunks (Q10 is multi-hop); a Day 3 judgment |
| Comprehension debt — Day 2 is ~5x Day 1's code, and the project rule is "every line is one you can explain tomorrow" | **Managed** — staged A–E with a review pause after each. This, not schedule, is the real scarce resource: Claude writes the code, so Michael's review time is the constraint |
| Day 2 overruns and consumes Days 3–5 *calendar time* (it cannot do their work — the gold set is irreducibly Michael's judgment) | **Managed** — stage E is the release valve; A–D are load-bearing |
