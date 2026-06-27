from __future__ import annotations

from semantic_tool_router.models import ToolSpec

# Routing phrases keyed by normalized MCP tool name (underscore form).
_MCP_ROUTING_PHRASES: dict[str, tuple[str, ...]] = {
    "create_entities": (
        "remember a new person or entity",
        "store a new collaborator",
        "create a node in the knowledge graph",
    ),
    "create_relations": (
        "link two entities together",
        "connect a project to a research topic",
        "associate an author with a paper",
        "record a dependency between concepts",
    ),
    "search_nodes": (
        "find anything previously remembered",
        "search memory for stored nodes",
        "look up entities by keyword",
    ),
    "open_nodes": (
        "open an entity record by name",
        "fetch a specific stored node",
    ),
    "read_graph": (
        "show the complete knowledge graph",
        "display everything currently in memory",
        "browse the full stored graph",
    ),
    "add_observations": (
        "add another fact to an existing entity",
        "attach a note to a stored person",
    ),
    "delete_observations": (
        "remove an outdated note",
        "delete an observation from an entity",
    ),
    "delete_relations": (
        "delete a relationship that is no longer true",
        "remove an incorrect link between entities",
    ),
    "delete_entities": (
        "remove an entity added by mistake",
        "delete a stored node from memory",
    ),
    "search_files": (
        "find files recursively by pattern",
        "search the project for matching paths",
    ),
    "list_directory": (
        "list files and folders in a directory",
        "show directory contents",
    ),
    "read_text_file": (
        "open and read a text file",
        "show the contents of a project file",
    ),
    "move_file": (
        "move or rename a file",
        "relocate a file to another folder",
    ),
    "edit_file": (
        "edit or patch a text file",
        "update lines inside a file",
    ),
    "trigger_long_running_operation": (
        "start a long running background task",
        "kick off an async operation",
    ),
}


def _normalize_name(name: str) -> str:
    return name.lower().replace("-", "_")


def enrichment_phrases(tool_name: str) -> tuple[str, ...]:
    return _MCP_ROUTING_PHRASES.get(_normalize_name(tool_name), ())


def enrich_tool_spec(tool: ToolSpec) -> ToolSpec:
    phrases = enrichment_phrases(tool.name)
    if not phrases:
        return tool
    merged = tuple(dict.fromkeys((*tool.examples, *phrases)))
    return ToolSpec(
        name=tool.name,
        description=tool.description,
        input_schema=tool.input_schema,
        examples=merged,
        tags=tool.tags,
        permissions=tool.permissions,
        cost=tool.cost,
    )
