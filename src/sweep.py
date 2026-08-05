"""Find chunks that restate a gold answer but were never labeled gold.

Run:  .venv/bin/python src/sweep.py              every answerable question
      .venv/bin/python src/sweep.py Q22          one question
      .venv/bin/python src/sweep.py --show-text  full text_raw of each candidate

WHY THIS EXISTS
---------------
Q14 and Q26 each carried one gold chunk, and each turned out to have two or
three chunks restating the same fact. Under D5a all of them are gold, so both
labels were wrong. They were caught only because they collided on the same
chunk, which has nothing to do with the defect. The other 22 questions were
never checked for it.

WHAT IT SEARCHES FOR, AND WHY THAT IS NARROW
--------------------------------------------
D5b: "independently sufficient" means sufficient for the GOLD ANSWER, not for
the question. So this searches from the answer, never from the question.

Searching from the question would surface every chunk on the topic, which is
D5's rejected "contributory" rule wearing a script, and would drift to "on
topic" by question 19 exactly as D5 predicted.

WHY IT MATCHES IDENTIFIERS LITERALLY
------------------------------------
Three designs were tried and the first two failed the retro-test below.

1. Score the answer's whole vocabulary. Missed BOTH known defects. A restatement
   is written by a different author on a different page, so it shares the fact
   and not the phrasing. Q14's answer says `/init` "walks you through creating"
   a CLAUDE.md; `doc-05:c010` says "generate a starter CLAUDE.md file". One
   content word in common.

2. Tokenise the identifiers. Destroys what makes them identifiers: `/context`
   becomes "context", which is on 28 of 30 pages, and `agent` matched 650
   chunks.

3. Match identifiers as literal substrings, the way `show.py --find` does. A
   restatement of "run `/init` to create a CLAUDE.md" must contain the literal
   `/init`, whoever wrote it. This is that.

Identifiers are taken from the answer whether or not they are backticked, since
Q14's answer writes "a CLAUDE.md" in plain prose and that token is exactly what
separates a real restatement from a chunk mentioning `system/init`.

WHY ALL KEYS MUST MATCH
-----------------------
Requiring any one key returned 883 candidates, most of them chunks that mention
a command while documenting something else. Requiring all of them returns tight
sets and still catches both known defects.

WHY IT REPORTS ITS OWN BLIND SPOTS
----------------------------------
Some answers contain no identifier at all ("use auto mode when you trust the
general direction"), and some contain one so common that requiring it matches a
third of the corpus (`CLAUDE.md`, 108 chunks). For those questions this tool
cannot help, and saying "0 candidates" would be a lie that reads like a clean
bill of health. They are printed as NO KEY and TOO BROAD and have to be swept by
hand. That is the same failure the leak check had on its first run: an
unqualified zero from a check that could not have found anything.

WHY IT CANNOT DECIDE ANYTHING
-----------------------------
A literal match is a proxy for restatement. A chunk can carry every identifier
and be documenting the opposite case. The D5 delete test is a judgement about
meaning that no substring search performs. Output is a reading list.

It never loads the embedding model, for the reason in show.py's docstring: gold
must be found independently of the retriever being graded.
"""

import argparse
import re
import sys

import leakage
from show import load_chunks

# Slash commands, --flags, dotted.filenames, camelCase. These are the tokens a
# restatement on another page has to carry, because they are names rather than
# words and an author cannot paraphrase them.
IDENTIFIER = re.compile(
    r"(?:/[a-z][a-z0-9-]{2,}"           # /init, /reload-plugins
    r"|--[a-z][a-z0-9-]{2,}"            # --fork-session
    r"|[A-Za-z_][A-Za-z0-9_]*\.[a-z]{2,4}\b"   # CLAUDE.md, settings.json
    r"|\b[a-z]+[A-Z][A-Za-z]+\b"        # cleanupPeriodDays
    r"|\b[A-Z][a-z]+[A-Z][A-Za-z]+\b)"  # PreToolUse
)

# Above this many candidates the key is a word the corpus says everywhere, and
# the result is a reading list nobody reads. Reported as TOO BROAD instead.
BREADTH_LIMIT = 20

PUNCT = set("/-.@:+_")


