from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

SearchIndexMode = Literal[
    "description",
    "description_examples",
    "description_schema",
    "full",
]

SEARCH_INDEX_MODES: tuple[SearchIndexMode, ...] = (
    "description",
    "description_examples",
    "description_schema",
    "full",
)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    examples: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    cost: str = "local"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolSpec:
        required = ("name", "description")
        missing = [key for key in required if not data.get(key)]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Tool is missing required field(s): {joined}")

        return cls(
            name=str(data["name"]),
            description=str(data["description"]),
            input_schema=dict(data.get("input_schema", {})),
            examples=tuple(str(item) for item in data.get("examples", ())),
            tags=tuple(str(item) for item in data.get("tags", ())),
            permissions=tuple(str(item) for item in data.get("permissions", ())),
            cost=str(data.get("cost", "local")),
        )

    def searchable_text(self, mode: SearchIndexMode = "full") -> str:
        if mode == "description":
            return self.description

        parts = [self.description]
        if mode in ("description_examples", "full"):
            parts.append(" ".join(self.examples))
        if mode in ("description_schema", "full"):
            parts.append(" ".join(self.input_schema.keys()))
        if mode == "full":
            parts.extend(
                [
                    self.name,
                    " ".join(self.tags),
                    " ".join(self.permissions),
                    self.cost,
                ]
            )
        return " ".join(part for part in parts if part)


@dataclass(frozen=True)
class DiscoveryResult:
    tool: ToolSpec
    score: float
    reasons: tuple[str, ...] = ()
