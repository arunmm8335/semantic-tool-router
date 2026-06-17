from __future__ import annotations

import json
from pathlib import Path

from semantic_tool_router.models import ToolSpec


class ToolRegistry:
    def __init__(self, tools: list[ToolSpec]) -> None:
        names = [tool.name for tool in tools]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            joined = ", ".join(duplicates)
            raise ValueError(f"Duplicate tool name(s): {joined}")
        self._tools = tuple(tools)

    @classmethod
    def from_file(cls, path: str | Path) -> "ToolRegistry":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("tools", [])
        if not isinstance(data, list):
            raise ValueError("Registry must be a list or an object with a 'tools' list")
        return cls([ToolSpec.from_dict(item) for item in data])

    def tools(self) -> tuple[ToolSpec, ...]:
        return self._tools

