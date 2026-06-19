# Live MCP Baseline

Generated: `2026-06-19T07:29:08.697975+00:00`

- Servers: 4
- Tasks: 15
- Hit rate@3: 73.3%
- Top-1 accuracy: 40.0%
- MRR: 0.556
- Mean estimated context saved: 62.0%
- Nontrivial hit rate@3: 69.2% (13 tasks on servers with multiple tools)
- Nontrivial top-1 accuracy: 30.8%
- Nontrivial MRR: 0.487

| Server | Tools | Tasks | Hit rate | Top-1 | MRR | Context saved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| filesystem | 14 | 4 | 75.0% | 25.0% | 0.458 | 77.0% |
| memory | 9 | 5 | 60.0% | 20.0% | 0.400 | 67.2% |
| sequential-thinking | 1 | 2 | 100.0% | 100.0% | 1.000 | 0.0% |
| everything | 13 | 4 | 75.0% | 50.0% | 0.625 | 71.6% |

## Task Results

### filesystem

- **PASS** `Open the project README and show me its text`  
  Expected: `read_text_file`; ranked: `read_text_file, read_multiple_files, edit_file`
- **PASS** `Show the files and folders directly inside the source directory`  
  Expected: `list_directory, list_directory_with_sizes`; ranked: `move_file, search_files, list_directory`
- **FAIL** `Find every Python source file under this project recursively`  
  Expected: `search_files`; ranked: `move_file, list_allowed_directories, read_text_file`
- **PASS** `Tell me the size and modification time of pyproject.toml`  
  Expected: `get_file_info`; ranked: `read_text_file, get_file_info, move_file`

### memory

- **PASS** `Remember Arun as a person who is researching tool discovery`  
  Expected: `create_entities`; ranked: `search_nodes, create_entities, create_relations`
- **PASS** `Connect the semantic router project to the MCP research topic`  
  Expected: `create_relations`; ranked: `add_observations, create_relations, read_graph`
- **FAIL** `Find anything previously remembered about Arun`  
  Expected: `search_nodes, open_nodes`; ranked: `create_relations, delete_relations, delete_entities`
- **FAIL** `Show the complete stored knowledge graph`  
  Expected: `read_graph`; ranked: `delete_observations, delete_relations, delete_entities`
- **PASS** `Add another fact to an existing person's memory`  
  Expected: `add_observations`; ranked: `add_observations, search_nodes, read_graph`

### sequential-thinking

- **PASS** `Work through a difficult architecture decision step by step`  
  Expected: `sequentialthinking`; ranked: `sequentialthinking`
- **PASS** `Revise an earlier line of reasoning after discovering a mistake`  
  Expected: `sequentialthinking`; ranked: `sequentialthinking`

### everything

- **PASS** `Repeat my test message back to me`  
  Expected: `echo`; ranked: `get-annotated-message, echo, get-env`
- **PASS** `Add two numbers and return their total`  
  Expected: `get-sum`; ranked: `get-sum, simulate-research-query, echo`
- **PASS** `Return a response containing structured data`  
  Expected: `get-structured-content`; ranked: `get-structured-content, gzip-file-as-resource, get-resource-reference`
- **FAIL** `Start a task that takes a while to finish`  
  Expected: `trigger-long-running-operation`; ranked: `gzip-file-as-resource, simulate-research-query, get-resource-reference`

