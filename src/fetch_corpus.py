"""Download the docs corpus.

Run:  python fetch_corpus.py

Fetches the 30 pages listed in PAGES as raw markdown, saves each as
corpus/doc-NN.md, and writes corpus/INDEX.md with a content hash.

The corpus is FROZEN as of 2026-07-29. Re-running this script should reproduce
the same hash. If it doesn't, the upstream docs changed and every number in
results/ predates that change — see corpus/INDEX.md.
"""

import hashlib
import time
from datetime import date
from pathlib import Path

# urllib is in the standard library, so no pip install needed.
# If you'd rather use `requests`, that's fine too — swap the import.
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


# This file lives in src/, so the corpus is one level UP and then down again:
#   src/fetch_corpus.py  ->  .parent is src/  ->  .parent.parent is the repo root
# .resolve() first turns a relative invocation like `python src/fetch_corpus.py`
# into an absolute path, so the corpus is found no matter which directory you
# run the script from.
CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"

CODE_BASE = "https://code.claude.com/docs/en"

# Unused in the frozen corpus, kept so re-adding API pages is a one-line change.
API_BASE = "https://platform.claude.com/docs/en"

# (base_url, slug) pairs. Order here decides doc-01, doc-02, ...
#
# This list IS the corpus definition. Once INDEX.md is written it is frozen:
# changing this list changes every number computed downstream, which makes old
# results uncomparable with new ones. See notes/decisions.md (D1).
#
# Note: the initial candidate list also included 6 API pages from
# platform.claude.com. Those were dropped in favour of 6 more Claude Code
# pages — see notes/decisions.md (D2) for why, and what it costs us.
PAGES = [
    # --- Foundations (5)
    (CODE_BASE, "overview"),
    (CODE_BASE, "quickstart"),
    (CODE_BASE, "how-claude-code-works"),
    (CODE_BASE, "common-workflows"),
    (CODE_BASE, "best-practices"),

    # --- Config & control (5)
    (CODE_BASE, "memory"),
    (CODE_BASE, "settings"),
    (CODE_BASE, "cli-reference"),
    (CODE_BASE, "context-window"),
    (CODE_BASE, "permissions"),

    # --- Extending (8)
    (CODE_BASE, "checkpointing"),
    (CODE_BASE, "skills"),
    (CODE_BASE, "hooks-guide"),
    (CODE_BASE, "hooks"),
    (CODE_BASE, "sub-agents"),
    (CODE_BASE, "mcp"),
    (CODE_BASE, "tools-reference"),
    (CODE_BASE, "plugins"),

    # --- Headless & CI (3)
    (CODE_BASE, "headless"),
    (CODE_BASE, "github-actions"),
    (CODE_BASE, "code-review"),

    # --- Surfaces (2)
    (CODE_BASE, "worktrees"),
    (CODE_BASE, "output-styles"),

    # --- Agent SDK (7)
    (CODE_BASE, "agent-sdk/overview"),
    (CODE_BASE, "agent-sdk/python"),
    (CODE_BASE, "agent-sdk/custom-tools"),
    (CODE_BASE, "agent-sdk/structured-outputs"),
    (CODE_BASE, "agent-sdk/hooks"),
    (CODE_BASE, "agent-sdk/cost-tracking"),
    (CODE_BASE, "agent-sdk/sessions"),
]


# ---------------------------------------------------------------- YOU WRITE --

def fetch_page(base: str, slug: str) -> str | None:
    """Fetch one page as markdown.

    Build the URL by joining base + slug + ".md", request it, return the body
    as a string. Return None if the request fails — a 404 on one page should
    not kill the whole run.

    Hint: urlopen(...).read() gives you bytes, not str.
    """
    # 1. Build the address we want to download.
    url = f"{base}/{slug}.md"

    # 2. Describe the request. This does NOT download anything yet —
    #    it's just an object holding the URL and the headers.
    #    The User-Agent is required: without it the server returns 403.
    headers = {"User-Agent": "rag-eval-practice/1.0"}
    req = Request(url, headers=headers)

    # 3. Try to download. If anything in here fails, jump to `except`.
    try:
        response = urlopen(req, timeout=30)   # actually hits the network
        raw_bytes = response.read()           # b'# Overview\n...'
        response.close()                      # hang up the connection
        text = raw_bytes.decode("utf-8")      # '# Overview\n...'
        return text                           # SUCCESS: hand back a str

    # 4a. Server replied, but with an error (404 = no such page).
    except HTTPError as e:
        print(f"  HTTP {e.code} for {url}")
        return None

    # 4b. Never even reached the server (no wifi, bad domain).
    except URLError as e:
        print(f"  network error for {url}: {e.reason}")
        return None


def save_page(doc_id: str, text: str) -> Path:
    """Write the markdown to corpus/<doc_id>.md and return the path."""
    # 1. Build the destination path.
    #    We name the file after the doc_id ("doc-25.md") and NOT after the slug.
    #    That looks like a downgrade in readability, and it is — but seven of
    #    our slugs look like "agent-sdk/python". That "/" is a directory
    #    separator, so a slug-named file would try to write into a
    #    corpus/agent-sdk/ folder that doesn't exist, and crash. doc-NN is flat
    #    by construction. INDEX.md is what remembers which ID is which slug.
    path = CORPUS_DIR / f"{doc_id}.md"

    # 2. Write the text to disk.
    #    write_text() opens the file, writes it, and closes it in one call —
    #    no `with open(...)` block needed for a single write like this.
    #
    #    encoding="utf-8" is NOT optional. These pages contain arrows (→), box
    #    drawing, and emoji. Without it, Python falls back to the machine's
    #    default encoding, which on some systems is cp1252, and the write dies
    #    with a UnicodeEncodeError partway through. Being explicit means the
    #    script behaves identically no matter whose laptop runs it.
    path.write_text(text, encoding="utf-8")

    # 3. Hand the path back.
    #    main() ignores it today, but returning it means you can verify the
    #    write from a REPL, and a future caller could check path.stat().st_size
    #    without recomputing where the file went.
    return path


