# Changelog

## Unreleased

- Added `compare-retrievers` CLI and `comparison.py` module to run frozen retriever comparisons across fixture and live MCP suites.
- Published retriever comparison results in `benchmarks/results/comparison.md` and `comparison.json`.
- Added GitHub issue templates (bug report, feature request) and a pull request template.
- Added `docs/benchmark-contributing.md` and `docs/workshop-paper-outline.md`.
- Updated README with positioning table, real CI badge, and comparison benchmark instructions.
- Updated `docs/research-plan.md` with retriever comparison results.
- Added an optional two-stage CrossEncoder reranker. The router now accepts a `Reranker`; when one is provided, the cheap embedding-similarity ranking produces a small candidate pool and the reranker rescores it before the final `top_k` is returned.
- Wired `--reranker cross-encoder` and `--reranker-model` into all four CLI subcommands.
- Added `examples/reranker_demo.py` end-to-end walkthrough.
- Added open-source community files: `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, and `SECURITY.md`.
- Added project URLs (Homepage, Issues, Changelog) and a real author record in `pyproject.toml`.
- Tightened `LICENSE` holder attribution.
- Added ruff and mypy configuration to `pyproject.toml` with a strict type-check profile scoped to the source package.
- Refreshed the LangChain and LlamaIndex integration examples with a graceful import-error fallback so the routing path runs on any Python version.
- Tidied docstrings and module headers across the source package and tests.

## 0.1.0-alpha - 2026-06-18

The first alpha research prototype. Tags: `v0.1.0-alpha`.

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