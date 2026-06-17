# Research Plan

## Hypothesis

Agents can select tools more reliably and use less prompt context when tools are retrieved dynamically from a structured registry instead of injected all at once.

## MVP Evaluation

The first benchmark measures recall at `k`: whether at least one expected tool appears in the top retrieved results for a task.

```powershell
python -m semantic_tool_router benchmark --registry examples/tools.json --tasks benchmarks/tasks.json --top-k 3
```

## Next Experiments

1. Compare retrieval inputs: description only, description plus examples, description plus schema, and all metadata.
2. Compare retrievers: keyword BM25, local hashing embeddings, sentence-transformer embeddings, hosted embeddings, and LLM reranking.
3. Measure context savings: tokens for all tools versus tokens for retrieved tools.
4. Add safety scoring: penalize tools with network, write, execute, or destructive permissions unless the task clearly needs them.
5. Build MCP import: convert MCP tool schemas into registry entries automatically.

## Metrics

- `recall@k`: expected tool appears in top-k results.
- `mrr`: expected tool rank quality.
- `context_tokens_saved`: estimated prompt tokens avoided.
- `unsafe_activation_rate`: privileged tools selected when not needed.
- `fallback_rate`: agent needed a tool that retrieval did not expose.

