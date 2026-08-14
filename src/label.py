"""Hand-label the judge pools, one pool per screen.

Run:  .venv/bin/python src/label.py               next unlabeled pool onwards
      .venv/bin/python src/label.py --question Q04    jump to one pool

For each pool it prints the question, the gold answer, and every candidate in
full, then asks for the MINIMAL SUBSET that fully supports the answer. Answer
with the displayed numbers ("1 3"), or "none", or "q" to stop. Rows land in
judge/hand-labels.csv as you go, so stopping halfway loses nothing.

WHY A TOOL AND NOT JUST THE JSON
--------------------------------
judge/pools.json is 122 KB and a single candidate averages about 1,100
characters, so reading it by hand means scrolling past nine chunks you are not
currently judging. That is not a comfort problem: D5 necessity is decided
against the alternatives in the pool, so the whole pool has to be readable at
once and nothing else should be.

WHY IT ASKS FOR A SUBSET AND NOT A YES/NO PER CHUNK
--------------------------------------------------
Because that is the task the judge is given (day-13-judge-design.md, decision
1), and kappa between two raters doing different tasks is not a reliability
measure. Asking you chunk by chunk would let you answer "is this relevant",
which is the contributory rule D5 exists to reject.

WHY IT NEVER OPENS pools-key.json
---------------------------------
The key is the answer sheet. This tool imports nothing that can reach it, so
the only way to see gold status while labeling is to open it deliberately in
another window.

WHY IT WRITES AFTER EVERY POOL
------------------------------
24 pools is more than one sitting. Everything already answered is on disk and
the next run skips it, so the alternative - one long session you must not
interrupt - is the thing most likely to end with a rushed Q04.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POOLS_PATH = REPO_ROOT / "judge" / "pools.json"
LABELS_PATH = REPO_ROOT / "judge" / "hand-labels.csv"

FIELDS = ["question_id", "chunk_id", "necessary"]


def labeled_questions(csv_text: str) -> set[str]:
    """Question IDs that already have rows, so a second run resumes.

    Reads the text rather than the path so the resume rule is testable without
    a filesystem, and so a missing file is just the empty string.
    """
    rows = csv.DictReader(csv_text.splitlines())
    return {row["question_id"] for row in rows if row.get("question_id")}


def parse_selection(raw: str, candidates: list[dict]) -> list[str]:
    """Turn "1 3" into chunk IDs, or raise ValueError with the reason.

    Every rejection here is a case where guessing what you meant would write a
    label you did not intend. There is no downstream check that could catch it,
    because these labels ARE the reference.
    """
    text = raw.strip().lower()

    # "none" has to be spelled out. A bare Enter is the easiest key to hit by
    # accident while reading, and if it meant "nothing is necessary" the slip
    # would write a full pool of zeros that reads as a real judgment.
    if not text:
        raise ValueError('type numbers, "none", or "q" - blank is not "none"')
    if text == "none":
        return []

    picked = []
    for token in text.replace(",", " ").split():
        if not token.isdigit():
            raise ValueError(f'"{token}" is not a number')
        n = int(token)
        # The screen counts from 1. Accepting 0 would silently shift the whole
        # pool by one position.
        if not 1 <= n <= len(candidates):
            raise ValueError(f"{n} is outside 1-{len(candidates)}")
        if n in picked:
            raise ValueError(f"{n} listed twice - lost your place?")
        picked.append(n)

    return [candidates[n - 1]["id"] for n in picked]


def rows_for(pool: dict, chosen: list[str]) -> list[dict]:
    """One row per candidate, in pool order, chosen or not.

    The negatives are 55 of the 99 pairs. Writing only the chosen chunks would
    leave kappa with nothing to disagree about.
    """
    return [
        {"question_id": pool["id"],
         "chunk_id": c["id"],
         "necessary": 1 if c["id"] in chosen else 0}
        for c in pool["candidates"]
    ]


def show_pool(pool: dict, position: int, total: int) -> None:
    """Print one pool in full: the question, the answer, every candidate."""
    print("\n" + "=" * 78)
    print(f"{pool['id']}   pool {position} of {total}   "
          f"{len(pool['candidates'])} candidates")
    print("=" * 78)
    print(f"\nQUESTION\n  {pool['question']}")
    print(f"\nGOLD ANSWER\n  {pool['gold_answer']}")

    for i, c in enumerate(pool["candidates"], start=1):
        print("\n" + "-" * 78)
        # The number is what you type, so it goes first and stays loud.
        print(f"[{i}]  {c['id']}")
        print("-" * 78)
        print(c["text"])

    print("\n" + "=" * 78)
    print("Which chunks are REQUIRED? Delete any one of them and the gold "
          "answer\nis no longer supported. Smallest sufficient set, not "
          "everything relevant.")


def ask(pool: dict) -> list[str] | None:
    """Prompt until the answer parses. None means stop for now."""
    while True:
        raw = input(f"{pool['id']} > ")
        if raw.strip().lower() == "q":
            return None
        try:
            return parse_selection(raw, pool["candidates"])
        except ValueError as exc:
            print(f"  {exc}")


def append(rows: list[dict]) -> None:
    """Append one pool's rows, writing the header if the file is new."""
    new_file = not LABELS_PATH.exists()
    with LABELS_PATH.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hand-label the judge pools, one pool per screen.")
    parser.add_argument("--question", metavar="ID",
                        help="label just this pool, e.g. Q04")
    args = parser.parse_args()

    pools = json.loads(POOLS_PATH.read_text(encoding="utf-8"))["pools"]
    done = labeled_questions(
        LABELS_PATH.read_text(encoding="utf-8") if LABELS_PATH.exists() else "")

    if args.question:
        pending = [p for p in pools if p["id"] == args.question]
        if not pending:
            sys.exit(f"no pool {args.question} - IDs look like Q04")
        if args.question in done:
            sys.exit(f"{args.question} is already labeled in {LABELS_PATH.name}")
    else:
        pending = [p for p in pools if p["id"] not in done]

    if not pending:
        print(f"all {len(pools)} pools labeled. Commit "
              f"{LABELS_PATH.name}, record its sha256, then run the judge.")
        return

    print(f"{len(done)} of {len(pools)} pools labeled, {len(pending)} to go.")
    for pool in pending:
        # Position in the whole set, not in this run's queue: with --question
        # the queue is one pool long and Q04 is still the 4th of 24.
        show_pool(pool, pools.index(pool) + 1, len(pools))
        chosen = ask(pool)
        if chosen is None:
            print(f"\nstopped. {LABELS_PATH.name} has everything up to here.")
            return
        append(rows_for(pool, chosen))
        print(f"  saved: {len(chosen)} of {len(pool['candidates'])} necessary")

    print(f"\nall {len(pools)} pools labeled. Commit {LABELS_PATH.name} and "
          f"record its sha256 before the judge runs.")


if __name__ == "__main__":
    main()
