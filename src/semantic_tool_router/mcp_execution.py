from __future__ import annotations

from pathlib import Path
from typing import Any

from semantic_tool_router.mcp import McpError, StdioMcpClient


def tool_call_succeeded(result: dict[str, Any]) -> bool:
    if result.get("isError") is True:
        return False
    return True


def is_destructive_tool(raw_tool: dict[str, Any]) -> bool:
    annotations = raw_tool.get("annotations", {})
    if not isinstance(annotations, dict):
        return False
    return annotations.get("destructiveHint") is True


def minimal_tool_arguments(
    schema: dict[str, Any],
    *,
    workspace: str | Path | None = None,
    query: str = "",
) -> dict[str, Any]:
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}
    required = schema.get("required", [])
    if not isinstance(required, list):
        required = []

    workspace_path = Path(workspace).resolve() if workspace else Path.cwd()
    readme = workspace_path / "README.md"
    default_path = str(readme) if readme.exists() else str(workspace_path)

    arguments: dict[str, Any] = {}
    for key in required:
        if not isinstance(key, str):
            continue
        prop = properties.get(key, {})
        if not isinstance(prop, dict):
            prop = {}
        arguments[key] = _default_value(
            key,
            prop,
            workspace_path=workspace_path,
            default_path=default_path,
            query=query,
        )
    return arguments


def execute_selected_tool(
    client: StdioMcpClient,
    *,
    tool_name: str,
    raw_tool: dict[str, Any] | None,
    workspace: str | Path | None,
    query: str,
    arguments: dict[str, Any] | None = None,
) -> tuple[bool, str | None]:
    if raw_tool is None:
        return False, f"Tool {tool_name!r} was not found in the server snapshot"

    schema = raw_tool.get("inputSchema", {})
    if not isinstance(schema, dict):
        schema = {}

    if arguments is None:
        arguments = minimal_tool_arguments(schema, workspace=workspace, query=query)

    try:
        result = client.call_tool(tool_name, arguments)
    except McpError as error:
        return False, str(error)

    if tool_call_succeeded(result):
        return True, None
    return False, "MCP tool call returned isError=true"


def _default_value(
    key: str,
    prop: dict[str, Any],
    *,
    workspace_path: Path,
    default_path: str,
    query: str,
) -> Any:
    lowered = key.lower()
    prop_type = prop.get("type")

    if lowered in {"path", "filepath", "file"}:
        return default_path
    if lowered in {"message", "text", "input", "prompt"}:
        return query or "test"
    if lowered == "topic":
        return query or "semantic tool routing"
    if lowered == "thought":
        return query or "Breaking the problem into steps."
    if lowered == "nextthoughtneeded":
        return True
    if lowered in {"thoughtnumber", "totalthoughts"}:
        return 1
    if lowered in {"a", "b", "x", "y", "left", "right"}:
        return 1
    if lowered == "entities":
        return [
            {
                "name": "benchmark-suite",
                "entityType": "project",
                "observations": ["Used for routing evaluation"],
            }
        ]
    if lowered == "relations":
        return [
            {
                "from": "benchmark-suite",
                "to": "semantic-tool-router",
                "relationType": "depends_on",
            }
        ]
    if lowered == "observations":
        return [{"entityName": "benchmark-suite", "contents": ["evaluation run"]}]
    if prop_type == "boolean":
        return False
    if prop_type == "integer":
        return 1
    if prop_type == "number":
        return 1.0
    if prop_type == "array":
        return []
    if prop_type == "object":
        return {}
    return query or "test"
