from __future__ import annotations

import unittest

from semantic_tool_router.mcp_execution import minimal_tool_arguments, tool_call_succeeded


class McpExecutionTests(unittest.TestCase):
    def test_minimal_arguments_for_required_path(self) -> None:
        schema = {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        }
        arguments = minimal_tool_arguments(schema, workspace=".")
        self.assertIn("path", arguments)

    def test_tool_call_succeeded_false_on_is_error(self) -> None:
        self.assertFalse(tool_call_succeeded({"isError": True, "content": []}))

    def test_tool_call_succeeded_true_without_is_error(self) -> None:
        self.assertTrue(tool_call_succeeded({"content": [{"type": "text", "text": "ok"}]}))


if __name__ == "__main__":
    unittest.main()
