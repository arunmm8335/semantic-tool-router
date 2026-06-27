# Live MCP Agent Evaluation

Generated: `2026-06-27T18:48:13Z`

Suite: `benchmarks/live_mcp_suite.json`  
Profile: `bge`  
Selector: `llm:gpt-4o-mini`  
Tasks: 51 | top-k: 3

| Metric | Value |
| --- | ---: |
| Retrieval hit@3 | 98.0% |
| Agent success | 98.0% |
| End-to-end success | 98.0% |

## Task Results

- **PASS** [filesystem] `Open the project README and show me its text`  
  Expected: `read_text_file`; retrieved: `read_text_file, read_media_file, directory_tree`; selected: `read_text_file`
- **PASS** [filesystem] `Show the files and folders directly inside the source directory`  
  Expected: `list_directory, list_directory_with_sizes`; retrieved: `list_directory, list_directory_with_sizes, directory_tree`; selected: `list_directory`
- **PASS** [filesystem] `Find every Python source file under this project recursively`  
  Expected: `search_files`; retrieved: `search_files, directory_tree, list_directory`; selected: `search_files`
- **PASS** [filesystem] `Tell me the size and modification time of pyproject.toml`  
  Expected: `get_file_info`; retrieved: `edit_file, list_directory_with_sizes, get_file_info`; selected: `get_file_info`
- **PASS** [filesystem] `Give me a tree view of the whole project directory structure`  
  Expected: `directory_tree`; retrieved: `directory_tree, list_directory, list_directory_with_sizes`; selected: `directory_tree`
- **PASS** [filesystem] `Which directories am I allowed to access in this workspace`  
  Expected: `list_allowed_directories`; retrieved: `list_allowed_directories, list_directory, list_directory_with_sizes`; selected: `list_allowed_directories`
- **PASS** [filesystem] `Read README and LICENSE together in one request`  
  Expected: `read_multiple_files`; retrieved: `read_media_file, read_multiple_files, read_text_file`; selected: `read_multiple_files`
- **PASS** [filesystem] `List the source folder contents with each file size shown`  
  Expected: `list_directory_with_sizes`; retrieved: `list_directory_with_sizes, list_directory, get_file_info`; selected: `list_directory_with_sizes`
- **PASS** [filesystem] `Search this project for every JSON configuration file`  
  Expected: `search_files`; retrieved: `search_files, directory_tree, list_directory`; selected: `search_files`
- **PASS** [filesystem] `Move pyproject.toml into a temporary backup folder`  
  Expected: `move_file`; retrieved: `move_file, write_file, read_multiple_files`; selected: `move_file`
- **PASS** [filesystem] `Update a single line inside the README file`  
  Expected: `edit_file`; retrieved: `edit_file, read_text_file, read_multiple_files`; selected: `edit_file`
- **PASS** [filesystem] `Read an image or binary media file from the repository`  
  Expected: `read_media_file`; retrieved: `read_media_file, read_text_file, get_file_info`; selected: `read_media_file`
- **PASS** [memory] `Remember Arun as a person who is researching tool discovery`  
  Expected: `create_entities`; retrieved: `search_nodes, add_observations, create_entities`; selected: `create_entities`
- **PASS** [memory] `Connect the semantic router project to the MCP research topic`  
  Expected: `create_relations`; retrieved: `create_relations, search_nodes, open_nodes`; selected: `create_relations`
- **PASS** [memory] `Find anything previously remembered about Arun`  
  Expected: `search_nodes, open_nodes`; retrieved: `search_nodes, read_graph, open_nodes`; selected: `search_nodes`
- **PASS** [memory] `Show the complete stored knowledge graph`  
  Expected: `read_graph`; retrieved: `read_graph, open_nodes, search_nodes`; selected: `read_graph`
- **PASS** [memory] `Add another fact to an existing person's memory`  
  Expected: `add_observations`; retrieved: `add_observations, create_entities, create_relations`; selected: `add_observations`
- **PASS** [memory] `Link the mentor person to the student they advise in the graph`  
  Expected: `create_relations`; retrieved: `create_relations, create_entities, add_observations`; selected: `create_relations`
- **FAIL** [memory] `Record that the benchmark suite depends on the router library`  
  Expected: `create_relations`; retrieved: `open_nodes, read_graph, add_observations`; selected: `add_observations`
- **PASS** [memory] `Associate a new research paper with its primary author`  
  Expected: `create_relations`; retrieved: `create_relations, add_observations, create_entities`; selected: `create_relations`
- **PASS** [memory] `Store a new collaborator who joined the open source project`  
  Expected: `create_entities`; retrieved: `create_entities, create_relations, add_observations`; selected: `create_entities`
- **PASS** [memory] `Search memory for nodes related to semantic retrieval`  
  Expected: `search_nodes`; retrieved: `search_nodes, open_nodes, read_graph`; selected: `search_nodes`
- **PASS** [memory] `Open the entity record for a person already stored by name`  
  Expected: `open_nodes`; retrieved: `open_nodes, add_observations, create_entities`; selected: `open_nodes`
- **PASS** [memory] `Remove an outdated note attached to an existing entity`  
  Expected: `delete_observations`; retrieved: `delete_observations, delete_entities, add_observations`; selected: `delete_observations`
- **PASS** [memory] `Delete a relationship that is no longer true`  
  Expected: `delete_relations`; retrieved: `delete_relations, delete_entities, delete_observations`; selected: `delete_relations`
