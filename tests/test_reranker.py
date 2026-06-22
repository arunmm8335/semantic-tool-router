from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from semantic_tool_router.models import DiscoveryResult, ToolSpec
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.reranker import Reranker
from semantic_tool_router.router import ToolRouter


class _UnsortedReranker:
    """A reranker that returns candidates in input order with scrambled scores.

    Used to verify the router's contract that the final results are always
    sorted by score desc, even if a reranker returns its output unsorted.
    Also used to spy on the candidate pool size passed to the reranker.
    """

    def rerank(self, query: str, candidates: list[DiscoveryResult]) -> list[DiscoveryResult]:
        # Assign scores in a way that does NOT match the input order, and
        # return the candidates unsorted to exercise the router's re-sort.
        scrambled = [3.0, 0.0, 1.0, 2.0]
        return [
            DiscoveryResult(tool=item.tool, score=scrambled[index], reasons=item.reasons)
            for index, item in enumerate(candidates)
        ]


class RerankerProtocolTests(unittest.TestCase):
    def test_reranker_protocol_satisfied(self) -> None:
        reranker: Reranker = _UnsortedReranker()
        self.assertTrue(callable(getattr(reranker, "rerank", None)))

    def test_router_uses_reranker_when_provided(self) -> None:
        registry = ToolRegistry(
            [
                ToolSpec(name="alpha", description="alpha tool"),
                ToolSpec(name="bravo", description="bravo tool"),
                ToolSpec(name="charlie", description="charlie tool"),
            ]
        )

        # A reranker that assigns scores in reverse of the input order
        # (last input item gets the highest score). The router sorts by
        # score desc, so the final order flips compared to the baseline.
        class _ScoreReversingReranker:
            def rerank(self, query, candidates):
                return [
                    DiscoveryResult(tool=item.tool, score=float(index), reasons=item.reasons)
                    for index, item in enumerate(candidates)
                ]

        baseline = ToolRouter(registry).discover("alpha", top_k=3)
        baseline_names = [item.tool.name for item in baseline]

        reranked = ToolRouter(registry, reranker=_ScoreReversingReranker()).discover(
            "alpha", top_k=3
        )
        reranked_names = [item.tool.name for item in reranked]

        self.assertEqual(baseline_names, list(reversed(reranked_names)))

    def test_reranker_receives_top_k_times_multiplier_candidates(self) -> None:
        registry = ToolRegistry(
            [ToolSpec(name=f"tool_{i}", description=f"description number {i}") for i in range(10)]
        )
        spy = MagicMock(wraps=_UnsortedReranker())
        ToolRouter(registry, reranker=spy, rerank_multiplier=2).discover("query", top_k=2)

        spy.rerank.assert_called_once()
        candidates = spy.rerank.call_args.kwargs.get("candidates") or spy.rerank.call_args.args[1]
        self.assertEqual(len(candidates), 4)

    def test_router_without_reranker_unchanged(self) -> None:
        registry = ToolRegistry(
            [
                ToolSpec(
                    name="github_fetch_workflow_logs",
                    description="Fetch GitHub Actions workflow logs for failing CI jobs.",
                ),
                ToolSpec(name="image_generate", description="Generate bitmap images from prompts."),
            ]
        )

        results = ToolRouter(registry).discover("debug failing github ci logs", top_k=1)
        self.assertEqual(results[0].tool.name, "github_fetch_workflow_logs")

    def test_router_resorts_reranker_output_by_score(self) -> None:
        # The router must re-sort reranker output by score desc, even if
        # the reranker returns results out of order.
        registry = ToolRegistry(
            [
                ToolSpec(name="alpha", description="alpha tool"),
                ToolSpec(name="bravo", description="bravo tool"),
                ToolSpec(name="charlie", description="charlie tool"),
                ToolSpec(name="delta", description="delta tool"),
            ]
        )

        results = ToolRouter(registry, reranker=_UnsortedReranker()).discover("alpha", top_k=4)
        scores = [item.score for item in results]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
