# Workshop Paper Outline

**Working title:** *Semantic Tool Router: Reproducible, Permission-Aware Retrieval for MCP Agent Toolsets*

**Target venues:** MLSys workshop, EMNLP Industry Track demo, arXiv technical report, or MCP / agent-systems meetup proceedings.

---

## 1. Abstract (150 words)

- Problem: MCP and agent frameworks expose growing tool catalogs; full-schema injection wastes context and hurts selection.
- Contribution: An open-source library with frozen benchmarks, permission-aware filtering, and live MCP evaluation.
- Results: On 15 live MCP tasks across 4 servers, hashing achieves 73% hit@3; MiniLM reaches 87%; cross-encoder reranking reaches 93%.
- Claim: Reproducible infrastructure and honest baselines matter more than a single SOTA number.

## 2. Introduction

- The many-tool problem in agentic LLM systems.
- Gap: Most benchmarks pre-annotate relevant tools; production must retrieve from hundreds.
- Position this work as **systems + evaluation**, not a new foundation model.

## 3. Related Work

| Work | Relationship |
| --- | --- |
| ToolRet (ACL 2025) | Large-scale retrieval benchmark; we are smaller but MCP-live |
| LiveMCPBench | Real MCP servers; complementary scale |
| GRETEL | Execution-based reranking; future direction for us |
| MCP-Zero | Query rewriting + dense retrieval |
| Tool-to-Agent Retrieval | Agent-level vs tool-level retrieval |

## 4. System Design

- `ToolSpec` registry model (description, schema, tags, permissions).
- Two-stage retrieval: embedding similarity → optional cross-encoder rerank.
- Permission gating (`read`, `write`, `destructive`, `network`).
- MCP stdio client: `tools/list` import, guarded execution.

Include architecture diagram from README.

## 5. Benchmarks

### 5.1 Fixture suite

- 12 tools, 15 tasks (`examples/tools.json`, `benchmarks/tasks.json`).
- Saturates at 100% for all retrievers — useful for CI, not for ranking methods.

### 5.2 Live MCP suite

- 4 official servers: Filesystem, Memory, Sequential Thinking, Everything.
- 15 independently phrased tasks.
- Report all-tasks and nontrivial-task metrics (exclude single-tool servers).

### 5.3 Metrics

- hit@k, top-1, MRR, context token savings.
- Planned: `unsafe_activation_rate`, downstream agent pass rate.

## 6. Experiments

### Experiment 1 — Retriever comparison (completed)

| Config | Live hit@3 | Live top-1 | Live MRR |
| --- | ---: | ---: | ---: |
| Hashing | 73.3% | 40.0% | 0.556 |
| MiniLM | 86.7% | 66.7% | 0.744 |
| Hashing + cross-encoder | 93.3% | 80.0% | 0.856 |
| MiniLM + cross-encoder | 93.3% | 80.0% | 0.856 |

### Experiment 2 — Retrieval input ablation (planned)

- Description only vs +examples vs +schema vs full metadata.

### Experiment 3 — Permission gating (planned)

- Measure `unsafe_activation_rate` with and without `allow_permissions`.

### Experiment 4 — Downstream agent eval (planned)

- Fixed LLM selects tool from retrieved top-k; measure task success.

## 7. Failure Analysis

Use per-task failures from `benchmarks/results/live_mcp_baseline.md`:

- Memory server: destructive tools ranked above `read_graph` / `search_nodes` with hashing.
- Filesystem: `search_files` missed when query lacks lexical overlap.
- Cross-encoder fixes most memory failures; `create_relations` remains hard.

## 8. Discussion

- Semantic similarity ≠ functional correctness (cite GRETEL).
- When top-k routing is enough vs when full tool dump is fine (<10 tools).
- Limitations: 15 tasks, English only, stdio MCP only.

## 9. Conclusion

- Release reproducible benchmark + library.
- Call for community task contributions.

## 10. Artifact checklist

- [ ] GitHub repo public with frozen `benchmarks/`
- [ ] `compare-retrievers` CLI documented
- [ ] `comparison.md` committed with dated results
- [ ] One end-to-end demo (query → discover → MCP execute)
- [ ] Optional: Hugging Face dataset card for task JSON

## Appendix A — Reproduction commands

```bash
pip install -e ".[sentence-transformers]"
python -m semantic_tool_router compare-retrievers \
  --registry examples/tools.json \
  --tasks benchmarks/tasks.json \
  --suite benchmarks/live_mcp_suite.json \
  --markdown-output benchmarks/results/comparison.md
```
