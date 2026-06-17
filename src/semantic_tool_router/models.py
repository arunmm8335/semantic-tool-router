from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    def from_dict(cls, data: dict[str, Any]) -> "ToolSpec":
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

    def searchable_text(self) -> str:
        schema_keys = " ".join(self.input_schema.keys())
        return " ".join(
            part
            for part in (
                self.name,
                self.description,
                " ".join(self.examples),
                " ".join(self.tags),
                " ".join(self.permissions),
                schema_keys,
                self.cost,
            )
            if part
        )


@dataclass(frozen=True)
class DiscoveryResult:
    tool: ToolSpec
    score: float
    reasons: tuple[str, ...] = ()

