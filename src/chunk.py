"""Split the frozen corpus into chunks.

Run:  .venv/bin/python src/chunk.py
      .venv/bin/python src/chunk.py --inspect 10

TWO TEXTS PER CHUNK
-------------------
Every chunk carries two versions of itself:

  text_raw    a byte-exact slice of corpus/doc-NN.md
  text_embed  the rendered version that goes to the model

This is the single most important decision in the file. Gold labels on Days 3-5
point at `text_raw`, so a bug in the RENDERING can make retrieval worse but can
never corrupt the labels. It turns the whole transformation pipeline from a
permanent bet into a knob we can still turn on Day 9.

THE PARTITION INVARIANT
-----------------------
The chunks of a document TILE it: their raw slices are contiguous, non-
overlapping, and cover every byte. So:

    "".join(c.text_raw for c in chunks_of(doc)) == doc_file_contents

exactly, byte for byte. This is asserted on every run. It is a much stronger
guarantee than "we didn't seem to lose anything", and it is what makes silent
data loss - the worst chunker bug, because nothing looks wrong - impossible
rather than merely unlikely.

Note that whitespace, table header rows, and |---| separators all still belong
to some chunk's text_raw even though they contribute nothing to text_embed.
That is exactly why the invariant can be exact instead of approximate.

WHY TOKENS, NOT CHARACTERS
--------------------------
src/tokens.py measured this corpus: code runs 2.20 chars/token, tables 3.54.
A 1.6x spread means no single character limit works - sized for code, tables get
needlessly chopped; sized for tables, code silently truncates at the model's
256-token ceiling. So we count tokens directly and the conversion error simply
stops existing.
"""

import argparse
import hashlib
import json
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import mdx
import tables
from fetch_corpus import CORPUS_DIR, PAGES

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# The model reads at most 256 tokens and wraps every input in [CLS] ... [SEP],
# leaving 254 for our text. Exceeding this is not an error - the surplus is
# silently discarded - which is why it is enforced here instead of hoped for.
TOKEN_LIMIT = 254

INDEX_DIR = Path(__file__).resolve().parent.parent / "index"
NOTES_DIR = Path(__file__).resolve().parent.parent / "notes"

_tokenizer = None


def tokenizer():
    """Load the tokenizer once, lazily.

    This is the `tokenizers` library turning text into integers - it does not
    load model weights and does not run torch, so it is cheap. Lazy because the
    tests for chunk boundaries do not all need it.
    """
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    return _tokenizer


def n_tokens(text: str) -> int:
    if not text.strip():
        return 0
    return len(tokenizer().encode(text, add_special_tokens=False))


# ------------------------------------------------------------------- UNITS --

@dataclass
class Unit:
    """One indivisible piece of the document.

    `start`/`end` are offsets into the RAW file. Units are built so that they
    tile the document, which is what lets the partition invariant hold.
    `rendered` may be empty (header rows, blank lines) - such a unit still owns
    its raw bytes, it just contributes nothing to the embedded text.
    """
    start: int
    end: int
    rendered: str
    kind: str
    tokens: int = field(default=0)
    # Separator to place BEFORE this unit when joining it to the previous one.
    # Whole blocks are separate thoughts and get a blank line. Pieces produced by
    # splitting an oversized block are continuations of one another and already
    # carry their own newlines, so they get nothing - otherwise a split code
    # fence comes out double-spaced, with every blank line costing real tokens.
    glue: str = "\n\n"


def _fence_spans(text: str) -> list[tuple[int, int]]:
    """Character spans of fenced code blocks, including their closing line.

    Found FIRST, before any blank-line splitting: 18% of the fences in this
    corpus contain a blank line, and splitting first would tear them apart and
    misclassify the pieces as prose.
    """
    marks = [m.start() for m in re.finditer(r"^```", text, re.M)]
    spans = []
    for i in range(0, len(marks) - 1, 2):
        close = marks[i + 1]
        line_end = text.find("\n", close)
        line_end = len(text) if line_end == -1 else line_end + 1
        spans.append((marks[i], line_end))
    return spans


def _line_spans(text: str, offset: int) -> list[tuple[int, int]]:
    """Every line of `text` as (start, end) offsets, keeping its newline.

    Lines are the fallback unit for anything too big to embed whole. Because
    they tile their parent exactly, splitting into lines never breaks the
    partition invariant.
    """
    spans, pos = [], 0
    for line in text.splitlines(keepends=True):
        spans.append((offset + pos, offset + pos + len(line)))
        pos += len(line)
    return spans


