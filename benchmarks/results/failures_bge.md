# Live MCP Baseline

Generated: `2026-06-27T17:59:48.621247+00:00`

- Servers: 4
- Tasks: 51
- Hit rate@3: 98.0%
- Top-1 accuracy: 92.2%
- MRR: 0.944
- Mean estimated context saved: 64.7%
- Nontrivial hit rate@3: 97.8% (46 tasks on servers with multiple tools)
- Nontrivial top-1 accuracy: 91.3%
- Nontrivial MRR: 0.938

| Server | Tools | Tasks | Hit rate | Top-1 | MRR | Context saved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| filesystem | 14 | 12 | 100.0% | 83.3% | 0.903 | 78.0% |
| memory | 9 | 20 | 95.0% | 90.0% | 0.917 | 64.9% |
| sequential-thinking | 1 | 5 | 100.0% | 100.0% | 1.000 | 0.0% |
| everything | 13 | 14 | 100.0% | 100.0% | 1.000 | 76.0% |

## Task Results

### filesystem

- **PASS** `Open the project README and show me its text`  
  Expected: `read_text_file`; ranked: `read_text_file, read_media_file, directory_tree`
- **PASS** `Show the files and folders directly inside the source directory`  
  Expected: `list_directory, list_directory_with_sizes`; ranked: `list_directory, list_directory_with_sizes, directory_tree`
- **PASS** `Find every Python source file under this project recursively`  
  Expected: `search_files`; ranked: `search_files, directory_tree, list_directory`
- **PASS** `Tell me the size and modification time of pyproject.toml`  
  Expected: `get_file_info`; ranked: `edit_file, list_directory_with_sizes, get_file_info`
- **PASS** `Give me a tree view of the whole project directory structure`  
  Expected: `directory_tree`; ranked: `directory_tree, list_directory, list_directory_with_sizes`
- **PASS** `Which directories am I allowed to access in this workspace`  
  Expected: `list_allowed_directories`; ranked: `list_allowed_directories, list_directory, list_directory_with_sizes`
- **PASS** `Read README and LICENSE together in one request`  
  Expected: `read_multiple_files`; ranked: `read_media_file, read_multiple_files, read_text_file`
- **PASS** `List the source folder contents with each file size shown`  
  Expected: `list_directory_with_sizes`; ranked: `list_directory_with_sizes, list_directory, get_file_info`
- **PASS** `Search this project for every JSON configuration file`  
  Expected: `search_files`; ranked: `search_files, directory_tree, list_directory`
- **PASS** `Move pyproject.toml into a temporary backup folder`  
  Expected: `move_file`; ranked: `move_file, write_file, read_multiple_files`
- **PASS** `Update a single line inside the README file`  
  Expected: `edit_file`; ranked: `edit_file, read_text_file, read_multiple_files`
- **PASS** `Read an image or binary media file from the repository`  
  Expected: `read_media_file`; ranked: `read_media_file, read_text_file, get_file_info`

### memory

- **PASS** `Remember Arun as a person who is researching tool discovery`  
  Expected: `create_entities`; ranked: `search_nodes, add_observations, create_entities`
- **PASS** `Connect the semantic router project to the MCP research topic`  
  Expected: `create_relations`; ranked: `create_relations, search_nodes, open_nodes`
- **PASS** `Find anything previously remembered about Arun`  
  Expected: `search_nodes, open_nodes`; ranked: `search_nodes, read_graph, open_nodes`
- **PASS** `Show the complete stored knowledge graph`  
  Expected: `read_graph`; ranked: `read_graph, open_nodes, search_nodes`
- **PASS** `Add another fact to an existing person's memory`  
  Expected: `add_observations`; ranked: `add_observations, create_entities, create_relations`
- **PASS** `Link the mentor person to the student they advise in the graph`  
  Expected: `create_relations`; ranked: `create_relations, create_entities, add_observations`
- **FAIL** `Record that the benchmark suite depends on the router library`  
  Expected: `create_relations`; ranked: `open_nodes, read_graph, add_observations`
- **PASS** `Associate a new research paper with its primary author`  
  Expected: `create_relations`; ranked: `create_relations, add_observations, create_entities`
- **PASS** `Store a new collaborator who joined the open source project`  
  Expected: `create_entities`; ranked: `create_entities, create_relations, add_observations`
- **PASS** `Search memory for nodes related to semantic retrieval`  
  Expected: `search_nodes`; ranked: `search_nodes, open_nodes, read_graph`
- **PASS** `Open the entity record for a person already stored by name`  
  Expected: `open_nodes`; ranked: `open_nodes, add_observations, create_entities`
