"""Turn the docs' MDX components into plain prose.

Text in, text out. This module knows nothing about chunks, vectors, or models —
that separation is what lets its rules be tested on their own.

WHY NOT JUST DELETE EVERY TAG
-----------------------------
A single regex that strips `<Anything>` would be three lines and would be wrong.
Two of these components carry meaning in their structure:

  <Tabs>  says "these are ALTERNATIVES — pick one"
  <Steps> says "these are SEQUENTIAL — do them in order"

Strip the tags blindly and three mutually exclusive install methods concatenate
into what reads like one procedure: "run the npm install, then the Homebrew
install, then the native install." That chunk is not noisy, it is FALSE. If it
gets retrieved and cited, it asserts something untrue. That is a correctness bug
wearing a preprocessing costume, and it is why this file is longer than a regex.

The rest of the components (<Note>, <Tip>, <Warning>, <Card>, ...) really are
presentational, so those tags get dropped and their contents kept.

WHY WE SKIP CODE FENCES
-----------------------
Measured on this corpus: 0 capitalized MDX components appear inside code fences,
but 46 lowercase HTML tags (<div>, <span>) DO — they are examples being
documented. Rewriting those would corrupt the code samples, so every rule here
runs only on the text between fences.
"""

import re

# Components that are pure decoration: drop the tag, keep whatever is inside.
# <CodeGroup> is here because the ``` fences inside it already delimit the code.
PRESENTATIONAL = (
    "Note", "Tip", "Warning", "Info", "Check", "Danger",
    "CodeGroup", "CardGroup", "Frame", "Columns", "Expandable",
)
# NOTE: "Card" is deliberately NOT in that list. It carries a title= attribute
# that is a visible heading on the docs page, so dropping the whole tag would
# leave an orphaned description with no subject - see _flatten_cards below.

# Raw HTML used for layout in the source. Dropped OUTSIDE fences only.
HTML_LAYOUT = ("div", "span", "br", "p", "img", "a")


# --------------------------------------------------------- FENCE PROTECTION --

def _split_on_fences(text: str) -> list[tuple[bool, str]]:
    """Break text into (is_fence, segment) pairs.

    Returns segments in order, so "".join(segment for _, segment) rebuilds the
    original exactly. That property matters: this module must never lose a
    character, and the caller relies on being able to reassemble.
    """
    # Find fence delimiters: ``` at the start of a line. Pair them up — the
    # first is an opener, the second its closer, and so on.
    marks = [m.start() for m in re.finditer(r"^```", text, re.M)]

    segments, pos = [], 0
    # Step through the marks two at a time: marks[i] opens, marks[i+1] closes.
    for i in range(0, len(marks) - 1, 2):
        open_at, close_at = marks[i], marks[i + 1]
        # Everything before this fence is ordinary text...
        if open_at > pos:
            segments.append((False, text[pos:open_at]))
        # ...and the fence itself runs to the END of its closing line, so the
        # trailing ``` is included rather than leaking into the next segment.
        line_end = text.find("\n", close_at)
        line_end = len(text) if line_end == -1 else line_end + 1
        segments.append((True, text[open_at:line_end]))
        pos = line_end

    # Whatever is left after the last complete fence. An unclosed trailing ```
    # ends up here as ordinary text, which is the safe way to fail.
    if pos < len(text):
        segments.append((False, text[pos:]))
    return segments


# -------------------------------------------------------- STRUCTURAL RULES --

def _flatten_tabs(text: str) -> str:
    """<Tab title="npm"> ... </Tab>  ->  "Alternative (npm): ..."

    The word "Alternative" is doing real work. It is the only thing left in the
    plain text telling a reader — or an embedding model — that these blocks are
    a choice rather than a sequence.
    """
    # Named tab: keep the title, which is usually the thing a user searches for
    # ("npm", "Homebrew", "Windows").
    text = re.sub(r'<Tab\s+title="([^"]*)"[^>]*>', r"\nAlternative (\1):\n", text)
    # Tab with no title still needs the alternative-ness marked.
    text = re.sub(r"<Tab(?:\s[^>]*)?>", "\nAlternative:\n", text)
    text = re.sub(r"</Tabs?>", "", text)
    # The <Tabs> wrapper itself carries no text once its children are labelled.
    text = re.sub(r"<Tabs(?:\s[^>]*)?>", "", text)
    return text


