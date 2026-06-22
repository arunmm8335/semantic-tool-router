from __future__ import annotations

from semantic_tool_router.embeddings import (
    EmbeddingProvider,
    HashingEmbeddingProvider,
    cosine_similarity,
)
from semantic_tool_router.models import DiscoveryResult, ToolSpec
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.reranker import Reranker


class ToolRouter:
    def __init__(
        self,
        registry: ToolRegistry,
        embedding_provider: EmbeddingProvider | None = None,
        reranker: Reranker | None = None,
        rerank_multiplier: int = 3,
    ) -> None:
        if rerank_multiplier < 1:
            raise ValueError("rerank_multiplier must be >= 1")
        self.registry = registry
        self.embedding_provider = embedding_provider or HashingEmbeddingProvider()
        self.reranker = reranker
        self.rerank_multiplier = rerank_multiplier
        self._tool_vectors = {
            tool.name: self.embedding_provider.embed(tool.searchable_text())
            for tool in self.registry.tools()
        }

    def discover(
        self,
        query: str,
        top_k: int = 5,
        require_tags: set[str] | None = None,
        allow_permissions: set[str] | None = None,
    ) -> list[DiscoveryResult]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        query_vector = self.embedding_provider.embed(query)
        results: list[DiscoveryResult] = []

        for tool in self.registry.tools():
            if require_tags and not require_tags.issubset(set(tool.tags)):
                continue
            if allow_permissions is not None and not set(tool.permissions).issubset(
                allow_permissions
            ):
                continue

            score = cosine_similarity(query_vector, self._tool_vectors[tool.name])
            if "deprecated" in tool.tags:
                score -= 0.25
            reasons = _reasons(query, tool)
            results.append(DiscoveryResult(tool=tool, score=score, reasons=tuple(reasons)))

        ranked = sorted(results, key=lambda item: item.score, reverse=True)
        if self.reranker is not None:
            candidate_pool = ranked[: max(top_k, top_k * self.rerank_multiplier)]
            ranked = self.reranker.rerank(query, candidate_pool)
            # Re-sort defensively: rerankers document that they return
            # score-ordered output, but the router's contract is that
            # callers always receive results sorted by score desc.
            ranked = sorted(ranked, key=lambda item: item.score, reverse=True)
        return ranked[:top_k]


def _reasons(query: str, tool: ToolSpec) -> list[str]:
    query_terms = {part.lower() for part in query.replace("-", " ").replace("_", " ").split()}
    tool_terms = set(tool.searchable_text().lower().replace("-", " ").replace("_", " ").split())
    overlap = sorted(query_terms & tool_terms)

    reasons = []
    if overlap:
        reasons.append(f"matched terms: {', '.join(overlap[:6])}")
    if tool.tags:
        reasons.append(f"tags: {', '.join(tool.tags)}")
    if tool.permissions:
        reasons.append(f"permissions: {', '.join(tool.permissions)}")
    return reasons
