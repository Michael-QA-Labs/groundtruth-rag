"""Tests for the table cell splitter and row renderer.

These target the failures that change MEANING rather than appearance. A cell
filed under the wrong column produces a chunk that states something false, and
nothing downstream would ever flag it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tables                                                    # noqa: E402
from fetch_corpus import CORPUS_DIR                              # noqa: E402


# ------------------------------------------------------- the splitter rules --

def test_plain_row_splits_into_cells():
    cells = tables.split_cells("| `foo` | does a thing | `[]` |")
    assert cells == ["foo", "does a thing", "[]"]


def test_pipe_inside_backticks_is_not_a_boundary():
    """`cmd | grep x` is ONE cell. A naive split would make it two and shift
    every later cell into the wrong column."""
    cells = tables.split_cells("| `cmd | grep x` | runs a pipeline |")
    assert len(cells) == 2
    assert "cmd | grep x" in cells[0]


def test_escaped_pipe_is_content_not_a_boundary():
    """115 rows in this corpus use \\| as a literal pipe."""
    cells = tables.split_cells(r"| a \| b | second |")
    assert len(cells) == 2
    assert cells[0] == "a | b"          # backslash dropped, pipe kept


def test_padding_is_collapsed_but_words_are_not_joined():
    cells = tables.split_cells("|  spaced     out   |  b  |")
    assert cells == ["spaced out", "b"]


def test_backticks_removed_after_splitting():
    cells = tables.split_cells("| `--flag` | `value` |")
    assert cells == ["--flag", "value"]


def test_separator_row_detected():
    assert tables.is_separator("|---|---|")
    assert tables.is_separator("| :--- | ---: |")
    assert not tables.is_separator("| real | content |")


# --------------------------------------------------------- the row renderer --

def test_row_renders_as_subject_plus_labels():
    headers = ["Key", "Description", "Default"]
    cells = ["permissions.allow", "Array of rules", "[]"]
    out = tables.render_row(headers, cells)
    assert out.splitlines() == [
        "permissions.allow",
        "Description: Array of rules",
        "Default: []",
    ]


def test_header_is_never_repeated_in_output():
    """The whole reason this module exists: no boilerplate per row."""
    block = (
        "| Key | Description |\n"
        "|---|---|\n"
        "| a | first |\n"
        "| b | second |\n"
    )
    rows = tables.render_table(block)
    assert len(rows) == 2
    # "Key" is the first column's label and must not appear anywhere, since the
    # subject line is bare.
    assert not any(r.startswith("Key:") for r in rows)


def test_extra_cells_are_kept_not_dropped():
    """105 rows have more cells than their header declares. Dropping the
    surplus would silently lose content."""
    out = tables.render_row(["Key", "Description"], ["a", "b", "c"])
    assert "c" in out


def test_empty_cells_are_skipped():
    out = tables.render_row(["Key", "Description", "Default"], ["a", "", "z"])
    assert "Description:" not in out
    assert "Default: z" in out


# ------------------------------------------------- conservation on real data --

def test_no_cell_is_lost_across_the_whole_corpus():
    """Every non-empty cell of every real table row must appear in its rendered
    output. This is the assertion that catches a splitter regression."""
    import re

    checked = 0
    for path in sorted(CORPUS_DIR.glob("doc-*.md")):
        for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
            if not tables.is_table_block(block):
                continue
            lines = [l for l in block.splitlines() if l.strip()]
            headers = tables.split_cells(lines[0])
            for line in lines[1:]:
                if tables.is_separator(line):
                    continue
                cells = tables.split_cells(line)
                rendered = tables.render_row(headers, cells)
                for cell in cells:
                    if cell:
                        assert cell in rendered, (
                            f"lost cell {cell!r} from {path.name}: {line[:80]!r}"
                        )
                checked += 1

    assert checked > 1000, f"expected to check >1000 real rows, got {checked}"
