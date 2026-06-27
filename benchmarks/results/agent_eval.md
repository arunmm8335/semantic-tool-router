# Downstream Agent Evaluation

Generated: `2026-06-27`

## Live MCP (51 tasks, `--profile bge`, rank1 selector)

| Metric | Value |
| --- | ---: |
| Retrieval hit@3 | 98.0% |
| Agent success | 92.2% |
| End-to-end success | 92.2% |

Full per-task results: [agent_eval_live.md](agent_eval_live.md)

## Fixture suite (15 tasks)

| Router profile | Selector | Retrieval hit@3 | Agent success | End-to-end |
| --- | --- | ---: | ---: | ---: |
| quality (MiniLM + cross-encoder) | rank1 | 100.0% | 100.0% | 100.0% |
| fast (hashing + BM25) | rank1 | 100.0% | 100.0% | 100.0% |

The JSON fixture saturates at 100%. Live MCP evaluation is the meaningful benchmark.

## Reproduce

```bash
python -m semantic_tool_router agent-eval \
  --live \
  --suite benchmarks/live_mcp_suite.json \
  --profile bge \
  --selector rank1 \
  --markdown-output benchmarks/results/agent_eval_live.md
```

## Interpretation

When **retrieval hit@3 > agent success**, the bottleneck is agent selection—not routing.
With rank1 selector on BGE, both metrics match (92.2%), meaning failures are retrieval misses, not agent reasoning.
