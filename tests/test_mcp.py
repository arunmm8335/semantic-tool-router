from __future__ import annotations

import sys
import unittest
from pathlib import Path

from semantic_tool_router.mcp import StdioMcpClient, estimate_tokens
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.router import ToolRouter


class McpClientTests(unittest.TestCase):
    def test_imports_and_calls_live_stdio_tools(self) -> None:
        server = Path(__file__).parent / "fixtures" / "fake_mcp_server.py"

        with StdioMcpClient([sys.executable, str(server)]) as client:
            snapshot = client.snapshot()
            result = client.call_tool("read_text_file", {"path": "README.md"})

        self.assertEqual(snapshot.name, "fake-filesystem")
        self.assertEqual([tool.name for tool in snapshot.tools], ["read_text_file", "delete_file"])
        self.assertEqual(snapshot.tools[0].permissions, ("read",))
        self.assertEqual(snapshot.tools[1].permissions, ("write", "destructive"))
        self.assertIn("called read_text_file", result["content"][0]["text"])

    def test_routes_over_imported_mcp_tools(self) -> None:
        server = Path(__file__).parent / "fixtures" / "fake_mcp_server.py"

        with StdioMcpClient([sys.executable, str(server)]) as client:
            snapshot = client.snapshot()

        results = ToolRouter(ToolRegistry(list(snapshot.tools))).discover(
            "read a local text file",
            top_k=1,
        )

        self.assertEqual(results[0].tool.name, "read_text_file")
        self.assertGreater(estimate_tokens(snapshot.raw_tools), 0)


if __name__ == "__main__":
    unittest.main()
