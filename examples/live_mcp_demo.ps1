$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$readmePath = (Join-Path $projectRoot "README.md").Replace("\", "/")

python -m semantic_tool_router mcp-discover `
    "read the first lines of the project README as text" `
    --top-k 3 `
    --allow-permission read `
    --expect-tool read_text_file `
    --call-argument "path=$readmePath" `
    --call-argument "head=8" `
    --server npx -y @modelcontextprotocol/server-filesystem $projectRoot
