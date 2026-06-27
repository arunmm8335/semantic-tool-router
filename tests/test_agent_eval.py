from __future__ import annotations

import unittest

from semantic_tool_router.agent_eval import LexicalSelector, RankOneSelector, evaluate_agent
from semantic_tool_router.evaluation import BenchmarkTask
from semantic_tool_router.models import ToolSpec
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.router import ToolRouter


class AgentEvalTests(unittest.TestCase):
    def test_rank_one_selector_end_to_end(self) -> None:
        registry = ToolRegistry(
            [
                ToolSpec(
                    name="github_fetch_workflow_logs",
                    description="Fetch GitHub Actions workflow logs for failing CI jobs.",
                    examples=("debug failed continuous integration",),
                ),
                ToolSpec(
                    name="image_generate",
                    description="Generate bitmap images from prompts.",
                ),
            ]
        )
        router = ToolRouter(registry)
        tasks = (
            BenchmarkTask(
                query="debug failing github ci logs",
                expected_tools=("github_fetch_workflow_logs",),
            ),
        )
        report = evaluate_agent(
            router,
            tasks,
            top_k=1,
            selector=RankOneSelector(),
            selector_name="rank1",
        )
        self.assertEqual(report.end_to_end_success_rate, 1.0)

    def test_lexical_selector_picks_overlap(self) -> None:
        selector = LexicalSelector()
        from semantic_tool_router.models import DiscoveryResult

        candidates = (
            DiscoveryResult(
                tool=ToolSpec(name="move_file", description="Move a file"),
                score=0.9,
            ),
            DiscoveryResult(
                tool=ToolSpec(name="search_files", description="Search files recursively"),
                score=0.8,
            ),
        )
        selected = selector.select("find python files recursively", candidates)
        self.assertEqual(selected, "search_files")


if __name__ == "__main__":
    unittest.main()
