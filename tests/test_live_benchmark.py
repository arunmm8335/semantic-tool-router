from __future__ import annotations

import unittest

from semantic_tool_router.live_benchmark import (
    LiveServerCase,
    LiveTask,
    _evaluate_server,
    render_markdown,
)
from semantic_tool_router.mcp import McpServerSnapshot
from semantic_tool_router.models import ToolSpec


class LiveBenchmarkTests(unittest.TestCase):
    def test_evaluates_server_and_renders_markdown(self) -> None:
        raw_tools = (
            {
                "name": "read_file",
                "description": "Read a local file",
                "inputSchema": {"type": "object"},
            },
            {
                "name": "send_email",
                "description": "Send an email message",
                "inputSchema": {"type": "object"},
            },
        )
        snapshot = McpServerSnapshot(
            name="fake",
            version="1.0",
            tools=(
                ToolSpec(name="read_file", description="Read a local file"),
                ToolSpec(name="send_email", description="Send an email message"),
            ),
            raw_tools=raw_tools,
        )
        case = LiveServerCase(
            identifier="fake",
            command=("fake",),
            tasks=(LiveTask("read a local file", ("read_file",)),),
        )

        server = _evaluate_server(case, snapshot, top_k=1)
        report = {
            "generated_at": "2026-06-19T00:00:00+00:00",
            "top_k": 1,
            "server_count": 1,
            "task_count": 1,
            "metrics": server["metrics"],
            "nontrivial_task_count": 1,
            "nontrivial_metrics": server["metrics"],
            "servers": [server],
        }

        self.assertEqual(server["metrics"]["hit_rate"], 1.0)
        self.assertIn("Live MCP Baseline", render_markdown(report))


if __name__ == "__main__":
    unittest.main()
