from __future__ import annotations

from typing import Protocol

from semantic_tool_router.models import DiscoveryResult


class Reranker(Protocol):
    """Re-orders an already-retrieved candidate list using a more expensive model.

    Implementations should return candidates in score-descending order. The
    router will re-sort defensively, so a correct order is not strictly
    required, but emitting sorted output is the documented contract.
    """

    def rerank(self, query: str, candidates: list[DiscoveryResult]) -> list[DiscoveryResult]: ...


class CrossEncoderReranker:
    """Rerank candidates using a sentence-transformers CrossEncoder.

    The CrossEncoder scores each (query, tool_description) pair jointly, which is
    much more accurate than the dot-product of independent embeddings but is
    expensive enough that it should only be run on a small candidate pool
    produced by a cheaper first-stage retriever.
    """

    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as err:
            raise ImportError(
                "sentence-transformers is required to use CrossEncoderReranker. "
                "Install it with `pip install semantic-tool-router[sentence-transformers]`"
            ) from err
        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: list[DiscoveryResult]) -> list[DiscoveryResult]:
        if not candidates:
            return []
        pairs = [(query, _candidate_text(item)) for item in candidates]
        scores = self.model.predict(pairs)
        scored = [
            DiscoveryResult(tool=item.tool, score=float(score), reasons=item.reasons)
            for item, score in zip(candidates, scores, strict=True)
        ]
        return sorted(scored, key=lambda item: item.score, reverse=True)


def _candidate_text(result: DiscoveryResult) -> str:
    parts = [result.tool.name, result.tool.description]
    if result.tool.examples:
        parts.append("Examples: " + " ".join(result.tool.examples))
    if result.tool.tags:
        parts.append("Tags: " + " ".join(result.tool.tags))
    return " ".join(parts)
