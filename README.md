# Semantic Tool Router

[![PyPI Version](https://img.shields.io/badge/pypi-v0.1.0--alpha-blue)](https://pypi.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python Support](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](pyproject.toml)
[![CI Build](https://img.shields.io/badge/build-passing-brightgreen)](.github/workflows/ci.yml)

> **Dynamic runtime tool discovery and retrieval-augmented routing for AI agents.**

Semantic Tool Router is a dependency-light library designed to manage the "Many-Tool" problem in LLM and Agentic workflows. Instead of exposing every available tool or Model Context Protocol (MCP) server schema to a model context window (which increases costs and degrades accuracy), it embeds tools based on their descriptions and dynamically retrieves a focused candidate set ($top-k$) for the current task.

---

## How It Works

```mermaid
graph TD
    Query[User Task Query] --> QueryEmbed[Embed Query]
    Registry[MCP Servers / JSON Registry] --> ToolSpecs[Extract Tool Specs]
    ToolSpecs --> EmbedTools[Embed Tool metadata]
    QueryEmbed --> Routing{Cosine Similarity}
    EmbedTools --> Routing
    Routing --> Filters{Tag & Permission Filters}
    Filters --> Ranked[Ranked Candidate Tools]
    Ranked --> TopK[Select Top-K Tools]
    TopK --> LLM[LLM Context Window]

    style Query fill:#d1e7dd,stroke:#0f5132,stroke-width:2px
    style LLM fill:#cff4fc,stroke:#087990,stroke-width:2px
    style Routing fill:#f8d7da,stroke:#842029,stroke-width:2px
```

1. **Tool Indexing:** Tool descriptions, schemas, tags, examples, and permissions are compiled into search strings and vectorized.
2. **Semantic Matching:** The user query is embedded and compared against the indexed tools using cosine similarity.
3. **Metadata Filtering:** Results are filtered by permission layers (e.g. read-only vs destructive commands) or specific tags.
4. **Context Injection:** Only the top $k$ relevant tool schemas are injected into the LLM system prompt, preserving context tokens.

---

## Features

*   ⚡ **Zero-Dependency Hashing Baseline:** Comes with a local token-hashing vectorizer (`HashingEmbeddingProvider`) that runs instantly without external APIs or PyTorch downloads.
*   🔌 **First-Class MCP Client:** Connects to live Stdio MCP servers, imports schemas automatically, and executes selected tools under expectation guards.
*   🏷️ **Metadata-Aware Filtering:** Apply rigid tag filters or restrict tools based on security permissions (`read`, `write`, `execute`, `destructive`, `network`).
*   📈 **Evaluation Suite:** Measure retrieval metrics (`hit_rate@k`, `top_1_accuracy`, `MRR`, `context_tokens_saved`) against reproducible benchmark files.
*   🧠 **Swappable Embedders:** Easily swap the hashing provider for local Hugging Face `SentenceTransformers` or cloud APIs (`OpenAI`).

---

## Installation

Install the core package (includes standard hashing retriever):

```bash
pip install -e .
```

For advanced semantic embeddings, install the optional package extras:

```bash
# To run local models via SentenceTransformers
pip install -e .[sentence-transformers]

# To use OpenAI's hosted embedding models
pip install -e .[openai]
```

---

## Quick Start

### 1. Basic Tool Discovery
Query a local JSON registry of tool specs:

```bash
python -m semantic_tool_router discover "read the project README file" --registry examples/tools.json
```

Or choose a specific embedding model:

```bash
python -m semantic_tool_router discover "generate a mock logo" \
  --registry examples/tools.json \
  --embedder sentence-transformers \
  --embedding-model all-MiniLM-L6-v2
```

### 2. Live MCP Routing
Connect to a live filesystem MCP server, dynamically retrieve the top-3 candidate tools matching your task, and execute the selected tool with safety parameters:

```powershell
python -m semantic_tool_router mcp-discover \
  "read the first lines of the project README" \
  --top-k 3 \
  --allow-permission read \
  --expect-tool read_text_file \
  --call-argument "path=README.md" \
  --call-argument "head=8" \
  --server npx -y @modelcontextprotocol/server-filesystem .
```

---

## Integrations

Use the router as a preprocessing step inside standard orchestrator loops to save prompt tokens:

*   **LangChain Agent Integration:** See the [langchain_integration.py](examples/langchain_integration.py) template.
*   **LlamaIndex Agent Integration:** See the [llamaindex_integration.py](examples/llamaindex_integration.py) template.

---

## Benchmarking & Evaluation

Evaluate your router configuration on fixture datasets:

```bash
python -m semantic_tool_router benchmark \
  --registry examples/tools.json \
  --tasks benchmarks/tasks.json \
  --top-k 3
```

To run the reproducible baseline benchmark suite across four official live MCP reference servers (Filesystem, Memory, Sequential Thinking, and Everything):

```bash
python -m semantic_tool_router mcp-benchmark \
  --suite benchmarks/live_mcp_suite.json \
  --workspace . \
  --markdown-output benchmarks/results/live_mcp_baseline.md
```

---

## Testing

Run unit tests locally across mock registry and MCP environments:

```bash
python -m unittest discover -s tests
```

---

## Contributing & Development

Contributions are welcome! Please run tests and benchmarking commands to verify that metrics remain high before submitting pull requests.

1. Fork the repo and clone locally.
2. Setup tests: `python -m pip install -e .[sentence-transformers,openai]`
3. Ensure CI checks pass: `python -m unittest discover -s tests`

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