def answer_keys(answer: str, df: dict[str, int], vocab: set[str]) -> set[str]:
    """Identifier-shaped strings in a gold answer, backticked or not.

    Backticked spans are added only when they look like names rather than
    English: `Bash` and `description` are backticked in real answers and match
    279 and 347 chunks respectively, which is noise. A span qualifies on
    punctuation (it is a path, flag or command) or on being rare enough that the
    corpus is not saying it everywhere.
    """
    keys = {m.group(0) for m in IDENTIFIER.finditer(answer)}

    for span in (s.strip() for s in re.findall(r"`([^`]+)`", answer)):
        if " " in span:
            # Multi-word literals like the full curl command match nothing, and
            # their parts are already caught by IDENTIFIER above.
            continue
        tokens = leakage.normalised_tokens(span, vocab)
        rare_enough = tokens and max(df.get(t, 0) for t in tokens) <= 12
        if any(ch in PUNCT for ch in span) or rare_enough:
            keys.add(span)

    return {k for k in keys if sum(ch.isalnum() for ch in k) >= 3}


def restatement_candidates(chunks: list[dict], gold_ids: set[str],
                           keys: set[str]) -> list[dict]:
    """Non-gold chunks containing every key, matched case-insensitively.

    Already-gold chunks are excluded rather than ranked: the answer was written
    from them, so they match by construction and are not what this is looking
    for.
    """
    out = []
    for c in chunks:
        if c["id"] in gold_ids:
            continue
        lowered = c["text_raw"].lower()
        if all(k.lower() in lowered for k in keys):
            out.append(c)
    return out


def parse_answers(text: str) -> dict[str, str]:
    """Gold answers by question ID.

    The answer runs from `**Gold answer:**` to the next bolded field, so it
    wraps across lines. Deliberately not added to leakage.parse_gold: that
    module must not depend on answer text, or re-wording an answer would move a
    leak number for no reason.
    """
    out = {}
    sections = re.split(r"^## (Q\d+)\s*$", text, flags=re.M)[1:]
    for qid, body in zip(sections[0::2], sections[1::2]):
        m = re.search(r"^\*\*Gold answer:\*\*(.*?)(?=^\*\*)", body, re.M | re.S)
        out[qid] = " ".join(m.group(1).split()) if m else ""
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find unlabeled chunks that restate a gold answer.")
    parser.add_argument("question", nargs="?", help="one question ID, e.g. Q22")
    parser.add_argument("--show-text", action="store_true",
                        help="print full text_raw instead of a snippet")
    parser.add_argument("--chars", type=int, default=300, help="snippet length")
    args = parser.parse_args()

    chunks = load_chunks()
    vocab = leakage.build_vocabulary(chunks)
    df = leakage.document_frequency(chunks, vocab)
    answers = parse_answers(leakage.GOLD_FILE.read_text(encoding="utf-8"))

    entries = [e for e in leakage.parse_gold(leakage.GOLD_FILE) if e["answerable"]]
    if args.question:
        entries = [e for e in entries if e["id"] == args.question.upper()]
        if not entries:
            sys.exit(f"no answerable question {args.question}")

    readable, no_key, too_broad, total = 0, [], [], 0

    for e in entries:
        keys = answer_keys(answers.get(e["id"], ""), df, vocab)
        print("=" * 96)
        print(f"{e['id']}  gold: {', '.join(e['gold_chunks'])}")

        if not keys:
            no_key.append(e["id"])
            print("  NO KEY: the answer contains no identifier. Sweep by hand.\n")
            continue

        hits = restatement_candidates(chunks, set(e["gold_chunks"]), keys)
        print(f"  keys (all must match): {', '.join(sorted(keys))}")

        if len(hits) > BREADTH_LIMIT:
            too_broad.append((e["id"], len(hits)))
            print(f"  TOO BROAD: {len(hits)} candidates. The key is something the "
                  f"corpus says everywhere. Sweep by hand.\n")
            continue

        readable += 1
        total += len(hits)
        if not hits:
            print("  no candidates\n")
            continue

        for c in hits:
            body = (c["text_raw"].strip() if args.show_text
                    else " ".join(c["text_raw"].split())[:args.chars] + "...")
            print(f"\n  {c['id']:14} {c['slug']:22} {c['block_type']}")
            print(f"    {body}")
        print()

    print("=" * 96)
    print(f"{total} candidate(s) to read across {readable} sweepable question(s).")
    if no_key:
        print(f"NO KEY, not swept: {', '.join(no_key)}")
    if too_broad:
        print("TOO BROAD, not swept: "
              + ", ".join(f"{q} ({n})" for q, n in too_broad))
    print("Neither list is a clean result. Those questions are unswept, "
          "not clean.")


if __name__ == "__main__":
    main()