def build_units(text: str) -> list[Unit]:
    """Break one document into units that tile it exactly."""
    units: list[Unit] = []
    fences = _fence_spans(text)
    pos = 0

    def add_prose_or_tables(chunk_start: int, chunk_end: int) -> None:
        """Handle the non-fenced stretch between two code fences."""
        segment = text[chunk_start:chunk_end]
        # Split on blank lines but KEEP the separators, so the pieces still
        # tile the segment. re.split with a capturing group returns the
        # delimiters alongside the content.
        parts = re.split(r"(\n\s*\n)", segment)
        cursor = chunk_start
        for part in parts:
            if not part:
                continue
            start, end = cursor, cursor + len(part)
            cursor = end

            if not part.strip():
                # Blank run: owns its bytes, renders to nothing.
                units.append(Unit(start, end, "", "whitespace"))
            elif tables.is_table_block(part):
                units.extend(_table_units(part, start))
            else:
                units.append(Unit(start, end, mdx.transform(part), "prose"))

    for fence_start, fence_end in fences:
        if fence_start > pos:
            add_prose_or_tables(pos, fence_start)
        # A fence is embedded verbatim - it is already the plain text a user
        # would search for, and mdx.transform deliberately never touches it.
        units.append(Unit(fence_start, fence_end, text[fence_start:fence_end], "code"))
        pos = fence_end

    if pos < len(text):
        add_prose_or_tables(pos, len(text))

    return units


def _table_units(block: str, offset: int) -> list[Unit]:
    """One unit per table line, rendering data rows and blanking the scaffolding.

    Rendering happens HERE, at the table level, because a row needs its header
    to know what its cells are called. Doing it later - once rows had been
    split across chunks - would leave the second chunk's rows unlabelled.
    """
    out: list[Unit] = []
    lines = block.splitlines(keepends=True)
    if not lines:
        return out

    headers = tables.split_cells(lines[0])
    cursor = offset

    for i, line in enumerate(lines):
        start, end = cursor, cursor + len(line)
        cursor = end
        stripped = line.strip()

        # The header row and the |---| separator carry no information once every
        # data row labels itself. They keep their raw bytes and render to "".
        if i == 0 or tables.is_separator(stripped) or not stripped:
            out.append(Unit(start, end, "", "table_scaffold"))
            continue

        rendered = tables.render_row(headers, tables.split_cells(stripped))
        out.append(Unit(start, end, rendered, "table_row"))

    return out


def split_oversized(unit: Unit, text: str) -> list[Unit]:
    """Break a unit whose rendered form exceeds the token limit.

    Measured: 67 of 7,170 units (under 1%) need this. Two levels of fallback,
    both of which preserve the partition because they cut at offsets:

      1. Split into lines and re-render each.
      2. If one line is STILL too big, cut it at character offsets.

    Level 2 costs a little quality - a table row cut in half loses its labels,
    which affects 4 rows in the whole corpus - but it never loses content, and
    content loss is the failure that cannot be recovered from.
    """
    pieces = _line_spans(text[unit.start:unit.end], unit.start)
    if len(pieces) > 1:
        out = []
        for start, end in pieces:
            raw = text[start:end]
            rendered = raw if unit.kind == "code" else mdx.transform(raw)
            # glue="" — these lines keep their own trailing newline, so joining
            # them with nothing reproduces the original block exactly.
            sub = Unit(start, end, rendered, unit.kind, glue="")
            sub.tokens = n_tokens(sub.rendered)
            out.extend(split_oversized(sub, text) if sub.tokens > TOKEN_LIMIT else [sub])
        # The first piece inherits the parent's separator: it still follows
        # whatever block came before, and only the CONTINUATIONS are seamless.
        if out:
            out[0].glue = unit.glue
        return out

    # A single line too long for the model. Cut on character count, using the
    # measured worst-case density (2.20 chars/token) so a piece cannot overshoot.
    out, start = [], unit.start
    step = int(TOKEN_LIMIT * 2.0)
    while start < unit.end:
        end = min(start + step, unit.end)
        raw = text[start:end]
        # Unstripped, glue="" — the pieces concatenate back into the line.
        piece = Unit(start, end, raw, unit.kind, glue="")
        piece.tokens = n_tokens(piece.rendered)
        out.append(piece)
        start = end
    if out:
        out[0].glue = unit.glue
    return out


# ----------------------------------------------------------------- PACKING --

@dataclass
class Chunk:
    doc_id: str
    slug: str
    index: int
    start: int
    end: int
    text_raw: str
    text_embed: str
    block_type: str
    tokens: int

    @property
    def id(self) -> str:
        # Three digits, not two: doc-07 produces hundreds of chunks, and
        # zero-padding keeps IDs sorting correctly when grepped by hand.
        return f"{self.doc_id}:c{self.index:03d}"


