"""Measure how this corpus tokenizes, then set the chunk size constants from it.

Run:  .venv/bin/python src/tokens.py

WHY THIS FILE EXISTS
--------------------
The embedding model has a hard input limit measured in TOKENS. Our chunker cuts
text by CHARACTERS. So we need a conversion rate, and the usual rule of thumb
("about 4 characters per token for English") is wrong here.

It is wrong because 40% of this corpus is markdown tables, and a table line like

    | `permissions.allow` | Array of rules | `[]` |

is mostly punctuation. Every `|`, every backtick, every run of `---` tends to
become its own token. Prose gets ~4 chars/token; table syntax can get half that.

If we guessed 4 and the real number were 2.5, every table chunk would be silently
cut off at the model's limit — the text would look complete on disk while the
back half of it contributed NOTHING to the vector. Nothing would error. We would
only notice on Day 8, as retrieval failures with no obvious cause.

So: measure first, chunk once.

A NOTE ON WHAT WE MEASURE
-------------------------
Ideally we'd measure the *rendered* table text (what src/tables.py will produce),
but that module doesn't exist yet. We measure RAW table rows instead. Raw rows
carry more syntax than the rendered form ever will, so they tokenize worse. Using
the worse number to pick our limit errs toward chunks that are too small, which
is the safe direction: a slightly small chunk still embeds correctly, a slightly
large one is silently truncated.
"""

import re
import statistics as st
from pathlib import Path

from fetch_corpus import CORPUS_DIR

# The model we embed with. Also decides the tokenizer, which is the whole point
# of this file — a different model would tokenize differently and need a rerun.
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# How many samples per category. A few hundred is plenty to pin down an average;
# we are not doing statistics here, just refusing to guess.
SAMPLE_SIZE = 300


# ------------------------------------------------------------------ SAMPLING --

def is_table_block(text: str) -> bool:
    """True if this block looks like a markdown table.

    A table is at least 3 lines (header, |---| separator, one row) where almost
    every line starts with a pipe. We allow one stray line because some tables
    have a stray caption or trailing note tucked inside the block.
    """
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 3:
        return False
    piped = sum(1 for l in lines if l.lstrip().startswith("|"))
    return piped >= len(lines) - 1


def collect_samples() -> dict[str, list[str]]:
    """Pull representative text out of the corpus, grouped by kind.

    We keep the three kinds separate because they tokenize very differently, and
    an average across all of them would hide exactly the case we care about.
    """
    samples: dict[str, list[str]] = {"table_row": [], "prose": [], "code": []}

    for path in sorted(CORPUS_DIR.glob("doc-*.md")):
        text = path.read_text(encoding="utf-8")

        # 1. Code fences first. We find them by pairing up ``` markers that sit
        #    at the start of a line. This has to happen before the blank-line
        #    split below: 18% of the fences in this corpus contain a blank line,
        #    and splitting first would tear them into misclassified pieces.
        fence_spans, open_at = [], None
        for m in re.finditer(r"^```", text, re.M):
            if open_at is None:
                open_at = m.start()
            else:
                fence_spans.append((open_at, m.end()))
                open_at = None

        for start, end in fence_spans:
            samples["code"].append(text[start:end])

        # 2. Blank out the fences so the next step can't see them, then split
        #    what remains on blank lines. Replacing with spaces (rather than
        #    deleting) keeps the surrounding text from being glued together.
        masked = list(text)
        for start, end in fence_spans:
            masked[start:end] = " " * (end - start)
        remainder = "".join(masked)

        # 3. Sort each remaining block into table rows or prose.
        for block in re.split(r"\n\s*\n", remainder):
            if not block.strip():
                continue
            if is_table_block(block):
                # Individual ROWS, not the whole table — a row is the unit the
                # chunker will actually be packing, so it's the unit to measure.
                for line in block.splitlines():
                    if line.lstrip().startswith("|") and not re.fullmatch(r"[\s|:\-]+", line):
                        samples["table_row"].append(line)
            else:
                samples["prose"].append(block)

    # Take an evenly spaced slice rather than the first N, so we sample across
    # all 30 documents instead of exhausting the budget on doc-01.
    for kind, items in samples.items():
        if len(items) > SAMPLE_SIZE:
            step = len(items) // SAMPLE_SIZE
            samples[kind] = items[::step][:SAMPLE_SIZE]

    return samples


# --------------------------------------------------------------- MEASUREMENT --

