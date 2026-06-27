from __future__ import annotations

import unittest

from semantic_tool_router.bm25 import Bm25Index


class Bm25Tests(unittest.TestCase):
    def test_prefers_document_with_more_query_overlap(self) -> None:
        index = Bm25Index(
            {
                "search_files": "Recursively find files matching a glob pattern",
                "move_file": "Move or rename a file to a new location",
            }
        )
        scores = index.score_all("find every python source file recursively")
        self.assertGreater(scores["search_files"], scores["move_file"])

    def test_empty_query_returns_zero(self) -> None:
        index = Bm25Index({"tool_a": "example document"})
        self.assertEqual(index.score("", "tool_a"), 0.0)


if __name__ == "__main__":
    unittest.main()
