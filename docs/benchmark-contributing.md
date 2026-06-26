# Contributing Benchmarks

Benchmarks are first-class contributions in this project. A frozen task that exposes a retrieval failure is as valuable as a code fix.

## Two benchmark suites

| Suite | File | Purpose |
| --- | --- | --- |
| **Fixture** | `benchmarks/tasks.json` + `examples/tools.json` | Fast CI smoke test; 12 tools, 15 tasks |
| **Live MCP** | `benchmarks/live_mcp_suite.json` | Realistic routing against official MCP servers |

Prefer adding tasks to the **live MCP suite** when the failure only appears with real tool names and schemas.

## Writing a fixture task

Add an object to `benchmarks/tasks.json`:

```json
{
  "query": "natural language task phrasing a user might type",
  "expected_tools": ["tool_name_from_registry"]
}
```

Rules:

1. **Query** — Write how a user would ask, not how the tool is named internally.
2. **expected_tools** — Use exact `name` values from `examples/tools.json`. List multiple tools only when a task genuinely requires more than one.
3. **No leakage** — Do not copy tool names verbatim into the query unless a real user would ("run python tests" is fine; "call python_unittest" is not).
4. **One intent per task** — Split compound workflows into separate tasks.

After adding a task, register the tool in `examples/tools.json` if it does not exist yet.

## Writing a live MCP task

Edit `benchmarks/live_mcp_suite.json`. Each server block has:

```json
{
  "id": "filesystem",
  "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "{workspace}"],
  "tasks": [
    {
      "query": "Find every Python source file under this project recursively",
      "expected_tools": ["search_files"]
    }
  ]
}
```

Rules:

1. **expected_tools** — Must match names returned by `tools/list` on that server version.
2. **Independent phrasing** — Tasks should not share boilerplate across servers.
3. **Nontrivial preference** — Prioritize servers with many similar tools (filesystem, memory) over single-tool servers.
4. **Document failures** — If a task consistently fails with the default hashing retriever, note it in your PR; that is useful signal.

## Verifying your change

```bash
# Fast fixture check (runs in CI)
python -m semantic_tool_router benchmark \
  --registry examples/tools.json \
  --tasks benchmarks/tasks.json \
  --top-k 3

# Full retriever comparison (fixture only, no MCP servers)
python -m semantic_tool_router compare-retrievers --fixture-only

# Live MCP suite (requires Node.js / npx)
python -m semantic_tool_router mcp-benchmark \
  --suite benchmarks/live_mcp_suite.json \
  --workspace .
```

Include before/after metrics in your pull request when retrieval rankings change.

## Metrics reference

| Metric | Meaning |
| --- | --- |
| `hit_rate@k` | At least one expected tool appears in top-k |
| `top_1_accuracy` | The first result is an expected tool |
| `mrr` | Mean reciprocal rank of the first relevant tool |
| `mean_recall@k` | Fraction of expected tools recovered per task |
| `mean_precision@k` | Fraction of retrieved tools that are relevant |
| `context_tokens_saved` | Estimated prompt tokens avoided vs dumping all tools |

See also [research-plan.md](research-plan.md) and [results/comparison.md](../benchmarks/results/comparison.md).
