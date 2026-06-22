"""
Example showing how to use a two-stage retriever with a CrossEncoder reranker.

The first stage is a cheap embedding-based retriever (HashingEmbeddingProvider
by default) that produces a small candidate pool. The second stage is a more
accurate (and more expensive) CrossEncoderReranker that re-scores the pool
jointly against the query.

Install the optional dependency with:
    pip install "semantic-tool-router[sentence-transformers]"

Run with:
    python examples/reranker_demo.py "debug a failing CI run on GitHub"
"""

from __future__ import annotations

import sys
from pathlib import Path

from semantic_tool_router import (
    CrossEncoderReranker,
    HashingEmbeddingProvider,
    ToolRegistry,
    ToolRouter,
)


def main(query: str | None = None) -> int:
    if query is None:
        query = "debug a failing CI run on GitHub"

    registry_path = Path(__file__).parent / "tools.json"
    registry = ToolRegistry.from_file(str(registry_path))

    # First-stage embedder: cheap, fast, no extra deps. The CrossEncoder
    # reranks only the top candidates, so the embedder quality matters
    # less than recall on the candidate pool.
    embedder = HashingEmbeddingProvider()

    # Second-stage reranker: a sentence-transformers CrossEncoder that
    # scores (query, tool_description) pairs jointly.
    try:
        reranker = CrossEncoderReranker()
    except ImportError as error:
        print(f"Skipping reranker demo: {error}")
        return 1

    router = ToolRouter(
        registry,
        embedding_provider=embedder,
        reranker=reranker,
        rerank_multiplier=3,
    )

    # top_k=3, rerank_multiplier=3 -> the reranker scores the top 9 candidates.
    results = router.discover(query, top_k=3)

    print(f"Query: {query}\n")
    print(f"Reranked top-{len(results)} tools (out of {len(registry)}):")
    for index, result in enumerate(results, start=1):
        print(f" {index}. {result.tool.name} (score: {result.score:.3f})")
        print(f"    {result.tool.description}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
