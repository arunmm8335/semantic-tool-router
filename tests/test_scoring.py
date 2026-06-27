from __future__ import annotations

import unittest

from semantic_tool_router.models import ToolSpec
from semantic_tool_router.scoring import query_intent, safety_penalty


class ScoringTests(unittest.TestCase):
    def test_read_query_penalizes_destructive_tools(self) -> None:
        tool = ToolSpec(
            name="delete_entities",
            description="Delete entities from the knowledge graph",
            permissions=("write", "destructive"),
        )
        self.assertGreater(
            safety_penalty("show the complete stored knowledge graph", tool),
            0.0,
        )

    def test_write_query_does_not_penalize_create_tools(self) -> None:
        tool = ToolSpec(
            name="create_relations",
            description="Create relations between entities",
            permissions=("write",),
        )
        self.assertEqual(
            safety_penalty("connect the router project to the research topic", tool),
            0.0,
        )

    def test_query_intent_classification(self) -> None:
        self.assertEqual(query_intent("show the complete stored knowledge graph"), "read")
        self.assertEqual(query_intent("remember a new collaborator"), "write")


if __name__ == "__main__":
    unittest.main()
