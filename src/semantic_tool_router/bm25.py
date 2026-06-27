from __future__ import annotations

import math
from collections import Counter

from semantic_tool_router.embeddings import tokenize


class Bm25Index:
    """Okapi BM25 index for lexical tool retrieval."""

    def __init__(
        self,
        documents: dict[str, str],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if not documents:
            raise ValueError("documents cannot be empty")
        if k1 <= 0:
            raise ValueError("k1 must be positive")
        if not 0.0 <= b <= 1.0:
            raise ValueError("b must be between 0 and 1")

        self.k1 = k1
        self.b = b
        self._doc_tokens = {doc_id: tokenize(text) for doc_id, text in documents.items()}
        self._doc_freqs = {doc_id: Counter(tokens) for doc_id, tokens in self._doc_tokens.items()}
        self._doc_lengths = {doc_id: len(tokens) for doc_id, tokens in self._doc_tokens.items()}
        doc_count = len(self._doc_tokens)
        self._avg_doc_length = sum(self._doc_lengths.values()) / doc_count

        term_doc_count: Counter[str] = Counter()
        for freqs in self._doc_freqs.values():
            for term in freqs:
                term_doc_count[term] += 1

        self._idf = {
            term: math.log(1.0 + (doc_count - count + 0.5) / (count + 0.5))
            for term, count in term_doc_count.items()
        }

    def score(self, query: str, doc_id: str) -> float:
        query_terms = tokenize(query)
        if not query_terms:
            return 0.0

        doc_freqs = self._doc_freqs[doc_id]
        doc_length = self._doc_lengths[doc_id]
        length_norm = 1.0 - self.b + self.b * (doc_length / self._avg_doc_length)
        total = 0.0

        for term in query_terms:
            if term not in doc_freqs:
                continue
            term_freq = doc_freqs[term]
            idf = self._idf.get(term, 0.0)
            numerator = term_freq * (self.k1 + 1.0)
            denominator = term_freq + self.k1 * length_norm
            total += idf * (numerator / denominator)

        return total

    def score_all(self, query: str) -> dict[str, float]:
        return {doc_id: self.score(query, doc_id) for doc_id in self._doc_tokens}