def write_index(rows: list[dict]) -> None:
    """Write corpus/INDEX.md as a markdown table.

    Each row dict has: id, slug, url, chars

    | ID | Slug | Source URL | Chars |
    |---|---|---|---|
    | doc-01 | quickstart | https://... | 12431 |
    """
    # 1. Stamp the run with a date.
    #    Every row gets the same date because they came from the same run. If
    #    you ever re-fetch a single page, that page's date will disagree with
    #    the rest — which is exactly the signal you want, because it means the
    #    corpus is no longer one coherent snapshot.
    today = date.today().isoformat()

    # 2. Compute a content hash over the corpus.
    #    This is the "freeze" step. A sha256 over every doc's bytes, in row
    #    order, collapses the whole corpus into one 64-character fingerprint.
    #    Later, before trusting a metric, you re-run this and compare: if the
    #    hash matches, the corpus is byte-identical to the one those numbers
    #    were computed on. If it doesn't, the numbers are stale and you know it
    #    instead of guessing.
    #
    #    Order matters — hashing the same files in a different order gives a
    #    different digest — which is why we walk `rows` (fixed by PAGES) rather
    #    than something order-unstable like CORPUS_DIR.iterdir().
    #
    #    read_bytes(), not read_text(): we want the fingerprint of what is
    #    actually on disk, before any decoding step gets a chance to normalise
    #    line endings or characters.
    digest = hashlib.sha256()
    for row in rows:
        digest.update((CORPUS_DIR / f"{row['id']}.md").read_bytes())
    corpus_hash = digest.hexdigest()

    # 3. Find the size outliers.
    #    Chunk count scales with character count, so a page 30x larger than
    #    another contributes ~30x the chunks and ~30x the chances of being
    #    retrieved by luck. Surfacing the top 3 right here in INDEX.md means
    #    you can't forget about the skew when you read your Day 8 numbers.
    total_chars = sum(row["chars"] for row in rows)
    biggest = sorted(rows, key=lambda row: row["chars"], reverse=True)[:3]
    biggest_share = sum(row["chars"] for row in biggest) / total_chars

    # 4. Build the file as a list of lines, then join once at the end.
    #    Accumulating into a list and joining beats `text += ...` in a loop:
    #    strings are immutable in Python, so every += copies the whole string
    #    built so far. Irrelevant at 30 rows, a real cost at 30,000, and it's
    #    the same amount of typing either way.
    lines = [
        "# Corpus INDEX",
        "",
        f"{len(rows)} pages from the Claude Code docs, fetched {today}.",
        "",
        "**FROZEN.** Do not add, remove, or re-fetch pages. Every metric in",
        "`results/` is only comparable to another number computed against this",
        "exact corpus. To verify nothing has drifted, re-run this script and",
        "check the hash below still matches.",
        "",
        f"- Total: {total_chars:,} chars",
        f"- sha256: `{corpus_hash}`",
        "",
        "## Size skew — read this before trusting a metric",
        "",
        f"The three largest pages are {biggest_share:.0%} of the corpus by characters:",
        "",
    ]
    for row in biggest:
        lines.append(f"- `{row['slug']}` — {row['chars']:,} chars")
    lines += [
        "",
        "They were kept rather than dropped (see notes/decisions.md D3), so",
        "expect them to dominate chunk counts. Report per-doc chunk counts",
        "alongside any aggregate metric.",
        "",
        "## Pages",
        "",
        "| ID | Slug | Source URL | Chars | Fetched |",
        # The `---:` in the Chars column right-aligns the numbers, which makes
        # the size skew visible at a glance instead of buried in ragged text.
        "|---|---|---|---:|---|",
    ]

    # 5. One table row per page.
    #    {row['chars']:,} inserts thousands separators — 271,213 rather than
    #    271213 — because you will be eyeballing these numbers a lot this week.
    for row in rows:
        lines.append(
            f"| {row['id']} | `{row['slug']}` | {row['url']}.md "
            f"| {row['chars']:,} | {today} |"
        )

    # 6. Write it out.
    #    "\n".join() puts newlines BETWEEN lines, so the last line has none —
    #    hence the trailing "\n". Text files are expected to end with one, and
    #    git will complain (`\ No newline at end of file`) if it's missing.
    index_path = CORPUS_DIR / "INDEX.md"
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {index_path}")
    print(f"corpus sha256: {corpus_hash}")


# -------------------------------------------------------------------- GIVEN --

def main() -> None:
    CORPUS_DIR.mkdir(exist_ok=True)
    rows = []

    for i, (base, slug) in enumerate(PAGES, start=1):
        doc_id = f"doc-{i:02d}"
        text = fetch_page(base, slug)

        if text is None:
            print(f"  SKIP {doc_id}  {slug}")
            continue

        save_page(doc_id, text)
        rows.append({
            "id": doc_id,
            "slug": slug,
            "url": f"{base}/{slug}",
            "chars": len(text),
        })
        print(f"  ok   {doc_id}  {slug}  ({len(text):,} chars)")

        time.sleep(0.5)  # be polite

    write_index(rows)
    print(f"\n{len(rows)} pages saved to {CORPUS_DIR}")


if __name__ == "__main__":
    main()