def pack(units: list[Unit], doc_id: str, slug: str, text: str) -> list[Chunk]:
    """Greedily fill chunks up to the token limit.

    A chunk is flushed when adding the next unit would overflow. Whitespace and
    table scaffolding cost zero tokens, so they ride along with whatever chunk
    they fall inside - keeping the raw slices contiguous at no cost.
    """
    chunks: list[Chunk] = []
    buf: list[Unit] = []
    buf_tokens = 0

    def flush() -> None:
        nonlocal buf, buf_tokens
        if not buf:
            return
        start, end = buf[0].start, buf[-1].end
        # Each unit brings its own separator, so a split block reads as one
        # continuous piece while distinct blocks stay visually separated.
        # Keep blank-line units that belong to a SPLIT block (glue == ""), or an
        # oversized code fence comes back with its internal blank lines deleted.
        # Whitespace units BETWEEN blocks still get dropped - their separation is
        # already expressed by the "\n\n" glue.
        parts = [u for u in buf if u.rendered.strip() or u.glue == ""]
        rendered = "".join((u.glue if i else "") + u.rendered
                           for i, u in enumerate(parts)).strip()
        # A unit that already ends in a newline plus a "\n\n" separator yields
        # three. Collapse any such run to a single blank line. Safe to do here
        # because this is text_embed - text_raw stays byte-exact, so nothing a
        # gold label points at is affected.
        rendered = re.sub(r"\n{3,}", "\n\n", rendered)
        # Prefer the kind that contributed the most tokens - it's what the chunk
        # mostly IS, which is what --inspect and the per-type stats care about.
        kinds = [u.kind for u in buf if u.rendered.strip()]
        block_type = max(set(kinds), key=kinds.count) if kinds else "whitespace"
        chunks.append(Chunk(
            doc_id=doc_id, slug=slug, index=len(chunks),
            start=start, end=end,
            text_raw=text[start:end], text_embed=rendered,
            block_type=block_type,
            # Recount exactly: per-unit counts are summed while packing, and
            # tokenization is not perfectly additive across joins.
            tokens=n_tokens(rendered),
        ))
        buf, buf_tokens = [], 0

    for unit in units:
        if unit.tokens > TOKEN_LIMIT:
            raise AssertionError(f"unit not split: {unit.kind} {unit.tokens} tokens")

        # An empty-rendering unit can always join - it costs nothing.
        if unit.tokens == 0:
            buf.append(unit)
            continue

        if buf_tokens + unit.tokens > TOKEN_LIMIT and any(u.rendered.strip() for u in buf):
            flush()

        buf.append(unit)
        buf_tokens += unit.tokens

    flush()
    return chunks


def chunk_document(path: Path, doc_id: str, slug: str) -> list[Chunk]:
    text = path.read_text(encoding="utf-8")

    units = []
    for unit in build_units(text):
        unit.tokens = n_tokens(unit.rendered)
        units.extend(split_oversized(unit, text) if unit.tokens > TOKEN_LIMIT else [unit])

    chunks = pack(units, doc_id, slug, text)

    # THE INVARIANT. Not a warning, not a log line - the run stops.
    rebuilt = "".join(c.text_raw for c in chunks)
    if rebuilt != text:
        raise AssertionError(
            f"{doc_id}: chunks do not reconstruct the document "
            f"({len(rebuilt):,} chars vs {len(text):,})"
        )
    for c in chunks:
        if c.tokens > TOKEN_LIMIT:
            raise AssertionError(f"{c.id}: {c.tokens} tokens exceeds {TOKEN_LIMIT}")

    return chunks


# ------------------------------------------------------------------ OUTPUT --

def record(c: Chunk) -> dict:
    raw_bytes = c.text_raw.encode("utf-8")
    # Two hashes, two jobs. `sha256` is exact and detects re-chunk drift, so any
    # normalisation would hide a real change. `sha256_norm` collapses whitespace
    # and case to group duplicate chunks across docs, where exactness would miss
    # rows differing only by table padding.
    norm = re.sub(r"\s+", " ", c.text_raw).strip().lower().encode("utf-8")
    return {
        "id": c.id,
        "doc_id": c.doc_id,
        "slug": c.slug,
        "text_raw": c.text_raw,
        "text_embed": c.text_embed,
        "char_start": c.start,
        "char_end": c.end,
        "chars_raw": len(c.text_raw),
        "tokens_embed": c.tokens,
        "block_type": c.block_type,
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "sha256_norm": hashlib.sha256(norm).hexdigest(),
    }


