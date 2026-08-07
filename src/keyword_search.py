"""BM25 Okapi over the same 1,637 chunks the dense index holds.

Import:  from keyword_search import BM25Index

WHY THIS IS WRITTEN OUT RATHER THAN INSTALLED
---------------------------------------------
`rank_bm25` is four lines to install and PLAN.md permits it. Two reasons not
to. Nothing in this venv provides it and there is no network here, so it would
block Day 9 outright. And requirements.txt exists to pin the code that turns
frozen data into numbers, on the argument that an unpinned minor version can
move every metric with no hash to catch it; adding a dependency to compute the
comparison variant is the one place that argument bites hardest.

It is also 40 lines. The formula is the deliverable, not the package.

THE FORMULA, AND WHERE THE 0.5s GO
----------------------------------
    idf(q)   = ln(1 + (N - n(q) + 0.5) / (n(q) + 0.5))
    score(D) = sum over query terms of
                 idf(q) * f(q,D) * (k1 + 1)
                 / (f(q,D) + k1 * (1 - b + b * |D| / avgdl))

k1 = 1.2 and b = 0.75, the standard defaults, chosen rather than tuned. Tuning
them against this gold set would fit the variant to the 24 questions it is
about to be measured on, and Day 11's confidence interval would then be a
statement about a retriever that had already seen the answers.

The `1 +` inside the logarithm is the Okapi form and it is load-bearing here.
Without it a term appearing in more than half the corpus gets a negative idf,
and a chunk can be penalised for containing "the". This corpus is 30 pages of
one product's documentation, so words like "claude", "code", "run" and "file"
are everywhere, and half the gold questions are mostly those words. The Okapi
form is why no stopword list is needed, which is one fewer hand-written list
to justify.

WHY IT INDEXES text_embed
-------------------------
The dense side embeds `text_embed`, so the keyword side scores the same text.
Any difference between the two variants is then a difference of scoring
method, which is the thing Day 11 has to attribute a confidence interval to.
Indexing `text_raw` here would make the comparison partly about MDX markup.

Labels are still written against `text_raw`. That rule is about what a human
reads when deciding what is gold, and it is untouched by this.
"""

import math
from collections import Counter

from leakage import tokenise

K1 = 1.2
B = 0.75


class BM25Index:
    """A scorer over a fixed list of chunks. Built once, queried many times.

    The tokeniser is imported from leakage.py rather than rewritten. It is the
    one that already knows `settings.json` is two tokens and `claude-code` is
    two more, it has 13 tests behind it, and using a different one here would
    mean the retriever cannot match the vocabulary D6 measured.
    """

    def __init__(self, chunks: list[dict]):
        if not chunks:
            raise ValueError("BM25Index needs at least one chunk")

        self.ids = [c["id"] for c in chunks]
        self.tokens = [tokenise(c["text_embed"]) for c in chunks]
        self.freqs = [Counter(t) for t in self.tokens]
        self.lengths = [len(t) for t in self.tokens]
        self.avgdl = sum(self.lengths) / len(self.lengths)
        self.n_docs = len(chunks)

        self.doc_freq: Counter = Counter()
        for tokens in self.tokens:
            self.doc_freq.update(set(tokens))

    def idf(self, term: str) -> float:
        """Okapi inverse document frequency. Never negative, see the header."""
        n = self.doc_freq.get(term, 0)
        return math.log(1 + (self.n_docs - n + 0.5) / (n + 0.5))

    def score(self, query: str) -> dict[str, float]:
        """BM25 score of every chunk against `query`, keyed by chunk ID.

        Every chunk gets an entry, including the ones scoring 0.0. Fusion
        needs a rank for each, and a chunk missing from this dict would be
        indistinguishable from one the query genuinely did not match.
        """
        terms = tokenise(query)
        scores = {chunk_id: 0.0 for chunk_id in self.ids}
        if not terms:
            return scores

        for term in terms:
            if term not in self.doc_freq:
                continue
            idf = self.idf(term)
            for i, chunk_id in enumerate(self.ids):
                f = self.freqs[i].get(term, 0)
                if not f:
                    continue
                norm = 1 - B + B * self.lengths[i] / self.avgdl
                scores[chunk_id] += idf * f * (K1 + 1) / (f + K1 * norm)
        return scores

    def search(self, query: str, top: int | None = 10) -> list[str]:
        """Chunk IDs best first. `top=None` returns the whole index.

        Ties break by chunk ID, the same convention run_retrieval.py pins for
        the dense side. Four groups of chunks in this index have identical
        text and therefore identical scores, and two retrievers that broke
        those ties differently would disagree for reasons that have nothing to
        do with retrieval.
        """
        scores = self.score(query)
        ranked = sorted(self.ids, key=lambda cid: (-scores[cid], cid))
        return ranked if top is None else ranked[:top]
