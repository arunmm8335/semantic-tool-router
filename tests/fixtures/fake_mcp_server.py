from __future__ import annotations

import json
import sys


TOOLS = [
    {
        "name": "read_text_file",
        "description": "Read a text file from the local filesystem.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "delete_file",
        "description": "Delete a local file.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        "annotations": {"destructiveHint": True},
    },
]


for line in sys.stdin:
    message = json.loads(line)
    method = message.get("method")
    request_id = message.get("id")

    if method == "initialize":
        result = {
            "protocolVersion": "2025-11-25",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "fake-filesystem", "version": "1.0.0"},
        }
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = message["params"]
        result = {
            "content": [
                {
                    "type": "text",
                    "text": f"called {params['name']} with {params['arguments']}",
                }
            ]
        }
    else:
        continue

    print(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}), flush=True)