- **PASS** [memory] `Remove an entity that was added to memory by mistake`  
  Expected: `delete_entities`; retrieved: `delete_entities, delete_observations, delete_relations`; selected: `delete_entities`
- **PASS** [memory] `Display the full graph of everything currently in memory`  
  Expected: `read_graph`; retrieved: `read_graph, search_nodes, open_nodes`; selected: `read_graph`
- **PASS** [memory] `Create a new project entity for the semantic tool router`  
  Expected: `create_entities`; retrieved: `create_entities, create_relations, add_observations`; selected: `create_entities`
- **PASS** [memory] `Attach a meeting summary observation to an existing team node`  
  Expected: `add_observations`; retrieved: `add_observations, create_entities, open_nodes`; selected: `add_observations`
- **PASS** [memory] `Look up stored nodes whose name contains benchmark`  
  Expected: `search_nodes`; retrieved: `search_nodes, open_nodes, read_graph`; selected: `search_nodes`
- **PASS** [memory] `Drop an incorrect link between two unrelated concepts`  
  Expected: `delete_relations`; retrieved: `delete_relations, delete_entities, create_relations`; selected: `delete_relations`
- **PASS** [memory] `Fetch a specific stored node by its identifier`  
  Expected: `open_nodes`; retrieved: `open_nodes, search_nodes, delete_entities`; selected: `open_nodes`
- **PASS** [sequential-thinking] `Work through a difficult architecture decision step by step`  
  Expected: `sequentialthinking`; retrieved: `sequentialthinking`; selected: `sequentialthinking`
- **PASS** [sequential-thinking] `Revise an earlier line of reasoning after discovering a mistake`  
  Expected: `sequentialthinking`; retrieved: `sequentialthinking`; selected: `sequentialthinking`
- **PASS** [sequential-thinking] `Break down a complex debugging problem into ordered reasoning steps`  
  Expected: `sequentialthinking`; retrieved: `sequentialthinking`; selected: `sequentialthinking`
- **PASS** [sequential-thinking] `Plan the rollout of a new retrieval feature in stages`  
  Expected: `sequentialthinking`; retrieved: `sequentialthinking`; selected: `sequentialthinking`
- **PASS** [sequential-thinking] `Compare two router designs using structured sequential analysis`  
  Expected: `sequentialthinking`; retrieved: `sequentialthinking`; selected: `sequentialthinking`
- **PASS** [everything] `Repeat my test message back to me`  
  Expected: `echo`; retrieved: `echo, toggle-subscriber-updates, get-structured-content`; selected: `echo`
- **PASS** [everything] `Add two numbers and return their total`  
  Expected: `get-sum`; retrieved: `get-sum, get-resource-links, echo`; selected: `get-sum`
- **PASS** [everything] `Return a response containing structured data`  
  Expected: `get-structured-content`; retrieved: `get-structured-content, echo, get-annotated-message`; selected: `get-structured-content`
- **PASS** [everything] `Start a task that takes a while to finish`  
  Expected: `trigger-long-running-operation`; retrieved: `trigger-long-running-operation, simulate-research-query, toggle-subscriber-updates`; selected: `trigger-long-running-operation`
- **PASS** [everything] `Read an environment variable from the host process`  
  Expected: `get-env`; retrieved: `get-env, get-structured-content, get-resource-reference`; selected: `get-env`
- **PASS** [everything] `Return a message with extra annotation metadata attached`  
  Expected: `get-annotated-message`; retrieved: `get-annotated-message, echo, get-structured-content`; selected: `get-annotated-message`
- **PASS** [everything] `Run a simulated research query against sample data`  
  Expected: `simulate-research-query`; retrieved: `simulate-research-query, toggle-subscriber-updates, trigger-long-running-operation`; selected: `simulate-research-query`
- **PASS** [everything] `Provide a reference handle to an external resource`  
  Expected: `get-resource-reference`; retrieved: `get-resource-reference, get-resource-links, get-annotated-message`; selected: `get-resource-reference`
- **PASS** [everything] `List hyperlinks or resource URLs exposed by the server`  
  Expected: `get-resource-links`; retrieved: `get-resource-links, get-resource-reference, get-annotated-message`; selected: `get-resource-links`
- **PASS** [everything] `Turn simulated diagnostic logging on or off`  
  Expected: `toggle-simulated-logging`; retrieved: `toggle-simulated-logging, toggle-subscriber-updates, trigger-long-running-operation`; selected: `toggle-simulated-logging`
- **PASS** [everything] `Compress a file and expose it as a downloadable resource`  
  Expected: `gzip-file-as-resource`; retrieved: `gzip-file-as-resource, get-structured-content, toggle-subscriber-updates`; selected: `gzip-file-as-resource`
- **PASS** [everything] `Echo back a short diagnostic string for connectivity testing`  
  Expected: `echo`; retrieved: `echo, get-env, get-structured-content`; selected: `echo`
- **PASS** [everything] `Compute the sum of 42 and 58`  
  Expected: `get-sum`; retrieved: `get-sum, simulate-research-query, get-resource-links`; selected: `get-sum`
- **PASS** [everything] `Kick off a long-running background operation and track it`  
  Expected: `trigger-long-running-operation`; retrieved: `trigger-long-running-operation, simulate-research-query, toggle-subscriber-updates`; selected: `trigger-long-running-operation`

