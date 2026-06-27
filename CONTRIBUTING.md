# Contributing to Semantic Tool Router

Thanks for your interest in contributing! This project aims to make tool routing for AI agents predictable, measurable, and cheap.

## Code of Conduct

By participating, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before posting issues, pull requests, or comments.

## Ways to contribute

- **Bug reports** — open an issue using the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml).
- **Feature requests** — open an issue using the [feature request template](.github/ISSUE_TEMPLATE/feature_request.yml). Explain the use case, not just the implementation.
- **Documentation** — README, docstrings, examples, and `docs/` improvements are always welcome.
- **New embedders or rerankers** — see the architecture section below.
- **Benchmarks** — adding new retrieval tasks or new live MCP servers to the suite. See [docs/benchmark-contributing.md](docs/benchmark-contributing.md).

## Development setup

```bash
git clone https://github.com/arunmm8335/semantic-tool-router.git
cd semantic-tool-router
python -m venv .venv
source .venv/bin/activate   # or: .venv\Scripts\activate on Windows
pip install -e ".[sentence-transformers,openai]"
pip install ruff mypy
```

If you only want to run the core tests, `pip install -e .` is enough.

## Running tests

```bash
python -m unittest discover -s tests -v
```

The test suite uses `unittest` only — no extra test runner required. Tests include a fake stdio MCP server fixture (`tests/fixtures/fake_mcp_server.py`) that exercises the real protocol rather than only mocking it.

## Running the benchmark

```bash
python -m semantic_tool_router benchmark \
  --registry examples/tools.json \
  --tasks benchmarks/tasks.json \
  --top-k 3
```

When changing the retriever, rerun the benchmark and include before/after numbers in your PR description.

## Code style

- **Formatter**: `ruff format src tests examples`
- **Linter**: `ruff check src tests examples`
- **Type checker**: `mypy src/semantic_tool_router`
- All three run in CI; PRs will not merge if any fail.

The codebase uses `from __future__ import annotations` and full type hints on all public functions. New public functions should include a one-line docstring.

## Pull request process

1. Fork and create a topic branch (`feature/...`, `fix/...`, `docs/...`).
2. Make focused commits. Avoid mixing refactors with behavior changes.
3. Ensure `ruff format`, `ruff check`, `mypy`, the unit tests, and the benchmark all pass.
4. Update `CHANGELOG.md` under the `Unreleased` section.
5. Open a PR using the pull request template. Reference the issue it closes.

## Architecture overview

```
ToolRouter
├── ToolRegistry        (loads JSON or MCP-imported ToolSpecs)
├── EmbeddingProvider   (hashing | sentence-transformers | openai)
├── Bm25Index           (hybrid lexical fusion, default 40% weight)
├── scoring             (read-query safety penalties for risky tools)
└── Reranker            (optional; runs after embedding retrieval)
```

- `embeddings.py` — `HashingEmbeddingProvider` is the zero-dependency default. `SentenceTransformerEmbeddingProvider` and `OpenAIEmbeddingProvider` are optional extras.
- `router.py` — `ToolRouter.discover` is the single entry point. Returns ranked `DiscoveryResult`s.
- `evaluation.py` / `live_benchmark.py` — frozen-task evaluation harness. If you change the ranking algorithm, you must justify any change in the frozen benchmark numbers.
- `mcp.py` — stdio MCP client. Hardcoded protocol version lives here; update with care.

## Reporting security issues

Please do **not** file public issues for security bugs. See [SECURITY.md](SECURITY.md) for the disclosure process.