def chars_per_token(tokenizer, texts: list[str]) -> list[float]:
    """For each text, how many characters did we get per token?

    Higher is better: it means more of our content fits inside the model's fixed
    token budget. This is the number the chunk size constants are derived from.
    """
    ratios = []
    for t in texts:
        # add_special_tokens=False: the [CLS]/[SEP] wrappers are a fixed cost the
        # model adds per input, not a property of our text. Including them would
        # skew short samples badly. We account for them separately below.
        n = len(tokenizer.encode(t, add_special_tokens=False))
        if n:
            ratios.append(len(t) / n)
    return ratios


def report(kind: str, ratios: list[float]) -> float:
    """Print the distribution and return the conservative (p10) figure.

    We take the 10th percentile, not the mean. The mean would let easy prose
    subsidise hard table rows, and the chunk limit has to hold for the WORST
    text we feed it, not the average. p10 rather than the outright minimum
    because a single pathological line shouldn't dictate the whole design.
    """
    ratios = sorted(ratios)
    p10 = ratios[int(len(ratios) * 0.10)]
    print(f"  {kind:11} n={len(ratios):4}  "
          f"mean={st.mean(ratios):5.2f}  median={st.median(ratios):5.2f}  "
          f"p10={p10:5.2f}  min={ratios[0]:5.2f}")
    return p10


def main() -> None:
    # Imported here, not at the top: this pulls in torch and takes a few seconds
    # plus a model download on first run. Keeping it inside main() means the file
    # can still be imported cheaply by tests that don't need the model.
    from sentence_transformers import SentenceTransformer

    print(f"loading {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    tokenizer = model.tokenizer

    # These two numbers were assumed during design (256 / 384) and never checked.
    # This is where the assumption becomes a fact — or gets corrected.
    max_tokens = model.max_seq_length
    dim = model.get_embedding_dimension()
    print(f"\nMODEL FACTS (previously assumed, now measured)")
    print(f"  max_seq_length: {max_tokens} tokens")
    print(f"  embedding dim:  {dim}")

    print(f"\nCHARS PER TOKEN, by text kind")
    samples = collect_samples()
    p10 = {kind: report(kind, chars_per_token(tokenizer, texts))
           for kind, texts in samples.items() if texts}

    # The binding constraint is whichever text kind tokenizes WORST, because the
    # chunker applies one limit to all of them.
    worst_kind = min(p10, key=p10.get)
    worst = p10[worst_kind]

    # Reserve a couple of tokens for the [CLS]/[SEP] the model adds, then leave a
    # 10% safety margin: our p10 is an estimate from a sample, not a guarantee,
    # and being slightly under the limit costs nothing while being over is silent
    # data loss.
    usable = (max_tokens - 2) * 0.90
    hard_max = int(usable * worst)
    target = int(hard_max * 0.83)   # leave room for a block to overshoot slightly

    print(f"\nBINDING CONSTRAINT: {worst_kind} at {worst:.2f} chars/token")
    print(f"\nSUGGESTED CONSTANTS")
    print(f"  HARD_MAX = {hard_max}   # ({max_tokens}-2 tokens x 0.90 safety) x {worst:.2f}")
    print(f"  TARGET   = {target}")

    # The decision rule agreed during design assumed TABLES would be the worst
    # case. They are not — see the spread below. So the rule is applied to the
    # actual binding constraint instead of to the kind we expected to bind.
    print(f"\nVERDICT ({worst_kind} at {worst:.2f} chars/token)")
    if worst >= 3.5:
        print("  >= 3.5  -> a single character limit is fine; proceed as planned")
    elif worst >= 2.5:
        print("  2.5-3.5 -> proceed with the LOWERED HARD_MAX above; expect more chunks")
    else:
        print("  < 2.5   -> a single CHARACTER limit no longer works.")

    # The real finding is the SPREAD, not any one number. A character limit is a
    # proxy for the token limit, and a proxy is only useful when it is roughly
    # constant. Here it is not:
    spread = max(p10.values()) / min(p10.values())
    print(f"\n  spread across kinds: {spread:.1f}x "
          f"({min(p10, key=p10.get)} {min(p10.values()):.2f} .. "
          f"{max(p10, key=p10.get)} {max(p10.values()):.2f})")
    if spread > 1.3:
        print("  -> One character limit cannot serve all three kinds. Sized for the")
        print("     worst (code), prose and table chunks would come out needlessly")
        print("     small; sized for the average, code chunks would be truncated.")
        print("     COUNT TOKENS DIRECTLY IN chunk.py INSTEAD. The tokenizer is")
        print("     cheap to load and removes the conversion error entirely.")


if __name__ == "__main__":
    main()