def _flatten_steps(text: str) -> str:
    """<Step title="Install"> ... -> "1. Install"

    Numbering restarts inside each <Steps> block, which is why this cannot be a
    plain re.sub — the replacement depends on how many steps came before it in
    THIS block.
    """
    def number_one_block(match: re.Match) -> str:
        body = match.group(1)
        counter = 0

        def number_step(step: re.Match) -> str:
            nonlocal counter
            counter += 1
            title = step.group(1) or step.group(2) or ""
            return f"\n{counter}. {title}\n" if title else f"\n{counter}.\n"

        # Handle titled and untitled <Step> in one pass so the counter stays
        # in sync across both forms.
        body = re.sub(
            r'<Step\s+title="([^"]*)"[^>]*>|<Step(?:\s[^>]*)?>()',
            number_step,
            body,
        )
        return re.sub(r"</Step>", "", body)

    # DOTALL so a <Steps> block can span many lines, non-greedy so two adjacent
    # blocks don't get swallowed into one.
    text = re.sub(r"<Steps(?:\s[^>]*)?>(.*?)</Steps>", number_one_block, text, flags=re.S)

    # Any <Step> outside a <Steps> wrapper: unwrap it, but keep the title, since
    # an unnumbered step is still a named piece of a procedure.
    text = re.sub(r'<Step\s+title="([^"]*)"[^>]*>', r"\n\1\n", text)
    text = re.sub(r"</?Steps?(?:\s[^>]*)?>", "", text)
    return text


def _flatten_accordions(text: str) -> str:
    """<Accordion title="Why does this happen?"> -> the title as a heading.

    Accordion titles are disproportionately valuable here: they are usually
    phrased as the question a user would actually ask, which is exactly the
    text a query has to match.
    """
    text = re.sub(r'<Accordion\s+title="([^"]*)"[^>]*>', r"\n\1\n", text)
    text = re.sub(r"</?Accordion(?:Group)?(?:\s[^>]*)?>", "", text)
    return text


def _drop_mdx_comments(text: str) -> str:
    """Remove {/* ... */} build directives.

    These are invisible on the rendered docs page - they are instructions to the
    docs build system, like {/* min-version: 2.1.207 */} or
    {/* plan-availability: feature=loop-dynamic */}. 228 of them appear across
    12% of the chunks, and they cost tokens while carrying nothing a user could
    ask about.

    Safe to drop: where the version information actually matters, the page
    restates it in prose immediately afterwards ("Before v2.1.207, ..."), so the
    fact survives in a form a question can match.

    Measured: all 228 sit outside code fences and none spans a line break. This
    only ever runs on non-fenced segments anyway, so a code example containing
    the same syntax would be left alone.
    """
    return re.sub(r"\{/\*.*?\*/\}", "", text, flags=re.S)


def _flatten_cards(text: str) -> str:
    """<Card title="Best practices" icon="star" href="..."> -> "Best practices"

    Cards are the "explore more" tiles at the foot of a docs page. The title is
    the visible heading; the body is a one-line description. Dropping the tag
    wholesale left the description stranded with no subject:

        Get better results with effective prompting and project setup

    which no query for "best practices" could ever match, even though the card
    is literally a link to that page. `icon` and `href` really are decoration
    and stay dropped.
    """
    text = re.sub(r'<Card\s+[^>]*?title="([^"]*)"[^>]*>', r"\n\1\n", text)
    text = re.sub(r"</?Card(?:Group)?(?:\s[^>]*)?>", "", text)
    return text


def _drop_wrapper_tags(text: str) -> str:
    """Remove decoration tags, keep their contents."""
    for tag in PRESENTATIONAL:
        text = re.sub(rf"</?{tag}(?:\s[^>]*)?>", "", text)
    for tag in HTML_LAYOUT:
        # re.I because raw HTML in docs is inconsistently cased.
        text = re.sub(rf"</?{tag}(?:\s[^>]*)?>", "", text, flags=re.I)
    return text


# ----------------------------------------------------------------- PUBLIC --

def transform(text: str) -> str:
    """Apply every D4 rule to the prose, leaving code fences untouched."""
    out = []
    for is_fence, segment in _split_on_fences(text):
        if is_fence:
            out.append(segment)          # verbatim — 46 HTML examples live here
            continue
        # Order matters: the structural rules read `title=` attributes, so they
        # must run before _drop_wrapper_tags removes anything tag-shaped.
        segment = _drop_mdx_comments(segment)
        segment = _flatten_tabs(segment)
        segment = _flatten_steps(segment)
        segment = _flatten_accordions(segment)
        segment = _flatten_cards(segment)
        segment = _drop_wrapper_tags(segment)
        out.append(segment)
    return "".join(out)
