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

Run tests:

```powershell
python -m unittest discover -s tests
```

If you do not want to install the package yet, run commands with `PYTHONPATH=src`.

## Project Shape

- `src/semantic_tool_router/models.py` defines tool metadata and discovery results.
- `src/semantic_tool_router/registry.py` loads and validates JSON tool registries.
- `src/semantic_tool_router/embeddings.py` provides a local hashing embedder.
- `src/semantic_tool_router/router.py` ranks tools with cosine similarity and filters.
- `src/semantic_tool_router/cli.py` exposes discovery and benchmark commands.

## Research Questions

- How much context can dynamic tool discovery save compared with static tool exposure?
- Do descriptions, schemas, examples, or tags contribute most to retrieval quality?
- When does a cheap local retriever need an LLM reranker?
- How should permission and safety metadata affect ranking?
