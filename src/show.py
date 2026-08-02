"""Read chunks by ID, by document, or by the text they contain.

Run:  .venv/bin/python src/show.py doc-10:c005      one chunk, full text_raw
      .venv/bin/python src/show.py doc-10           every chunk in a doc
      .venv/bin/python src/show.py --find acceptEdits    which chunks contain it

WHY THIS EXISTS
---------------
Day 4 labels gold chunks, and the gold-set rule is "label against text_raw,
never text_embed" - a rendering bug should be able to degrade retrieval without
being able to corrupt a label. But search.py --show-text prints text_embed. So
before this file there was no way to obey that rule.

WHY IT DOESN'T IMPORT THE MODEL
-------------------------------
search.py loads sentence-transformers, which costs several seconds of torch
import before it can answer anything. Nothing here needs a vector: these are
lookups by ID and substring over a 3.8 MB JSONL file. Keeping the model out
makes this fast enough to run in a loop while labeling, which is the only way it
gets used 25 times instead of twice.

WHY --find MATTERS MORE THAN IT LOOKS
-------------------------------------
Gold labels must be found INDEPENDENTLY of the retriever being graded. If you
pick gold from search.py's top 10, then every gold chunk is inside the top 10 by
construction and Day 8's recall@10 is 1.0 before you run it - you'd be scoring
the retriever against its own output.

--find is the independent path: grep the corpus for a term you know the answer
uses, then map that text to a chunk ID without the embeddings ever voting.
"""

import argparse
import json
import sys

from chunk import INDEX_DIR


def load_chunks() -> list[dict]:
    """Every chunk record, in index order."""
    path = INDEX_DIR / "chunks.jsonl"
    if not path.exists():
        sys.exit(f"{path} not found - run src/chunk.py first")

    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def show_one(chunk: dict) -> None:
    """Print a single chunk in full."""
    print("=" * 78)
    print(f"{chunk['id']}  |  {chunk['slug']}  |  {chunk['block_type']}  |  "
          f"{chunk['tokens_embed']} tok  |  chars {chunk['char_start']}-{chunk['char_end']}")
    print("=" * 78)
    # text_raw, deliberately. See the module docstring.
    print(chunk["text_raw"])
    print()


def show_doc(chunks: list[dict], doc_id: str) -> None:
    """List every chunk in one document, one line each.

    This is the view for "I know the answer is on the permissions page, which
    chunk is it in?" - the first line of each chunk is usually a heading or the
    start of a sentence, which is enough to navigate by.
    """
    hits = [c for c in chunks if c["doc_id"] == doc_id]
    if not hits:
        sys.exit(f"no chunks for {doc_id} - IDs look like doc-01 .. doc-30")

    print(f"{doc_id}  ({hits[0]['slug']})  -  {len(hits)} chunks\n")
    for c in hits:
        first_line = c["text_raw"].strip().split("\n")[0]
        if len(first_line) > 84:
            first_line = first_line[:84] + " ..."
        print(f"  {c['id']:16} {c['block_type']:11} {c['tokens_embed']:>4}tok  {first_line}")


def find(chunks: list[dict], needle: str) -> None:
    """Print every chunk whose text_raw contains `needle`, with context.

    Case-insensitive, because you're searching for a concept you half-remember,
    not running an exact-match test.
    """
    lowered = needle.lower()
    hits = [c for c in chunks if lowered in c["text_raw"].lower()]

    if not hits:
        print(f'no chunk contains "{needle}"')
        print("If you expected one, that absence is evidence - it is the kind "
              "of check an 'unanswerable' label needs.")
        return

    print(f'"{needle}" appears in {len(hits)} chunk(s)\n')
    for c in hits:
        # Show the text around the first occurrence, so you can judge whether
        # the chunk actually answers anything or merely mentions the word.
        i = c["text_raw"].lower().index(lowered)
        snippet = c["text_raw"][max(0, i - 100):i + 200].strip().replace("\n", " ")
        print(f"  {c['id']:16} {c['slug']:28} {c['block_type']}")
        print(f"      ...{snippet}...\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect chunks by ID, by doc, or by contained text.")
    parser.add_argument("target", nargs="?",
                        help="a chunk ID (doc-10:c005) or a doc ID (doc-10)")
    parser.add_argument("--find", metavar="TEXT",
                        help="print chunks whose text_raw contains TEXT")
    # Searching for a CLI flag is a normal thing to want ("--resume", "-p"), but
    # argparse sees the leading dash as the start of another option and dies with
    # "expected one argument". Rewrite `--find X` to `--find=X` first, which
    # argparse accepts verbatim whatever X looks like.
    argv = sys.argv[1:]
    if "--find" in argv:
        i = argv.index("--find")
        if i + 1 < len(argv):
            argv[i:i + 2] = [f"--find={argv[i + 1]}"]

    args = parser.parse_args(argv)

    if not args.target and not args.find:
        parser.error("give a chunk ID, a doc ID, or --find TEXT")

    chunks = load_chunks()

    if args.find:
        find(chunks, args.find)
        return

    # A colon is what separates the two lookup modes: doc-10 vs doc-10:c005.
    if ":" in args.target:
        by_id = {c["id"]: c for c in chunks}
        if args.target not in by_id:
            sys.exit(f"no chunk {args.target} - IDs look like doc-10:c005")
        show_one(by_id[args.target])
    else:
        show_doc(chunks, args.target)


if __name__ == "__main__":
    main()