def build_all() -> list[Chunk]:
    all_chunks = []
    for i, (_, slug) in enumerate(PAGES, start=1):
        doc_id = f"doc-{i:02d}"
        chunks = chunk_document(CORPUS_DIR / f"{doc_id}.md", doc_id, slug)
        all_chunks.extend(chunks)
        print(f"  {doc_id}  {slug:32} {len(chunks):>4} chunks")
    return all_chunks


def write_jsonl(chunks: list[Chunk]) -> Path:
    INDEX_DIR.mkdir(exist_ok=True)
    path = INDEX_DIR / "chunks.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for c in chunks:
            fh.write(json.dumps(record(c), ensure_ascii=False) + "\n")
    return path


def inspect(chunks: list[Chunk], n: int) -> str:
    """A STRATIFIED sample, not a random one.

    Random sampling from a corpus that is 40% tables could easily hand back ten
    prose chunks and tell you nothing about the case most likely to be wrong.
    Sampling the failure modes is worth far more for the same ten minutes.
    """
    rng = random.Random(0)          # seeded: the same sample every run
    buckets: dict[str, list[Chunk]] = {}
    for c in chunks:
        buckets.setdefault(c.block_type, []).append(c)

    picks: list[tuple[str, Chunk]] = []
    for kind, items in sorted(buckets.items()):
        picks.append((f"block_type={kind}", rng.choice(items)))

    for slug in ("settings", "checkpointing"):
        matching = [c for c in chunks if c.slug == slug]
        if matching:
            picks.append((f"largest/smallest doc: {slug}", rng.choice(matching)))
    # Search text_RAW for the source tags. Looking for "\n1. " in text_embed
    # would also match ordinary markdown ordered lists, which is how the first
    # version of this sampled a plain list and labelled it a <Steps> block.
    # text_raw is verbatim source, so the original tag is an exact marker.
    for marker, label in (("<Tab", "<Tabs> region"), ("<Step", "<Steps> region")):
        matching = [c for c in chunks if marker in c.text_raw]
        if matching:
            picks.append((label, rng.choice(matching)))

    picks = picks[:n]
    out = [
        "# Chunk inspection",
        "",
        f"Stratified sample of {len(picks)} chunks from {len(chunks):,}.",
        "Read this BEFORE writing gold labels - after Day 4 the chunk IDs are frozen.",
        "",
        "For each: `text_raw` is what you label against, `text_embed` is what the",
        "model actually sees.",
        "",
    ]
    for reason, c in picks:
        out += [
            "---", "",
            f"## `{c.id}` — {reason}",
            f"`{c.slug}` · {c.block_type} · {c.tokens} tokens · "
            f"chars {c.start:,}–{c.end:,}",
            "", "**text_raw**", "```", c.text_raw[:900].rstrip(), "```",
            "", "**text_embed**", "```", c.text_embed[:900].rstrip(), "```", "",
        ]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", type=int, metavar="N",
                        help="print a stratified sample of N chunks and write notes/")
    args = parser.parse_args()

    print(f"chunking {len(PAGES)} docs (limit {TOKEN_LIMIT} tokens)...")
    chunks = build_all()

    path = write_jsonl(chunks)
    total_tokens = sum(c.tokens for c in chunks)
    print(f"\n{len(chunks):,} chunks -> {path}")
    print(f"tokens: {total_tokens:,} total, "
          f"{total_tokens / len(chunks):.0f} mean per chunk")

    by_type: dict[str, int] = {}
    for c in chunks:
        by_type[c.block_type] = by_type.get(c.block_type, 0) + 1
    print("by block type: " + ", ".join(f"{k}={v:,}" for k, v in sorted(by_type.items())))

    # D3: the top docs dominate, so surface it rather than leaving it to be
    # rediscovered when a metric looks odd on Day 8.
    per_doc: dict[str, int] = {}
    for c in chunks:
        per_doc[c.doc_id] = per_doc.get(c.doc_id, 0) + 1
    top = sorted(per_doc.items(), key=lambda kv: -kv[1])[:3]
    share = 100 * sum(v for _, v in top) / len(chunks)
    print(f"top 3 docs = {share:.0f}% of chunks: " +
          ", ".join(f"{k}({v:,})" for k, v in top))

    if args.inspect:
        NOTES_DIR.mkdir(exist_ok=True)
        report = inspect(chunks, args.inspect)
        (NOTES_DIR / "chunk-inspection.md").write_text(report, encoding="utf-8")
        print(f"\nwrote {NOTES_DIR / 'chunk-inspection.md'}")
        print(report[:1500])


if __name__ == "__main__":
    sys.exit(main())
