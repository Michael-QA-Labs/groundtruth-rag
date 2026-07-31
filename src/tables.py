"""Render markdown table rows as self-labelling text.

WHY TABLES GET THEIR OWN MODULE
-------------------------------
40% of this corpus is markdown tables. The obvious way to chunk one — slice it
like any other text and repeat the header on each piece — was measured and
rejected: it would have made 65% of every table chunk a repeated header, leaving
about a third of the embedding model's token budget for actual content.

So instead each row is rendered to carry its own labels:

    | Key                 | Description               | Default |
    |---------------------|---------------------------|---------|
    | `permissions.allow` | Array of permission rules | `[]`    |

becomes

    permissions.allow
    Description: Array of permission rules
    Default: []

Nothing is repeated, the row stands alone, and a question like "what does
permissions.allow do?" now has one self-contained chunk to match against.

WHY THE CELL SPLITTER IS HAND-WRITTEN
-------------------------------------
`line.split("|")` corrupts 117 rows in this corpus:

  * 115 rows contain an ESCAPED pipe (`\\|`), which is a literal character in the
    cell text, not a column boundary.
  * 2 rows contain a real pipe inside a code span, e.g. `cmd | grep x`.

Both look like column separators to a naive split, which silently shifts every
cell after them into the wrong column — so a "Default" value would be filed
under "Description" and the chunk would state something false. Cheap to prevent,
invisible once it has happened, which is the worst combination.
"""

import re


def split_cells(line: str) -> list[str]:
    """Split one table row into cells, respecting escapes and code spans.

    Walks the line one character at a time rather than using a regex, because
    the decision "is this pipe a boundary?" depends on state (are we inside
    backticks?) that a regex cannot carry cleanly.
    """
    line = line.strip()
    # Drop the decorative leading and trailing pipes so we don't produce an
    # empty cell at each end.
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]

    cells: list[str] = []
    current: list[str] = []
    in_code = False
    i = 0

    while i < len(line):
        char = line[i]

        # 1. An escaped pipe is content. Consume both characters and keep the
        #    pipe, dropping the backslash — the reader wants "a | b", not "a \| b".
        if char == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            current.append("|")
            i += 2
            continue

        # 2. A backtick flips whether we are inside a code span. Pipes are only
        #    column boundaries when we are outside one.
        if char == "`":
            in_code = not in_code
            current.append(char)

        # 3. A bare pipe outside code ends the current cell.
        elif char == "|" and not in_code:
            cells.append("".join(current))
            current = []

        else:
            current.append(char)

        i += 1

    cells.append("".join(current))
    return [_clean_cell(c) for c in cells]


def _clean_cell(cell: str) -> str:
    """Trim padding and drop backticks.

    These tables are space-padded to align their columns in the raw markdown —
    measured at ~60% of table row text. That padding is invisible to a reader
    and pure cost to a tokenizer, so it goes.

    Backticks go too: they mark code identifiers for a human, but to an
    embedding model they are noise that never appears in a user's question.
    Note this is applied AFTER splitting, so removing them cannot affect where
    the cell boundaries were found.
    """
    cell = cell.strip()
    # Collapse runs of two or more spaces. Single spaces between words are left
    # alone so ordinary prose in a cell is untouched.
    cell = re.sub(r" {2,}", " ", cell)
    return cell.replace("`", "").strip()


def is_separator(line: str) -> bool:
    """True for the |---|---| line under a table header.

    It carries no information and is dropped, which is worth doing on its own:
    these separators average 210 characters here because the columns are wide.
    """
    return bool(re.fullmatch(r"[\s|:\-]+", line)) and "-" in line


def is_table_block(text: str) -> bool:
    """True if this block of text is a markdown table."""
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 3:
        return False
    piped = sum(1 for l in lines if l.lstrip().startswith("|"))
    return piped >= len(lines) - 1


def render_row(headers: list[str], cells: list[str]) -> str:
    """Turn one row into `subject` + `Label: value` lines.

    The first cell becomes a bare subject line rather than "Key: permissions.allow"
    because it is almost always the identifier a user would search for, and
    putting it alone on the first line keeps it prominent for both a reader
    skimming chunks on Day 4 and the embedding model.
    """
    if not cells:
        return ""

    lines = [cells[0]] if cells[0] else []

    for i in range(1, len(cells)):
        value = cells[i]
        if not value:
            continue                    # empty cell carries nothing; skip it
        # 105 rows in this corpus have more cells than their header declares.
        # Dropping the surplus would silently lose content, so they get a
        # positional label instead.
        label = headers[i] if i < len(headers) else f"Column {i + 1}"
        lines.append(f"{label}: {value}" if label else value)

    return "\n".join(lines)


def render_table(block: str) -> list[str]:
    """Render a whole table block into one string per data row.

    Returns a list rather than joined text so the chunker can pack rows up to
    its token budget without having to re-split them.
    """
    lines = [l for l in block.splitlines() if l.strip()]
    if not lines:
        return []

    headers = split_cells(lines[0])
    rendered = []
    for line in lines[1:]:
        if is_separator(line):
            continue
        cells = split_cells(line)
        text = render_row(headers, cells)
        if text:
            rendered.append(text)
    return rendered


def cell_count(line: str) -> int:
    """How many cells this row has, per the same rules as split_cells.

    Used by the conservation check in the tests: if the renderer ever loses a
    cell, counts stop reconciling and the test fails loudly rather than shipping
    mis-filed content into the gold set.
    """
    return len(split_cells(line))
