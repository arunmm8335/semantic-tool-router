from __future__ import annotations

from semantic_tool_router.embeddings import tokenize
from semantic_tool_router.models import ToolSpec

READ_QUERY_TERMS = frozenset(
    {
        "browse",
        "display",
        "find",
        "get",
        "inspect",
        "list",
        "look",
        "open",
        "read",
        "retrieve",
        "search",
        "show",
        "view",
        "what",
        "which",
    }
)

WRITE_QUERY_TERMS = frozenset(
    {
        "add",
        "associate",
        "connect",
        "create",
        "delete",
        "edit",
        "link",
        "move",
        "record",
        "register",
        "remember",
        "remove",
        "rename",
        "run",
        "schedule",
        "send",
        "start",
        "store",
        "trigger",
        "update",
        "write",
    }
)


def effective_permissions(tool: ToolSpec) -> set[str]:
    permissions = set(tool.permissions)
    name = tool.name.lower().replace("-", "_")

    if name.startswith(("delete_", "remove_")):
        permissions.update({"destructive", "write"})
    elif name.startswith(("create_", "add_", "edit_", "move_", "write_")):
        permissions.add("write")
    elif name.startswith(("read_", "get_", "list_", "search_", "open_")):
        permissions.add("read")

    return permissions


def query_intent(query: str) -> str:
    terms = set(tokenize(query))
    if terms & WRITE_QUERY_TERMS:
        return "write"
    if terms & READ_QUERY_TERMS:
        return "read"
    return "neutral"


def safety_penalty(query: str, tool: ToolSpec, *, amount: float = 0.2) -> float:
    """Penalize risky tools when the query looks read-only."""
    if query_intent(query) != "read":
        return 0.0

    permissions = effective_permissions(tool)
    penalty = 0.0
    if "destructive" in permissions:
        penalty += amount
    elif "execute" in permissions:
        penalty += amount
    elif "write" in permissions and "read" not in permissions:
        penalty += amount * 0.5
    return penalty
