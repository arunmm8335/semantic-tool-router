# Downstream Agent Evaluation

Generated: `2026-06-27`

Simulated agent policies after retrieval (top-k=3):

| Router profile | Selector | Retrieval hit@3 | Agent success | End-to-end success |
| --- | --- | ---: | ---: | ---: |
| quality (MiniLM + cross-encoder) | rank1 | 100.0% | 100.0% | 100.0% |
| fast (hashing + BM25) | rank1 | 100.0% | 100.0% | 100.0% |

The JSON fixture suite (15 tasks, 12 tools) saturates at 100%. Use the live MCP
suite for meaningful downstream gaps between retrieval and agent selection.

## Selectors

| Selector | Behavior |
| --- | --- |
| `rank1` | Agent always picks the highest-ranked retrieved tool |
| `lexical` | Agent picks the candidate with strongest query term overlap |

## Reproduce

```bash
# Quality stack + rank-1 agent
python -m semantic_tool_router agent-eval \
  --registry examples/tools.json \
  --tasks benchmarks/tasks.json \
  --profile quality \
  --selector rank1 \
  --json

# Lexical agent simulation
python -m semantic_tool_router agent-eval \
  --registry examples/tools.json \
  --tasks benchmarks/tasks.json \
  --profile quality \
  --selector lexical
```

## Interpretation

- **Retrieval hit@k** — expected tool appears in retrieved top-k
- **Agent success** — simulated agent picks an expected tool from top-k
- **End-to-end success** — both retrieval and agent selection succeed

When retrieval hit@k > agent success, the bottleneck is agent reasoning—not routing.
