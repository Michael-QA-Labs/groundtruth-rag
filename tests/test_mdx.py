"""Tests for the MDX transform.

The two that matter most are the <Tabs> and <Steps> cases. Those tags encode
whether a set of blocks are ALTERNATIVES or a SEQUENCE, and getting them wrong
produces text that asserts something untrue rather than merely reading oddly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import mdx                                                       # noqa: E402
from fetch_corpus import CORPUS_DIR                              # noqa: E402


# ------------------------------------------------ structure-preserving rules --

def test_tabs_become_labelled_alternatives():
    """Without this, three install methods read as one sequential procedure."""
    src = (
        "<Tabs>\n"
        '<Tab title="npm">Run npm install.</Tab>\n'
        '<Tab title="Homebrew">Run brew install.</Tab>\n'
        "</Tabs>\n"
    )
    out = mdx.transform(src)
    assert "Alternative (npm):" in out
    assert "Alternative (Homebrew):" in out
    assert "<Tab" not in out
    # The bodies must survive.
    assert "Run npm install." in out
    assert "Run brew install." in out


def test_steps_are_numbered_in_order():
    src = (
        "<Steps>\n"
        '<Step title="Install">Do the install.</Step>\n'
        '<Step title="Configure">Edit settings.</Step>\n'
        '<Step title="Run">Start it.</Step>\n'
        "</Steps>\n"
    )
    out = mdx.transform(src)
    assert "1. Install" in out
    assert "2. Configure" in out
    assert "3. Run" in out


def test_step_numbering_restarts_per_block():
    """Two procedures on one page must not run 1,2,3,4 — the second is its own
    sequence and a chunk containing "step 3" should mean the third step of ITS
    procedure."""
    src = (
        '<Steps><Step title="A">x</Step><Step title="B">y</Step></Steps>\n'
        '<Steps><Step title="C">z</Step></Steps>\n'
    )
    out = mdx.transform(src)
    assert "1. A" in out and "2. B" in out
    assert "1. C" in out
    assert "3. C" not in out


def test_accordion_title_is_kept():
    """Accordion titles are usually phrased as the question a user would ask,
    which is exactly the text a query needs to match."""
    src = '<Accordion title="Why does this happen?">Because of X.</Accordion>'
    out = mdx.transform(src)
    assert "Why does this happen?" in out
    assert "Because of X." in out
    assert "<Accordion" not in out


# ------------------------------------------------------- presentational tags --

def test_note_tip_warning_are_unwrapped_keeping_body():
    src = "<Note>Keep this text.</Note><Tip>And this.</Tip><Warning>This too.</Warning>"
    out = mdx.transform(src)
    assert "Keep this text." in out
    assert "And this." in out
    assert "This too." in out
    for tag in ("<Note>", "<Tip>", "<Warning>"):
        assert tag not in out


def test_card_titles_are_kept():
    """Regression: dropping <Card> wholesale stranded its description with no
    subject, so a query for "best practices" could never match the card that
    links to exactly that page."""
    src = (
        '<CardGroup cols={2}>\n'
        '<Card title="Best practices" icon="star" href="/docs/en/best-practices">\n'
        'Get better results with effective prompting\n'
        '</Card>\n'
        '</CardGroup>\n'
    )
    out = mdx.transform(src)
    assert "Best practices" in out
    assert "Get better results with effective prompting" in out
    # icon and href are genuinely decoration.
    assert "star" not in out
    assert "<Card" not in out


def test_no_visible_title_attribute_is_ever_dropped():
    """Every tag carrying a human-visible title= must survive the transform.

    This is the automated form of the side-by-side inspection check: text_embed
    is allowed to look different from text_raw, but it may not LOSE anything a
    question could hinge on.
    """
    import re

    lost = []
    for path in sorted(CORPUS_DIR.glob("doc-*.md")):
        text = path.read_text(encoding="utf-8")
        out = mdx.transform(text)
        for m in re.finditer(r'<(Step|Tab|Accordion|Card)\s+[^>]*?title="([^"]+)"', text):
            if m.group(2) not in out:
                lost.append((path.stem, m.group(1), m.group(2)))

    assert not lost, f"titles dropped by the transform: {lost[:5]}"


def test_layout_html_is_dropped():
    out = mdx.transform('<div class="x"><span>content</span></div>')
    assert out.strip() == "content"


# ------------------------------------------------------------ fence safety --

def test_html_inside_code_fences_is_untouched():
    """46 lowercase HTML tags in this corpus sit inside fences as EXAMPLES.
    Rewriting them would corrupt the code samples."""
    src = 'before\n\n```html\n<div class="demo"><span>hi</span></div>\n```\n\nafter'
    out = mdx.transform(src)
    assert '<div class="demo">' in out
    assert "<span>hi</span>" in out


def test_fenced_content_survives_verbatim_on_real_docs():
    """Every code fence in the real corpus must come through byte-identical."""
    import re

    for path in sorted(CORPUS_DIR.glob("doc-*.md")):
        text = path.read_text(encoding="utf-8")
        out = mdx.transform(text)
        marks = [m.start() for m in re.finditer(r"^```", text, re.M)]
        for i in range(0, len(marks) - 1, 2):
            fence = text[marks[i]:marks[i + 1]]
            if len(fence) > 40:          # skip trivial fences
                assert fence in out, f"fence altered in {path.name}"


def test_no_component_tags_survive_the_transform():
    """Nothing tag-shaped should be left in the prose of any real doc."""
    import re

    leftovers = {}
    for path in sorted(CORPUS_DIR.glob("doc-*.md")):
        out = mdx.transform(path.read_text(encoding="utf-8"))
        # Look only OUTSIDE fences — inside them, tags are legitimate content.
        for is_fence, seg in mdx._split_on_fences(out):
            if is_fence:
                continue
            for m in re.finditer(r"</?(Tabs?|Steps?|Note|Tip|Warning|Info|Accordion\w*|Card\w*|Frame|CodeGroup)\b", seg):
                leftovers.setdefault(path.name, []).append(m.group())

    assert not leftovers, f"component tags survived: {leftovers}"
