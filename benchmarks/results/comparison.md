# Retriever Comparison

Generated: `2026-06-27T14:54:07Z`

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
Tasks: 51 across 4 official MCP servers  
Nontrivial tasks: 46 (servers with more than one tool)

### All tasks

| Config | Hit rate@3 | Top-1 | MRR | Context saved |
| --- | ---: | ---: | ---: | ---: |
| hashing | 82.4% | 60.8% | 0.703 | 62.0% |
| sentence-transformers (all-MiniLM-L6-v2) | 92.2% | 78.4% | 0.843 | 64.6% |
| hashing + cross-encoder | 92.2% | 80.4% | 0.853 | 63.8% |
| sentence-transformers + cross-encoder | 90.2% | 80.4% | 0.846 | 64.3% |
| BGE-small (bge-small-en-v1.5) | 94.1% | 84.3% | 0.889 | 64.5% |
| BGE-small + cross-encoder | 90.2% | 80.4% | 0.846 | 64.2% |

### Nontrivial tasks only

| Config | Hit rate@3 | Top-1 | MRR |
| --- | ---: | ---: | ---: |
| hashing | 80.4% | 56.5% | 0.670 |
| sentence-transformers (all-MiniLM-L6-v2) | 91.3% | 76.1% | 0.826 |
| hashing + cross-encoder | 91.3% | 78.3% | 0.837 |
| sentence-transformers + cross-encoder | 89.1% | 78.3% | 0.830 |
| BGE-small (bge-small-en-v1.5) | 93.5% | 82.6% | 0.877 |
| BGE-small + cross-encoder | 89.1% | 78.3% | 0.830 |

## Takeaways

- **BGE-small** reaches 94.1% hit@3 / 84.3% top-1 on the 51-task live MCP suite.
- **MiniLM + cross-encoder** (quality profile) reaches 90.2% hit@3 / 80.4% top-1.
- **Hashing + BM25** reaches 82.4% hit@3 — fast, zero-deps, CI-friendly.
- Context savings (~63%) are stable across retrievers because top-k is fixed.

