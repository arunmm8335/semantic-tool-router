from __future__ import annotations

import unittest

from semantic_tool_router.ablation import run_input_ablation
from semantic_tool_router.models import ToolSpec


class SearchIndexModeTests(unittest.TestCase):
    def test_searchable_text_modes_differ(self) -> None:
        tool = ToolSpec(
            name="github_search_prs",
            description="Search pull requests by repository.",
            input_schema={"repository": "owner/name", "query": "text"},
            examples=("find open pull requests",),
            tags=("github",),
            permissions=("network",),
        )
        description = tool.searchable_text("description")
        with_examples = tool.searchable_text("description_examples")
        with_schema = tool.searchable_text("description_schema")
        full = tool.searchable_text("full")

        self.assertEqual(description, "Search pull requests by repository.")
        self.assertIn("find open pull requests", with_examples)
        self.assertIn("repository", with_schema)
        self.assertIn("github_search_prs", full)
        self.assertLess(len(description), len(full))


class AblationTests(unittest.TestCase):
    def test_run_input_ablation_on_fixture(self) -> None:
        results = run_input_ablation(
            "examples/tools.json",
            "benchmarks/tasks.json",
            top_k=3,
        )
        self.assertEqual(len(results), 4)
        for item in results:
            self.assertIn("index_mode", item)
            self.assertIn("hit_rate@3", item["metrics"])


if __name__ == "__main__":
    unittest.main()
