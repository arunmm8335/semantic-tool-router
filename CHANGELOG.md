# Changelog

## 0.2.0 - 2026-06-27

- Added hybrid BM25 + embedding fusion with read-query safety penalties.
- Added `--profile quality` (MiniLM + cross-encoder) and `--profile fast` (hashing + BM25).
- Per-profile BM25 defaults: **0.4 for fast**, **0.0 for quality** (semantic embedders no longer diluted).
- Added `compare-retrievers` CLI, expanded live MCP benchmark to 28 tasks, and GitHub issue templates.
- Published on [PyPI](https://pypi.org/project/semantic-tool-router/).

## 0.1.0 - 2026-06-18

The first alpha research prototype.

- Added the first semantic tool discovery router.
- Added a dependency-light hashing embedder for local retrieval.
- Added JSON tool registry loading and validation.
- Added CLI commands for discovery and benchmarking.
- Added a sample registry, benchmark tasks, and unit tests.
- Added an initial research plan for evaluating dynamic tool retrieval.
- Added reusable rank-aware benchmark evaluation (hit rate, top-1 accuracy, MRR, mean recall, mean precision).
- Expanded the example registry to 12 tools and the benchmark to 15 tasks.
- Added JSON benchmark output and GitHub Actions CI for Python 3.10-3.12.
- Added import and ranking of tools from live stdio MCP servers.
- Added guarded MCP tool execution and a real filesystem-server demo.
- Added a reproducible four-server live MCP benchmark and baseline report.
