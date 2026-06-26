# Retriever Comparison

Generated: `2026-06-26T08:12:06Z`

Frozen-task comparison across embedding and reranking configurations. Reproduce with:

```bash
python -m semantic_tool_router compare-retrievers \
  --registry examples/tools.json \
  --tasks benchmarks/tasks.json \
  --suite benchmarks/live_mcp_suite.json \
  --markdown-output benchmarks/results/comparison.md
```

## Fixture benchmark (JSON registry)

Registry: `examples/tools.json`  
Tasks: `benchmarks/tasks.json`  
Tasks: 15 | top-k: 3

| Config | Hit rate@k | Top-1 | MRR | Mean recall@k | Mean precision@k |
| --- | ---: | ---: | ---: | ---: | ---: |
| hashing | 100.0% | 100.0% | 1.000 | 96.7% | 33.3% |
| sentence-transformers (all-MiniLM-L6-v2) | 100.0% | 100.0% | 1.000 | 100.0% | 35.6% |
| hashing + cross-encoder | 100.0% | 100.0% | 1.000 | 96.7% | 33.3% |
| sentence-transformers + cross-encoder | 100.0% | 100.0% | 1.000 | 100.0% | 35.6% |

The fixture suite is small (12 tools, 15 tasks) and may saturate at 100%. Use the live MCP suite below for meaningful retriever differences.

## Live MCP benchmark

Suite: `benchmarks/live_mcp_suite.json`  
Tasks: 15 across 4 official MCP servers  
Nontrivial tasks: 13 (servers with more than one tool)

### All tasks

| Config | Hit rate@3 | Top-1 | MRR | Context saved |
| --- | ---: | ---: | ---: | ---: |
| hashing | 73.3% | 40.0% | 0.556 | 62.0% |
| sentence-transformers (all-MiniLM-L6-v2) | 86.7% | 66.7% | 0.744 | 62.1% |
| hashing + cross-encoder | 93.3% | 80.0% | 0.856 | 61.4% |
| sentence-transformers + cross-encoder | 93.3% | 80.0% | 0.856 | 61.2% |

### Nontrivial tasks only

| Config | Hit rate@3 | Top-1 | MRR |
| --- | ---: | ---: | ---: |
| hashing | 69.2% | 30.8% | 0.487 |
| sentence-transformers (all-MiniLM-L6-v2) | 84.6% | 61.5% | 0.705 |
| hashing + cross-encoder | 92.3% | 76.9% | 0.833 |
| sentence-transformers + cross-encoder | 92.3% | 76.9% | 0.833 |

## Takeaways

- **Hashing** is fast and dependency-free but weaker on live MCP tool names that do not overlap lexically with the query.
- **Sentence-transformers (MiniLM)** improves live hit rate substantially without a reranker.
- **Cross-encoder reranking** recovers additional memory-server tasks where first-stage retrieval ranks destructive tools too high.
- Context savings (~62%) are stable across retrievers because top-k is fixed.
