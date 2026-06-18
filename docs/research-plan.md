# Research Plan

## Hypothesis

Agents can select tools more reliably and use less prompt context when tools are retrieved dynamically from a structured registry instead of injected all at once.

## Evaluation

The benchmark reports hit rate, top-1 accuracy, mean reciprocal rank, mean
recall, and mean precision. Per-task ranked results make retrieval errors
visible instead of reducing the experiment to one pass/fail number.

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

- `hit_rate@k`: fraction of tasks with at least one relevant result in top-k.
- `top_1_accuracy`: fraction of tasks whose first result is relevant.
- `mean_recall@k`: fraction of expected tools recovered per task.
- `mean_precision@k`: fraction of retrieved tools that are relevant.
- `mrr`: reciprocal rank of the first relevant tool, averaged across tasks.
- `context_tokens_saved`: estimated prompt tokens avoided.
- `unsafe_activation_rate`: privileged tools selected when not needed.
- `fallback_rate`: agent needed a tool that retrieval did not expose.
