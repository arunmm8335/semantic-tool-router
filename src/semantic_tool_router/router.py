from __future__ import annotations

from semantic_tool_router.bm25 import Bm25Index
from semantic_tool_router.embeddings import (
    EmbeddingProvider,
    HashingEmbeddingProvider,
    cosine_similarity,
)
from semantic_tool_router.models import DiscoveryResult, SearchIndexMode, ToolSpec
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.reranker import Reranker
from semantic_tool_router.scoring import safety_penalty


class ToolRouter:
    def __init__(
        self,
        registry: ToolRegistry,
        embedding_provider: EmbeddingProvider | None = None,
        reranker: Reranker | None = None,
        rerank_multiplier: int = 3,
        hybrid_bm25_weight: float = 0.4,
        safety_penalty_enabled: bool = True,
        safety_penalty_amount: float = 0.2,
        index_mode: SearchIndexMode = "full",
    ) -> None:
        if rerank_multiplier < 1:
            raise ValueError("rerank_multiplier must be >= 1")
        if not 0.0 <= hybrid_bm25_weight <= 1.0:
            raise ValueError("hybrid_bm25_weight must be between 0 and 1")
        if safety_penalty_amount < 0:
            raise ValueError("safety_penalty_amount must be >= 0")

        self.registry = registry
        self.embedding_provider = embedding_provider or HashingEmbeddingProvider()
        self.reranker = reranker
        self.rerank_multiplier = rerank_multiplier
        self.hybrid_bm25_weight = hybrid_bm25_weight
        self.safety_penalty_enabled = safety_penalty_enabled
        self.safety_penalty_amount = safety_penalty_amount
        self.index_mode = index_mode

        tools = list(self.registry.tools())
        self._tool_vectors = {
            tool.name: self.embedding_provider.embed(tool.searchable_text(index_mode))
            for tool in tools
        }
        self._bm25: Bm25Index | None = None
        if hybrid_bm25_weight > 0.0 and tools:
            documents = {tool.name: tool.searchable_text(index_mode) for tool in tools}
            self._bm25 = Bm25Index(documents)

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
        candidates = [
            tool
            for tool in self.registry.tools()
            if (not require_tags or require_tags.issubset(set(tool.tags)))
            and (allow_permissions is None or set(tool.permissions).issubset(allow_permissions))
        ]

        bm25_scores = self._bm25.score_all(query) if self._bm25 is not None else {}
        max_bm25 = max(bm25_scores.values(), default=0.0)
        if max_bm25 <= 0.0:
            max_bm25 = 1.0

        results: list[DiscoveryResult] = []
        for tool in candidates:
            embedding_score = cosine_similarity(query_vector, self._tool_vectors[tool.name])
            bm25_score = bm25_scores.get(tool.name, 0.0) / max_bm25
            weight = self.hybrid_bm25_weight
            score = ((1.0 - weight) * embedding_score) + (weight * bm25_score)

            if "deprecated" in tool.tags:
                score -= 0.25

            penalty = 0.0
            if self.safety_penalty_enabled:
                penalty = safety_penalty(
                    query,
                    tool,
                    amount=self.safety_penalty_amount,
                )
                score -= penalty

            reasons = _reasons(query, tool, bm25_score=bm25_score, penalty=penalty)
            results.append(DiscoveryResult(tool=tool, score=score, reasons=tuple(reasons)))

        ranked = sorted(results, key=lambda item: item.score, reverse=True)
        if self.reranker is not None:
            candidate_pool = ranked[: max(top_k, top_k * self.rerank_multiplier)]
            ranked = self.reranker.rerank(query, candidate_pool)
            ranked = sorted(ranked, key=lambda item: item.score, reverse=True)
        return ranked[:top_k]


def _reasons(
    query: str,
    tool: ToolSpec,
    *,
    bm25_score: float,
    penalty: float,
) -> list[str]:
    query_terms = {part.lower() for part in query.replace("-", " ").replace("_", " ").split()}
    tool_terms = set(
        tool.searchable_text("full").lower().replace("-", " ").replace("_", " ").split()
    )
    overlap = sorted(query_terms & tool_terms)

    reasons = []
    if overlap:
        reasons.append(f"matched terms: {', '.join(overlap[:6])}")
    if bm25_score > 0:
        reasons.append(f"bm25: {bm25_score:.3f}")
    if penalty > 0:
        reasons.append(f"safety penalty: -{penalty:.2f}")
    if tool.tags:
        reasons.append(f"tags: {', '.join(tool.tags)}")
    if tool.permissions:
        reasons.append(f"permissions: {', '.join(tool.permissions)}")
    return reasons
