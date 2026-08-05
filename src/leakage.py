"""Find questions that share rare vocabulary with their own gold chunks.

Run:  .venv/bin/python src/leakage.py
      .venv/bin/python src/leakage.py --df-max 5      loosen what counts as rare
      .venv/bin/python src/leakage.py --show-all      include the clean ones

WHY THIS EXISTS
---------------
Day 5's one measurable task: "rewrite any question that shares 3+ rare words
with its own gold chunk". A question written while looking at the chunk borrows
that chunk's wording, and a retriever then finds it by lexical echo rather than
by understanding. The recall number that comes out is real arithmetic over a
rigged input, which is worse than no number, because it looks defensible.

This cannot be caught by re-reading. You wrote the question; its vocabulary
feels like yours either way. It needs counting.

WHAT "RARE" MEANS HERE, AND WHY
-------------------------------
A term is rare if it appears on N or fewer of the 30 corpus pages. Document
frequency, not chunk frequency, for two reasons:

1. It is interpretable at the scale you label at. "This word is on 2 of 30
   pages" is a sentence you can defend in an interview. "This word is in 14 of
   1,637 chunks" needs a paragraph of setup first.
2. Stopwords disappear without a stopword list. "the", "you", "run" and "claude"
   are on nearly every page, so they are never rare, so they never get counted
   as shared. A hand-written stopword list would be one more thing to justify.

WHY THE THRESHOLD SWEEPS INSTEAD OF SITTING AT ONE NUMBER
---------------------------------------------------------
No value of N is obviously correct, and a run that reports "0 flagged" at one
arbitrary N is indistinguishable from a broken check that can only ever return
zero. That distinction is the entire value of the output, so the sweep is not
optional detail: it shows how far N has to move before the answer changes.

The first run of this file returned 0 at N=3 and the number was junk. 55% of
this corpus's vocabulary sits at 3 pages or fewer, but that tail is code
identifiers and one-off strings, not words anyone types into a question. The
product vocabulary a question could actually borrow ("rewind" on 7 pages,
"checkpoint" on 6, "statusline" on 4) sits well above it, because these pages
cross-reference each other constantly. A single-threshold answer would have
hidden that.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It does not decide anything. Q02 is "how do i import a plugin" and its gold
chunk is about installing plugins - of course they share the word. That is the
question's subject, not borrowed phrasing. The output is a shortlist to read,
and the reading is the Day 5 work. A script that returned a verdict here would
let you skip the re-read, which is the part that has value.

It also does not look at text_embed. Same rule as the labeling itself: judge
against text_raw, the bytes the page actually had.
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

from show import load_chunks

GOLD_FILE = Path(__file__).resolve().parent.parent / "gold" / "gold-set-template.md"

# Below this length a token is almost never a real term ("i", "a", "of"), and
# the ones that are ("mcp", "cli", "api") are 3 characters, so 3 is the floor.
MIN_TOKEN_LEN = 3


# ------------------------------------------------------------- tokenisation --

def tokenise(text: str) -> list[str]:
    """Lowercase, then split on anything that is not a letter or digit.

    Splitting on non-alphanumerics rather than on whitespace is the decision
    that makes this work at all. The corpus writes `claude-code`, `--resume`,
    `settings.json` and `acceptEdits`; you type "claude code", "resume",
    "settings json". Tokenising both sides the same crude way is what lets those
    meet. Keep the split on one side only and the check reports zero leaks
    because the vocabularies can never touch.

    Pure digits are dropped: sharing "5" with a chunk is not evidence of
    anything.
    """
    raw = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in raw if len(t) >= MIN_TOKEN_LEN and not t.isdigit()]


def build_vocabulary(chunks: list[dict]) -> set[str]:
    """Every token the corpus contains, before any folding.

    Needed before normalise() can run, because the plural rule below asks
    "is the singular a real word in THIS corpus?" rather than trusting a
    general-purpose stemmer to know that `acceptEdits` is not a plural.
    """
    vocab: set[str] = set()
    for c in chunks:
        vocab.update(tokenise(c["text_raw"]))
    return vocab


def normalise(token: str, vocab: set[str]) -> str:
    """Fold a plural onto its singular, but only when the singular exists.

    Copying "hooks" off the page and typing "hook" is still copying, so the two
    have to count as one term. A full stemmer would go further and start folding
    things that are not related ("permissions" and "permit"), which would invent
    leaks that are not there. The corpus-membership test is the brake: `hooks`
    folds because `hook` is on the page too, `across` does not because `acros`
    is not a word here.
    """
    if token.endswith("s") and len(token) > MIN_TOKEN_LEN:
        singular = token[:-1]
        if singular in vocab:
            return singular
    return token


def normalised_tokens(text: str, vocab: set[str]) -> list[str]:
    return [normalise(t, vocab) for t in tokenise(text)]


# --------------------------------------------------------- document frequency --

def document_frequency(chunks: list[dict], vocab: set[str]) -> dict[str, int]:
    """For each term, how many of the 30 pages contain it.

    Counted over text_raw, per doc_id, so a term repeated 40 times on one page
    still scores 1. Frequency within a page is not the signal; spread across the
    corpus is. A term on one page is distinctive to that page, and finding it in
    a question about that page is what this whole file is looking for.
    """
    docs_with: dict[str, set[str]] = defaultdict(set)
    for c in chunks:
        for term in set(normalised_tokens(c["text_raw"], vocab)):
            docs_with[term].add(c["doc_id"])
    return {term: len(docs) for term, docs in docs_with.items()}


# ------------------------------------------------------------- the gold set --

def parse_gold(path: Path) -> list[dict]:
    """Pull question text, answerability and gold chunk IDs out of the markdown.

    The gold set lives in markdown because it is written by hand and read by a
    human reviewer, and neither of those is easier in JSON. That leaves parsing
    it here. The format is regular enough for a regex: every entry opens with
    `## QNN` and its fields are single lines starting `**Field:**`.

    The worked example is skipped by construction - it lives under
    `## Worked example`, not `## QNN`, so the section regex never sees it. It is
    reference material, not one of the 30, and counting it would put 31
    questions into a 30-question tally.
    """
    text = path.read_text(encoding="utf-8")

    # Split on the QNN headings, keeping the heading with the body that follows.
    sections = re.split(r"^## (Q\d+)\s*$", text, flags=re.M)[1:]

    entries = []
    for qid, body in zip(sections[0::2], sections[1::2]):
        question = re.search(r"^\*\*Question:\*\*(.*)$", body, re.M)
        answerable = re.search(r"^\*\*Answerable:\*\*\s*(\w+)", body, re.M)
        gold_line = re.search(r"^\*\*Gold chunks:\*\*(.*)$", body, re.M)

        if not (question and answerable):
            sys.exit(f"{qid}: missing Question or Answerable field")

        entries.append({
            "id": qid,
            "question": question.group(1).strip(),
            "answerable": answerable.group(1).strip().lower() == "yes",
            # Chunk IDs are written in backticks: `doc-02:c005`, `doc-10:c005`.
            "gold_chunks": re.findall(r"`(doc-\d+:c\d+)`", gold_line.group(1)) if gold_line else [],
        })
    return entries


# ------------------------------------------------------------------ the check --

def shared_rare_terms(question: str, gold_text: str, df: dict[str, int],
                      vocab: set[str], df_max: int) -> list[tuple[str, int]]:
    """Rare terms present in both the question and its own gold chunks.

    Set intersection, not a count of occurrences: saying "hook" four times in
    one question is one borrowed word, not four. Returned rarest-first, because
    a term on 1 page of 30 is far more incriminating than one on 3, and you want
    to read those first.
    """
    q_terms = set(normalised_tokens(question, vocab))
    g_terms = set(normalised_tokens(gold_text, vocab))

    shared = [(t, df.get(t, 0)) for t in q_terms & g_terms if df.get(t, 0) <= df_max]
    return sorted(shared, key=lambda pair: (pair[1], pair[0]))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flag questions that share rare vocabulary with their gold chunks.")
    parser.add_argument("--df-max", type=int, default=3,
                        help="a term is rare if it appears on this many pages or fewer "
                             "(default: 3 of 30)")
    parser.add_argument("--flag-at", type=int, default=3,
                        help="how many shared rare terms make a question suspect "
                             "(default: 3, the Day 5 rule)")
    parser.add_argument("--show-all", action="store_true",
                        help="also print questions below the flag threshold")
    args = parser.parse_args()

    chunks = load_chunks()
    by_id = {c["id"]: c for c in chunks}
    n_docs = len({c["doc_id"] for c in chunks})

    vocab = build_vocabulary(chunks)
    df = document_frequency(chunks, vocab)
    entries = parse_gold(GOLD_FILE)

    # Unanswerable questions have no gold chunks, so there is nothing to leak
    # from. They are excluded here rather than scoring 0, which would quietly
    # improve the average by adding six guaranteed passes.
    answerable = [e for e in entries if e["answerable"]]

    print(f"{len(entries)} questions, {len(answerable)} answerable, "
          f"{n_docs} pages, {len(vocab):,} distinct terms")
    print(f'rare = on {args.df_max} or fewer of {n_docs} pages · '
          f'flagged at {args.flag_at}+ shared rare terms\n')

    # Every shared term with its page count, computed once at df_max = n_docs so
    # nothing is thrown away. Applying a threshold is then just a filter, which
    # is what lets the sweep below cost nothing.
    results = []
    for e in answerable:
        missing = [cid for cid in e["gold_chunks"] if cid not in by_id]
        if missing:
            sys.exit(f"{e['id']}: gold chunk(s) not in the index: {', '.join(missing)}")

        gold_text = "\n".join(by_id[cid]["text_raw"] for cid in e["gold_chunks"])
        results.append((e, shared_rare_terms(e["question"], gold_text, df, vocab, n_docs)))

    # Rarest shared term first. Sorting by count would put a question sharing
    # five ubiquitous words above one sharing a single term unique to its own
    # gold chunk, and the second is the actual leak.
    results.sort(key=lambda r: (r[1][0][1] if r[1] else n_docs + 1, -len(r[1])))

    flagged = 0
    for e, shared in results:
        rare = [(t, n) for t, n in shared if n <= args.df_max]
        if len(rare) >= args.flag_at:
            flagged += 1
            marker = "FLAG"
        elif not args.show_all:
            continue
        else:
            marker = "    "

        # Below the threshold the rare list is empty, so print what the question
        # DOES share. Seeing "undo(6), rewind(7)" is what tells you the check
        # looked at real words and found them innocent.
        shown = rare or shared[:5]
        terms = ", ".join(f"{t} ({n}p)" for t, n in shown) or "-"
        print(f"{marker} {e['id']}  {len(rare)} rare / {len(shared)} shared")
        print(f"       {e['question']}")
        print(f"       {terms}\n")

    print(f"{flagged} of {len(answerable)} answerable questions share "
          f"{args.flag_at}+ terms rarer than {args.df_max} pages "
          f"with their own gold chunks.\n")

    # --- sensitivity ---------------------------------------------------------
    # How far does the definition of "rare" have to move before the verdict
    # changes? If the answer is "not far", the verdict was the threshold's, not
    # the gold set's.
    print(f"Sensitivity: questions flagged at {args.flag_at}+ shared terms, "
          f"by what counts as rare")
    previous = None
    for cutoff in range(1, n_docs + 1):
        n_flagged = sum(1 for _, shared in results
                        if sum(1 for _, n in shared if n <= cutoff) >= args.flag_at)
        # One line per change, not 30 lines of the same number.
        if n_flagged != previous:
            first = next((e["id"] for e, shared in results
                          if sum(1 for _, n in shared if n <= cutoff) >= args.flag_at), "-")
            print(f"  rare = <= {cutoff:2d} of {n_docs} pages : {n_flagged:2d} flagged"
                  f"   (first: {first})")
            previous = n_flagged

    if flagged:
        print("\nRead each flag against its gold chunk before rewriting. A question "
              "that must name its own subject is not a leak.")


if __name__ == "__main__":
    main()
