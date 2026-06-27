# Live MCP Agent Evaluation

Generated: `2026-06-27T19:00:28Z`

Suite: `benchmarks/live_mcp_ci_smoke.json`  
Profile: `bge`  
Selector: `llm:gpt-4o-mini`  
Execute tools: `True`  
Tasks: 6 | top-k: 3

| Metric | Value |
| --- | ---: |
| Retrieval hit@3 | 100.0% |
| Agent success | 100.0% |
| End-to-end success | 100.0% |
| Execution success | 100.0% |
| End-to-end + execute | 100.0% |

## Task Results

- **PASS** [filesystem] `Open the project README and show me its text`  
  Expected: `read_text_file`; retrieved: `read_text_file, read_media_file, directory_tree`; selected: `read_text_file`; executed: `True`
- **PASS** [filesystem] `Which directories am I allowed to access in this workspace`  
  Expected: `list_allowed_directories`; retrieved: `list_allowed_directories, list_directory, list_directory_with_sizes`; selected: `list_allowed_directories`; executed: `True`
- **PASS** [memory] `Show the complete stored knowledge graph`  
  Expected: `read_graph`; retrieved: `read_graph, open_nodes, search_nodes`; selected: `read_graph`; executed: `True`
- **PASS** [sequential-thinking] `Work through a difficult architecture decision step by step`  
  Expected: `sequentialthinking`; retrieved: `sequentialthinking`; selected: `sequentialthinking`; executed: `True`
- **PASS** [everything] `Repeat my test message back to me`  
  Expected: `echo`; retrieved: `echo, toggle-subscriber-updates, get-structured-content`; selected: `echo`; executed: `True`
- **PASS** [everything] `Add two numbers and return their total`  
  Expected: `get-sum`; retrieved: `get-sum, get-resource-links, echo`; selected: `get-sum`; executed: `True`

