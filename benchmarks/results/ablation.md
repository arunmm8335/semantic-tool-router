# Retrieval Input Ablation

Generated: `2026-06-27T14:47:43Z`

Registry: `examples/tools.json`  
Tasks: `benchmarks/tasks.json`  
Embedder: hashing (BM25 weight 0.4)

| Index mode | Hit rate@k | Top-1 | MRR |
| --- | ---: | ---: | ---: |
| `description` | 100.0% | 100.0% | 1.000 |
| `description_examples` | 100.0% | 100.0% | 1.000 |
| `description_schema` | 100.0% | 100.0% | 1.000 |
| `full` | 100.0% | 100.0% | 1.000 |

Reproduce:

```bash
python -m semantic_tool_router ablation \
  --registry examples/tools.json \
  --tasks benchmarks/tasks.json \
  --markdown-output benchmarks/results/ablation.md
```

