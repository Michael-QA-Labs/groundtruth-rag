"""Concatenate the frozen corpus into one greppable file.

Run:  python build_combined.py   (after fetch_corpus.py)

Writes corpus/combined.md — every page in one file, each preceded by a
`@@PAGE nn/30 :: slug` marker, with a lookup table at the top.

Why this exists: on Days 3-5 you hand-label gold chunks, and `grep -n` across
one file is far faster than opening 30. This is a DERIVED file — corpus/doc-NN.md
are the source of truth. Rebuild it any time; never edit it by hand.

Note the filename: `combined.md`, not `index.md`. macOS filesystems are
case-INsensitive by default, so `corpus/index.md` and `corpus/INDEX.md` are the
same path and would silently overwrite each other.
"""

from pathlib import Path

from fetch_corpus import CORPUS_DIR, PAGES


def page_title(text: str) -> str:
    """Pull the first `# ` heading out of a markdown document."""
    # Walk lines until we hit a top-level heading. We don't just take line 1 —
    # some pages open with frontmatter or a blank line before the title.
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()

    # No heading found. Return a placeholder rather than raising: a missing
    # title is a cosmetic problem in a lookup table, not a reason to kill the
    # build. It'll be visible in the output if you care.
    return "(untitled)"


def main() -> None:
    # 1. Load every page, in PAGES order, so numbering matches doc-NN and the
    #    row order the D1 hash was computed over.
    docs = []
    for i, (base, slug) in enumerate(PAGES, start=1):
        text = (CORPUS_DIR / f"doc-{i:02d}.md").read_text(encoding="utf-8")
        docs.append({
            "n": i,
            "slug": slug,
            "url": f"{base}/{slug}.md",
            "chars": len(text),
            "title": page_title(text),
            "text": text,
        })

    # 2. Build the body first, recording which line each page starts on.
    #    Chicken-and-egg: the table wants line numbers, but the table itself
    #    occupies lines and shifts everything down. Solved by building the body
    #    with body-relative offsets now, then adding the header's height once
    #    it's known. The alternative — guessing the header height — breaks the
    #    moment you add a row.
    #    `body` must hold exactly ONE LINE PER ELEMENT for len(body) to be a
    #    usable line number. Appending a whole document as a single element
    #    looks like it works — it joins into the right text — but then
    #    len(body) counts documents, not lines, and every page after the first
    #    gets a line number that's short by however many lines preceded it.
    #    Hence .splitlines() and extend() rather than a bare append.
    body = []
    for doc in docs:
        body.append("")
        doc["body_line"] = len(body) + 1      # the marker goes on the next line
        body.append(f"@@PAGE {doc['n']:02d}/{len(docs)} :: {doc['slug']}")
        body.append("")
        body.extend(doc["text"].rstrip("\n").splitlines())

    # 3. Build the header. Its height is fixed by the row count, so we can
    #    assemble it with placeholder line numbers, measure it, then fill in
    #    the real values.
    total_chars = sum(doc["chars"] for doc in docs)
    header = [
        f"# Claude Code docs — combined corpus ({len(docs)} pages)",
        "",
        "DERIVED FILE — rebuild with `python build_combined.py`. Source of truth",
        "is `corpus/doc-NN.md`. Frozen snapshot: see `corpus/INDEX.md` for the hash.",
        "",
        "Search: `grep -n 'term' corpus/combined.md`",
        "List pages: `grep -nE '^@@PAGE' corpus/combined.md`",
        "",
        f"{total_chars:,} chars total.",
        "",
        "| # | ID | Line | Slug | Chars | Title | Link |",
        "|---|---|---:|---|---:|---|---|",
    ]
    header += [""] * len(docs)   # placeholder rows, so len(header) is final
    header += ["", ""]
    offset = len(header)

    # 4. Now that the header height is known, write the real rows into their
    #    placeholder slots. Row i lives at index (12 + i) — index 12 is the
    #    first slot after the two table-formatting lines above.
    for i, doc in enumerate(docs):
        header[12 + i] = (
            f"| {doc['n']} | doc-{doc['n']:02d} | {doc['body_line'] + offset} "
            f"| `{doc['slug']}` | {doc['chars']:,} | {doc['title']} "
            f"| [🔗]({doc['url']}) |"
        )

    out = CORPUS_DIR / "combined.md"
    out.write_text("\n".join(header + body) + "\n", encoding="utf-8")

    # 5. Verify the line numbers are actually right rather than asserting it.
    #    An off-by-one here silently sends you to the wrong page for the rest of
    #    the project, so it's worth the six lines to check.
    written = out.read_text(encoding="utf-8").splitlines()
    bad = [
        doc["slug"] for doc in docs
        if written[doc["body_line"] + offset - 1]
        != f"@@PAGE {doc['n']:02d}/{len(docs)} :: {doc['slug']}"
    ]
    if bad:
        raise SystemExit(f"line numbers wrong for: {bad}")

    print(f"wrote {out}  ({len(written):,} lines, {total_chars:,} chars)")
    print(f"verified all {len(docs)} page line numbers")


if __name__ == "__main__":
    main()
