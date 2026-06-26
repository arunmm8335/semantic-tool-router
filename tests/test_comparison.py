from __future__ import annotations

import unittest

from semantic_tool_router.comparison import render_comparison_markdown


class ComparisonMarkdownTests(unittest.TestCase):
    def test_render_includes_fixture_and_live_tables(self) -> None:
        fixture = [
            {
                "config": "hashing",
                "metrics": {
                    "task_count": 15,
                    "top_k": 3,
                    "hit_rate@3": 1.0,
                    "top_1_accuracy": 1.0,
                    "mrr": 1.0,
                    "mean_recall@3": 1.0,
                    "mean_precision@3": 0.33,
                },
            }
        ]
        live = [
            {
                "config": "hashing",
                "task_count": 15,
                "nontrivial_task_count": 13,
                "metrics": {
                    "hit_rate": 0.733,
                    "top_1_accuracy": 0.4,
                    "mrr": 0.556,
                    "mean_context_saved": 0.62,
                },
                "nontrivial_metrics": {
                    "hit_rate": 0.692,
                    "top_1_accuracy": 0.308,
                    "mrr": 0.487,
                },
            }
        ]
        markdown = render_comparison_markdown(fixture, live)
        self.assertIn("Fixture benchmark", markdown)
        self.assertIn("Live MCP benchmark", markdown)
        self.assertIn("hashing", markdown)


if __name__ == "__main__":
    unittest.main()