- **PASS** `Remove an outdated note attached to an existing entity`  
  Expected: `delete_observations`; ranked: `delete_observations, delete_entities, add_observations`
- **PASS** `Delete a relationship that is no longer true`  
  Expected: `delete_relations`; ranked: `delete_relations, delete_entities, delete_observations`
- **PASS** `Remove an entity that was added to memory by mistake`  
  Expected: `delete_entities`; ranked: `delete_entities, delete_observations, delete_relations`
- **PASS** `Display the full graph of everything currently in memory`  
  Expected: `read_graph`; ranked: `read_graph, search_nodes, open_nodes`
- **PASS** `Create a new project entity for the semantic tool router`  
  Expected: `create_entities`; ranked: `create_entities, create_relations, add_observations`
- **PASS** `Attach a meeting summary observation to an existing team node`  
  Expected: `add_observations`; ranked: `add_observations, create_entities, open_nodes`
- **PASS** `Look up stored nodes whose name contains benchmark`  
  Expected: `search_nodes`; ranked: `search_nodes, open_nodes, read_graph`
- **PASS** `Drop an incorrect link between two unrelated concepts`  
  Expected: `delete_relations`; ranked: `delete_relations, delete_entities, create_relations`
- **PASS** `Fetch a specific stored node by its identifier`  
  Expected: `open_nodes`; ranked: `open_nodes, search_nodes, delete_entities`

### sequential-thinking

- **PASS** `Work through a difficult architecture decision step by step`  
  Expected: `sequentialthinking`; ranked: `sequentialthinking`
- **PASS** `Revise an earlier line of reasoning after discovering a mistake`  
  Expected: `sequentialthinking`; ranked: `sequentialthinking`
- **PASS** `Break down a complex debugging problem into ordered reasoning steps`  
  Expected: `sequentialthinking`; ranked: `sequentialthinking`
- **PASS** `Plan the rollout of a new retrieval feature in stages`  
  Expected: `sequentialthinking`; ranked: `sequentialthinking`
- **PASS** `Compare two router designs using structured sequential analysis`  
  Expected: `sequentialthinking`; ranked: `sequentialthinking`

### everything

- **PASS** `Repeat my test message back to me`  
  Expected: `echo`; ranked: `echo, toggle-subscriber-updates, get-structured-content`
- **PASS** `Add two numbers and return their total`  
  Expected: `get-sum`; ranked: `get-sum, get-resource-links, echo`
- **PASS** `Return a response containing structured data`  
  Expected: `get-structured-content`; ranked: `get-structured-content, echo, get-annotated-message`
- **PASS** `Start a task that takes a while to finish`  
  Expected: `trigger-long-running-operation`; ranked: `trigger-long-running-operation, simulate-research-query, toggle-subscriber-updates`
- **PASS** `Read an environment variable from the host process`  
  Expected: `get-env`; ranked: `get-env, get-structured-content, get-resource-reference`
- **PASS** `Return a message with extra annotation metadata attached`  
  Expected: `get-annotated-message`; ranked: `get-annotated-message, echo, get-structured-content`
- **PASS** `Run a simulated research query against sample data`  
  Expected: `simulate-research-query`; ranked: `simulate-research-query, toggle-subscriber-updates, trigger-long-running-operation`
- **PASS** `Provide a reference handle to an external resource`  
  Expected: `get-resource-reference`; ranked: `get-resource-reference, get-resource-links, get-annotated-message`
- **PASS** `List hyperlinks or resource URLs exposed by the server`  
  Expected: `get-resource-links`; ranked: `get-resource-links, get-resource-reference, get-annotated-message`
- **PASS** `Turn simulated diagnostic logging on or off`  
  Expected: `toggle-simulated-logging`; ranked: `toggle-simulated-logging, toggle-subscriber-updates, trigger-long-running-operation`
- **PASS** `Compress a file and expose it as a downloadable resource`  
  Expected: `gzip-file-as-resource`; ranked: `gzip-file-as-resource, get-structured-content, toggle-subscriber-updates`
- **PASS** `Echo back a short diagnostic string for connectivity testing`  
  Expected: `echo`; ranked: `echo, get-env, get-structured-content`
- **PASS** `Compute the sum of 42 and 58`  
  Expected: `get-sum`; ranked: `get-sum, simulate-research-query, get-resource-links`
- **PASS** `Kick off a long-running background operation and track it`  
  Expected: `trigger-long-running-operation`; ranked: `trigger-long-running-operation, simulate-research-query, toggle-subscriber-updates`

