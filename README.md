# Semantic Tool Router

> Status: `0.1.0-alpha` research prototype.

Semantic Tool Router is a small, dependency-light prototype for discovering the right tools for an agent at runtime.

Instead of exposing every available tool to a model, it stores tool metadata in a registry, embeds each tool from its description and examples, and retrieves a focused set of candidate tools for the current task.

## Why

Agent systems are quickly gaining more tools, plugins, and MCP servers than can fit cleanly into one prompt. This project explores whether a lightweight retrieval layer can reduce context size while improving tool selection.

The current release uses a simple local hashing embedder. That makes the prototype easy to run and inspect, while leaving space for stronger embedding models and rerankers.

## Quick Start

Install the package in editable mode:

```powershell
python -m pip install -e .
```

Discover tools for a task:

```powershell
python -m semantic_tool_router discover "find open pull requests with failing CI" --registry examples/tools.json
```

Run the benchmark:

```powershell
python -m semantic_tool_router benchmark --registry examples/tools.json --tasks benchmarks/tasks.json
```

Get machine-readable metrics:

```powershell
python -m semantic_tool_router benchmark --registry examples/tools.json --tasks benchmarks/tasks.json --json
```

Run tests:

```powershell
python -m unittest discover -s tests
```

## Live MCP Demo

The live demo starts the official filesystem MCP server, imports its tool
schemas at runtime, retrieves three read-only tools, and executes the
highest-ranked tool against this repository:

```powershell
powershell -ExecutionPolicy Bypass -File examples/live_mcp_demo.ps1
```

Expected behavior:

- Connect to the real `@modelcontextprotocol/server-filesystem` process.
- Import its current tools through MCP `tools/list`.
- Select `read_text_file` from a natural-language task.
- Show estimated tool-schema context savings.
- Execute `read_text_file` and print the first lines of this README.

Node.js and `npx` are required. The server is granted access only to the
current project directory. Execution requires both explicit arguments and an
`--expect-tool` guard; the command aborts if a different tool ranks first.

Use any stdio MCP server with the generic command:

```powershell
python -m semantic_tool_router mcp-discover "your task" --top-k 3 --server <command> <args>
```

If you do not want to install the package yet, run commands with `PYTHONPATH=src`.

## Project Shape

- `src/semantic_tool_router/models.py` defines tool metadata and discovery results.
- `src/semantic_tool_router/registry.py` loads and validates JSON tool registries.
- `src/semantic_tool_router/embeddings.py` provides a local hashing embedder.
- `src/semantic_tool_router/router.py` ranks tools with cosine similarity and filters.
- `src/semantic_tool_router/evaluation.py` computes rank-aware retrieval metrics.
- `src/semantic_tool_router/mcp.py` imports tools from live stdio MCP servers.
- `src/semantic_tool_router/cli.py` exposes discovery and benchmark commands.

Every push and pull request runs the unit tests and benchmark on Python 3.10,
3.11, and 3.12 through GitHub Actions.

## Research Questions

- How much context can dynamic tool discovery save compared with static tool exposure?
- Do descriptions, schemas, examples, or tags contribute most to retrieval quality?
- When does a cheap local retriever need an LLM reranker?
- How should permission and safety metadata affect ranking?
