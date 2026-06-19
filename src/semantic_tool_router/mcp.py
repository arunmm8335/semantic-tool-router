from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
from dataclasses import dataclass
from typing import Any

from semantic_tool_router.models import ToolSpec


PROTOCOL_VERSION = "2025-11-25"


class McpError(RuntimeError):
    pass


@dataclass(frozen=True)
class McpServerSnapshot:
    name: str
    version: str
    tools: tuple[ToolSpec, ...]
    raw_tools: tuple[dict[str, Any], ...]


class StdioMcpClient:
    def __init__(self, command: list[str], timeout: float = 30.0) -> None:
        if not command:
            raise ValueError("MCP server command cannot be empty")
        self.command = command
        self.timeout = timeout
        self._process: subprocess.Popen[str] | None = None
        self._messages: queue.Queue[dict[str, Any] | BaseException] = queue.Queue()
        self._stderr_lines: list[str] = []
        self._request_id = 0

    def __enter__(self) -> "StdioMcpClient":
        command = list(self.command)
        if os.name == "nt" and command[0].lower() in {"npx", "npm"}:
            command[0] += ".cmd"

        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()
        return self

    def __exit__(self, *_: object) -> None:
        if self._process is None:
            return
        if self._process.stdin:
            self._process.stdin.close()
        try:
            self._process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
        if self._process.stdout:
            self._process.stdout.close()
        if self._process.stderr:
            self._process.stderr.close()
        self._process = None

    def snapshot(self) -> McpServerSnapshot:
        initialized = self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "semantic-tool-router",
                    "version": "0.1.0",
                },
            },
        )
        self._notify("notifications/initialized")

        server_info = initialized.get("serverInfo", {})
        raw_tools: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params = {"cursor": cursor} if cursor else None
            result = self._request("tools/list", params)
            tools = result.get("tools", [])
            if not isinstance(tools, list):
                raise McpError("MCP tools/list response did not contain a tools list")
            raw_tools.extend(tool for tool in tools if isinstance(tool, dict))
            cursor = result.get("nextCursor")
            if not cursor:
                break

        name = str(server_info.get("name", self.command[0]))
        version = str(server_info.get("version", "unknown"))
        specs = tuple(_tool_spec(tool, name) for tool in raw_tools)
        return McpServerSnapshot(
            name=name,
            version=version,
            tools=specs,
            raw_tools=tuple(raw_tools),
        )

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments,
            },
        )

    def _request(self, method: str, params: dict[str, Any] | None) -> dict[str, Any]:
        self._request_id += 1
        request_id = self._request_id
        message: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            message["params"] = params
        self._send(message)

        while True:
            try:
                response = self._messages.get(timeout=self.timeout)
            except queue.Empty as error:
                raise McpError(f"Timed out waiting for MCP {method}") from error
            if isinstance(response, BaseException):
                raise McpError(str(response)) from response
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise McpError(f"MCP {method} failed: {response['error']}")
            result = response.get("result", {})
            if not isinstance(result, dict):
                raise McpError(f"MCP {method} returned an invalid result")
            return result

    def _notify(self, method: str) -> None:
        self._send({"jsonrpc": "2.0", "method": method})

    def _send(self, message: dict[str, Any]) -> None:
        if self._process is None or self._process.stdin is None:
            raise McpError("MCP client is not connected")
        try:
            self._process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            raise McpError(self._process_error()) from error

    def _read_stdout(self) -> None:
        assert self._process is not None
        assert self._process.stdout is not None
        try:
            for line in self._process.stdout:
                line = line.strip()
                if line:
                    self._messages.put(json.loads(line))
        except (json.JSONDecodeError, OSError) as error:
            self._messages.put(error)
        finally:
            if self._process.poll() is not None:
                self._messages.put(McpError(self._process_error()))

    def _process_error(self) -> str:
        if self._process is None:
            return "MCP server stopped"
        stderr = "\n".join(self._stderr_lines).strip()
        detail = f": {stderr}" if stderr else ""
        return f"MCP server exited with code {self._process.poll()}{detail}"

    def _read_stderr(self) -> None:
        assert self._process is not None
        assert self._process.stderr is not None
        try:
            for line in self._process.stderr:
                self._stderr_lines.append(line.rstrip())
        except OSError:
            pass


def _tool_spec(tool: dict[str, Any], server_name: str) -> ToolSpec:
    annotations = tool.get("annotations", {})
    if not isinstance(annotations, dict):
        annotations = {}

    permissions = []
    if annotations.get("readOnlyHint") is True:
        permissions.append("read")
    else:
        permissions.append("write")
    if annotations.get("destructiveHint") is True:
        permissions.append("destructive")
    if annotations.get("openWorldHint") is True:
        permissions.append("network")

    schema = tool.get("inputSchema", {})
    tags = ["mcp", server_name]
    if "deprecated" in str(tool.get("description", "")).lower():
        tags.append("deprecated")
    return ToolSpec(
        name=str(tool.get("name", "")),
        description=str(tool.get("description", "MCP tool")),
        input_schema=dict(schema) if isinstance(schema, dict) else {},
        tags=tuple(tags),
        permissions=tuple(permissions),
        cost="remote" if "network" in permissions else "local",
    )


def estimate_tokens(value: object) -> int:
    serialized = json.dumps(value, separators=(",", ":"), ensure_ascii=True)
    return max(1, (len(serialized) + 3) // 4)
