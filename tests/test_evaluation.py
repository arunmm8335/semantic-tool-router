from __future__ import annotations

import unittest

from semantic_tool_router.evaluation import BenchmarkTask, evaluate
from semantic_tool_router.models import ToolSpec
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.router import ToolRouter


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        registry = ToolRegistry(
            [
                ToolSpec(name="read_file", description="Read local project files"),
                ToolSpec(name="web_search", description="Search the public web"),
                ToolSpec(name="run_tests", description="Run Python unit tests"),
            ]
        )
        self.router = ToolRouter(registry)

    def test_rank_aware_metrics(self) -> None:
        tasks = [
            BenchmarkTask(query="read a local project file", expected_tools=("read_file",)),
            BenchmarkTask(query="search the public web", expected_tools=("web_search",)),
        ]

        report = evaluate(self.router, tasks, top_k=2)

        self.assertEqual(report.task_count, 2)
        self.assertEqual(report.hit_rate, 1.0)
        self.assertEqual(report.top_1_accuracy, 1.0)
        self.assertEqual(report.mean_reciprocal_rank, 1.0)
        self.assertEqual(report.mean_recall, 1.0)
        self.assertEqual(report.mean_precision, 0.5)

    def test_task_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing a query"):
            BenchmarkTask.from_dict({"expected_tools": ["read_file"]})

        with self.assertRaisesRegex(ValueError, "no expected tools"):
            BenchmarkTask.from_dict({"query": "read a file"})


if __name__ == "__main__":
    unittest.main()
