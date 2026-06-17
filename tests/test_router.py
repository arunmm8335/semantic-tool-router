from __future__ import annotations

import unittest

from semantic_tool_router.models import ToolSpec
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.router import ToolRouter


class ToolRouterTests(unittest.TestCase):
    def test_discovers_relevant_tool(self) -> None:
        registry = ToolRegistry(
            [
                ToolSpec(
                    name="github_fetch_workflow_logs",
                    description="Fetch GitHub Actions workflow logs for failing CI jobs.",
                    examples=("debug failed continuous integration",),
                    tags=("github", "ci"),
                    permissions=("network",),
                ),
                ToolSpec(
                    name="image_generate",
                    description="Generate bitmap images from prompts.",
                    tags=("image",),
                    permissions=("network",),
                ),
            ]
        )

        results = ToolRouter(registry).discover("debug failing github ci logs", top_k=1)

        self.assertEqual(results[0].tool.name, "github_fetch_workflow_logs")

    def test_tag_filter(self) -> None:
        registry = ToolRegistry(
            [
                ToolSpec(name="read_file", description="Read a local file", tags=("local",)),
                ToolSpec(name="web_search", description="Search the web", tags=("network",)),
            ]
        )

        results = ToolRouter(registry).discover("search", require_tags={"network"})

        self.assertEqual([result.tool.name for result in results], ["web_search"])

    def test_permission_filter(self) -> None:
        registry = ToolRegistry(
            [
                ToolSpec(name="read_file", description="Read a local file", permissions=("read",)),
                ToolSpec(name="run_shell", description="Run a shell command", permissions=("execute",)),
            ]
        )

        results = ToolRouter(registry).discover("run command", allow_permissions={"read"})

        self.assertEqual([result.tool.name for result in results], ["read_file"])


if __name__ == "__main__":
    unittest.main()

