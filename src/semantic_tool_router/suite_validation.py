from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from semantic_tool_router.live_benchmark import load_live_suite
from semantic_tool_router.mcp import McpError, StdioMcpClient


@dataclass(frozen=True)
class SuiteValidationIssue:
    server: str
    query: str
    tool_name: str
    message: str


@dataclass(frozen=True)
class SuiteValidationReport:
    suite_path: str
    server_count: int
    task_count: int
    issues: tuple[SuiteValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict[str, Any]:
        return {
            "suite_path": self.suite_path,
            "server_count": self.server_count,
            "task_count": self.task_count,
            "valid": self.valid,
            "issue_count": len(self.issues),
            "issues": [
                {
                    "server": issue.server,
                    "query": issue.query,
                    "tool_name": issue.tool_name,
                    "message": issue.message,
                }
                for issue in self.issues
            ],
        }


def validate_live_suite(
    suite_path: str | Path,
    workspace: str | Path,
    *,
    timeout: float = 60.0,
) -> SuiteValidationReport:
    _, cases = load_live_suite(suite_path, workspace)
    issues: list[SuiteValidationIssue] = []
    task_count = 0

    for case in cases:
        try:
            with StdioMcpClient(list(case.command), timeout=timeout) as client:
                snapshot = client.snapshot()
        except (McpError, OSError) as error:
            issues.append(
                SuiteValidationIssue(
                    server=case.identifier,
                    query="*",
                    tool_name="*",
                    message=f"Could not connect to MCP server: {error}",
                )
            )
            task_count += len(case.tasks)
            continue

        available = {tool.name for tool in snapshot.tools}
        for task in case.tasks:
            task_count += 1
            for tool_name in task.expected_tools:
                if tool_name not in available:
                    issues.append(
                        SuiteValidationIssue(
                            server=case.identifier,
                            query=task.query,
                            tool_name=tool_name,
                            message="Tool not exposed by tools/list on this server version",
                        )
                    )

    return SuiteValidationReport(
        suite_path=str(suite_path),
        server_count=len(cases),
        task_count=task_count,
        issues=tuple(issues),
    )


def render_validation_markdown(report: SuiteValidationReport) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Live MCP Suite Validation",
        "",
        f"Generated: `{generated}`",
        "",
        f"Suite: `{report.suite_path}`",
        f"Servers: {report.server_count} | Tasks: {report.task_count}",
        f"Status: {'VALID' if report.valid else 'INVALID'}",
        "",
    ]
    if report.issues:
        lines.append("## Issues")
        lines.append("")
        for issue in report.issues:
            lines.append(
                f"- [{issue.server}] `{issue.tool_name}` for `{issue.query}` — {issue.message}"
            )
        lines.append("")
    return "\n".join(lines)


def write_validation_report(report: SuiteValidationReport, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
