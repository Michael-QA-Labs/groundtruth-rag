"""Build `gold/gold-set.json` from the markdown gold set.

Run:  .venv/bin/python src/build_gold.py           write the file
      .venv/bin/python src/build_gold.py --check   fail if it is out of date

WHY THIS IS GENERATED AND NOT WRITTEN
-------------------------------------
Day 6 onward needs the labels as data, and the labels change: eight of them moved
during Day 5 alone. A hand-maintained JSON beside a hand-maintained markdown is
two copies of the same facts, and the copy nobody is reading goes stale silently.
The markdown stays the working surface because that is where the reasoning lives;
this file is its machine-readable projection, and `--check` in the test suite
fails the build if the two diverge.

WHY THERE IS NO TIMESTAMP IN THE OUTPUT
---------------------------------------
A generated-at field would make the file differ from its own regeneration one
second later, which would make `--check` useless. Provenance is carried by
content instead: the corpus sha256 and the index manifest's hashes, which is what
actually determines whether a label is still valid. D1 froze the corpus for this
reason: a gold label means nothing without the bytes it was written against.

WHY IT REFUSES TO EMIT ON A BROKEN INVARIANT
--------------------------------------------
Silent partial output is how a bad number reaches the README. The counts here
were wrong in three separate places before 2026-08-05, each time because
authorship was recounted by hand from prose. So this asserts the structural
invariants and exits non-zero rather than writing a file that looks fine.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import leakage
import sweep
from show import load_chunks

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "gold" / "gold-set.json"
MANIFEST = ROOT / "index" / "manifest.json"


def parse_entries(text: str) -> list[dict]:
    """One record per `## QNN` section.

    Fields come from the same single-line `**Field:**` shapes leakage.py reads.
    `Authorship` is parsed strictly rather than inferred from the prose markers
    that used to carry it, because inferring it is what produced three wrong
    counts.
    """
    sections = re.split(r"^## (Q\d+)\s*$", text, flags=re.M)[1:]
    entries = []

    for qid, body in zip(sections[0::2], sections[1::2]):
        def field(name, pattern=r"(.*)$"):
            m = re.search(rf"^\*\*{name}:\*\*\s*{pattern}", body, re.M)
            return m.group(1).strip() if m else ""

        answer = re.search(r"^\*\*Gold answer:\*\*(.*?)(?=^\*\*)", body, re.M | re.S)
        author = re.search(r"^\*\*Authorship:\*\* question=(\w+), answer=(\w+)$",
                           body, re.M)
        if not author:
            sys.exit(f"{qid}: no Authorship field. Add it before building.")

        answerable = field("Answerable").lower() == "yes"
        chunks = re.findall(r"`(doc-\d+:c\d+)`", field("Gold chunks"))

        entries.append({
            "id": qid,
            "question": field("Question"),
            "type": field("Type") or None,
            "answerable": answerable,
            "gold_chunks": chunks,
            # Doc-level metrics fall out of chunk labels for free (template rule
            # 1). Precomputed here so a consumer never has to re-derive it and
            # get the de-duplication wrong.
            "gold_docs": sorted({c.split(":")[0] for c in chunks}),
            # Unanswerable entries carry an empty `**Gold answer:**` line, which
            # collapses to "" rather than absent. Normalised to null so that
            # "has no gold answer" is one test, not two.
            "gold_answer": (" ".join(answer.group(1).split()) or None) if answer else None,
            # Answerable entries write "n/a" here by template convention. That
            # is prose for "not applicable", not a value, so it becomes null
            # rather than a string a consumer might test for truthiness.
            "not_covered_because": (field("Not covered because") or None
                                    if field("Not covered because").lower() != "n/a"
                                    else None),
            "question_author": author.group(1),
            "answer_author": author.group(2),
        })
    return entries


def check_invariants(entries: list[dict], chunk_ids: set[str]) -> None:
    """Refuse to emit a file that would be quietly wrong.

    Each of these has actually been violated at some point this week, which is
    the only reason any of them is here.
    """
    if len(entries) != 30:
        sys.exit(f"expected 30 questions, parsed {len(entries)}")

    ids = [e["id"] for e in entries]
    if ids != [f"Q{n:02d}" for n in range(1, 31)]:
        sys.exit("question IDs are not Q01..Q30 in order")

    for e in entries:
        if e["answerable"]:
            if not e["gold_chunks"]:
                sys.exit(f"{e['id']}: answerable with no gold chunks")
            if not e["gold_answer"]:
                sys.exit(f"{e['id']}: answerable with no gold answer")
            missing = [c for c in e["gold_chunks"] if c not in chunk_ids]
            if missing:
                sys.exit(f"{e['id']}: gold chunks not in the index: {missing}")
            if e["answer_author"] == "none":
                sys.exit(f"{e['id']}: answerable but answer_author=none")
        else:
            if e["gold_chunks"]:
                sys.exit(f"{e['id']}: unanswerable but cites chunks")
            if e["answer_author"] != "none":
                sys.exit(f"{e['id']}: unanswerable but answer_author="
                         f"{e['answer_author']}")
            if not e["not_covered_because"]:
                sys.exit(f"{e['id']}: unanswerable with no evidence recorded")


def build() -> dict:
    text = leakage.GOLD_FILE.read_text(encoding="utf-8")
    entries = parse_entries(text)
    chunk_ids = {c["id"] for c in load_chunks()}
    check_invariants(entries, chunk_ids)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    answerable = [e for e in entries if e["answerable"]]

    return {
        # Provenance first: a label is only valid against the bytes it was
        # written from, and these are what prove which bytes those were.
        "corpus_sha256": manifest["corpus_sha256"],
        "index": {
            "n_chunks": manifest["n_chunks"],
            "model": manifest["model"],
            "embedding_dim": manifest["embedding_dim"],
            "token_limit": manifest["token_limit"],
            "vectors_sha256": manifest["vectors_sha256"],
        },
        "source": "gold/gold-set-template.md",
        "counts": {
            "questions": len(entries),
            "answerable": len(answerable),
            "unanswerable": len(entries) - len(answerable),
            "gold_chunks_total": sum(len(e["gold_chunks"]) for e in answerable),
            "multi_chunk_answerable": sum(1 for e in answerable
                                          if len(e["gold_chunks"]) > 1),
            "question_author": {
                "author": sum(1 for e in entries if e["question_author"] == "author"),
                "claude": sum(1 for e in entries if e["question_author"] == "claude"),
            },
            "answer_author": {
                "author": sum(1 for e in entries if e["answer_author"] == "author"),
                "claude": sum(1 for e in entries if e["answer_author"] == "claude"),
                "none": sum(1 for e in entries if e["answer_author"] == "none"),
            },
        },
        "notes": {
            "recall_undefined_when_unanswerable":
                "Unanswerable questions have no gold chunk, so recall and "
                "precision are undefined. Score them on abstention and exclude "
                "them from the means.",
            "gold_is_a_set":
                "Where several chunks each independently support the gold "
                "answer they are alternatives under D5a and all are gold. "
                "Retrieving one of N scores 1/N on recall while fully serving "
                "the user, so read MRR and first-relevant-rank alongside "
                "recall wherever len(gold_chunks) > 1.",
            "unanswerable_answer_author":
                "answer_author is 'none' for unanswerable questions because no "
                "gold answer exists. Their not_covered_because evidence was "
                "verified on Day 4.",
        },
        "questions": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build gold/gold-set.json.")
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero if the file is missing or stale")
    args = parser.parse_args()

    payload = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not OUT.exists():
            sys.exit(f"{OUT} does not exist. Run src/build_gold.py")
        if OUT.read_text(encoding="utf-8") != payload:
            sys.exit(f"{OUT} is stale. Re-run src/build_gold.py")
        print(f"{OUT.name} is current")
        return

    OUT.write_text(payload, encoding="utf-8")
    data = json.loads(payload)
    c = data["counts"]
    print(f"wrote {OUT.relative_to(ROOT)}: {c['questions']} questions, "
          f"{c['answerable']} answerable, {c['gold_chunks_total']} gold chunks")


if __name__ == "__main__":
    main()
