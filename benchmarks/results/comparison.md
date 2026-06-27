# Retriever Comparison

Generated: `2026-06-27T09:25:19Z`

Frozen-task comparison across embedding and reranking configurations. Reproduce with:

```bash
python -m semantic_tool_router compare-retrievers \
  --registry examples/tools.json \
  --tasks benchmarks/tasks.json \
  --suite benchmarks/live_mcp_suite.json \
  --markdown-output benchmarks/results/comparison.md
```

## Live MCP benchmark

Suite: `benchmarks/live_mcp_suite.json`  
Tasks: 28 across 4 official MCP servers  
Nontrivial tasks: 26 (servers with more than one tool)

### All tasks

| Config | Hit rate@3 | Top-1 | MRR | Context saved |
| --- | ---: | ---: | ---: | ---: |
| hashing | 78.6% | 46.4% | 0.601 | 63.0% |
| sentence-transformers (all-MiniLM-L6-v2) | 89.3% | 67.9% | 0.768 | 65.0% |
| hashing + cross-encoder | 85.7% | 75.0% | 0.792 | 65.5% |
| sentence-transformers + cross-encoder | 85.7% | 75.0% | 0.792 | 65.4% |

### Nontrivial tasks only

| Config | Hit rate@3 | Top-1 | MRR |
| --- | ---: | ---: | ---: |
| hashing | 76.9% | 42.3% | 0.571 |
| sentence-transformers (all-MiniLM-L6-v2) | 88.5% | 65.4% | 0.750 |
| hashing + cross-encoder | 84.6% | 73.1% | 0.776 |
| sentence-transformers + cross-encoder | 84.6% | 73.1% | 0.776 |

## Takeaways

- **Per-embedder BM25 tuning**: 40% for hashing, 0% for semantic embedders; MiniLM hit@3 reaches 89.3%.
- **Cross-encoder reranking** (quality profile) reaches 85.7% hit@3 / 75.0% top-1.
- Context savings (~64%) are stable across retrievers because top-k is fixed.

