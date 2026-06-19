from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from semantic_tool_router.embeddings import EmbeddingProvider
from semantic_tool_router.mcp import McpServerSnapshot, StdioMcpClient, estimate_tokens
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.router import ToolRouter


@dataclass(frozen=True)
class LiveTask:
    query: str
    expected_tools: tuple[str, ...]


@dataclass(frozen=True)
class LiveServerCase:
    identifier: str
    command: tuple[str, ...]
    tasks: tuple[LiveTask, ...]


def load_live_suite(path: str | Path, workspace: str | Path) -> tuple[int, tuple[LiveServerCase, ...]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    top_k = int(data.get("top_k", 3))
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    workspace_value = str(Path(workspace).resolve())
    cases = []
    for server in data.get("servers", []):
        command = tuple(
            str(part).replace("{workspace}", workspace_value)
            for part in server["command"]
        )
        tasks = tuple(
            LiveTask(
                query=str(task["query"]),
                expected_tools=tuple(str(name) for name in task["expected_tools"]),
            )
            for task in server["tasks"]
        )
        cases.append(
            LiveServerCase(
                identifier=str(server["id"]),
                command=command,
                tasks=tasks,
            )
        )
    if not cases:
        raise ValueError("Live suite must contain at least one server")
    return top_k, tuple(cases)


def run_live_suite(
    cases: tuple[LiveServerCase, ...],
    top_k: int,
    timeout: float = 60.0,
    embedding_provider: EmbeddingProvider | None = None,
) -> dict[str, Any]:
    server_reports = []
    for case in cases:
        with StdioMcpClient(list(case.command), timeout=timeout) as client:
            snapshot = client.snapshot()
        server_reports.append(
            _evaluate_server(case, snapshot, top_k, embedding_provider=embedding_provider)
        )

    task_reports = [
        task
        for server in server_reports
        for task in server["tasks"]
    ]
    nontrivial_tasks = [
        task
        for server in server_reports
        if server["available_tools"] > 1
        for task in server["tasks"]
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_k": top_k,
        "server_count": len(server_reports),
        "task_count": len(task_reports),
        "metrics": _metrics(task_reports),
        "nontrivial_task_count": len(nontrivial_tasks),
        "nontrivial_metrics": _metrics(nontrivial_tasks),
        "servers": server_reports,
    }


def render_markdown(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    nontrivial_metrics = report["nontrivial_metrics"]
    lines = [
        "# Live MCP Baseline",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        f"- Servers: {report['server_count']}",
        f"- Tasks: {report['task_count']}",
        f"- Hit rate@{report['top_k']}: {metrics['hit_rate']:.1%}",
        f"- Top-1 accuracy: {metrics['top_1_accuracy']:.1%}",
        f"- MRR: {metrics['mrr']:.3f}",
        f"- Mean estimated context saved: {metrics['mean_context_saved']:.1%}",
        (
            f"- Nontrivial hit rate@{report['top_k']}: "
            f"{nontrivial_metrics['hit_rate']:.1%} "
            f"({report['nontrivial_task_count']} tasks on servers with multiple tools)"
        ),
        f"- Nontrivial top-1 accuracy: {nontrivial_metrics['top_1_accuracy']:.1%}",
        f"- Nontrivial MRR: {nontrivial_metrics['mrr']:.3f}",
        "",
        "| Server | Tools | Tasks | Hit rate | Top-1 | MRR | Context saved |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for server in report["servers"]:
        server_metrics = server["metrics"]
        lines.append(
            f"| {server['id']} | {server['available_tools']} | "
            f"{len(server['tasks'])} | {server_metrics['hit_rate']:.1%} | "
            f"{server_metrics['top_1_accuracy']:.1%} | "
            f"{server_metrics['mrr']:.3f} | "
            f"{server_metrics['mean_context_saved']:.1%} |"
        )

    lines.extend(["", "## Task Results", ""])
    for server in report["servers"]:
        lines.append(f"### {server['id']}")
        lines.append("")
        for task in server["tasks"]:
            status = "PASS" if task["hit"] else "FAIL"
            ranked = ", ".join(task["retrieved_tools"])
            expected = ", ".join(task["expected_tools"])
            lines.append(
                f"- **{status}** `{task['query']}`  \n"
                f"  Expected: `{expected}`; ranked: `{ranked}`"
            )
        lines.append("")
    return "\n".join(lines)


def _evaluate_server(
    case: LiveServerCase,
    snapshot: McpServerSnapshot,
    top_k: int,
    embedding_provider: EmbeddingProvider | None = None,
) -> dict[str, Any]:
    router = ToolRouter(
        ToolRegistry(list(snapshot.tools)),
        embedding_provider=embedding_provider,
    )
    raw_by_name = {
        str(tool.get("name")): tool
        for tool in snapshot.raw_tools
    }
    all_tokens = estimate_tokens(snapshot.raw_tools)
    task_reports = []

    for task in case.tasks:
        results = router.discover(task.query, top_k=top_k)
        retrieved = [result.tool.name for result in results]
        expected = set(task.expected_tools)
        relevant_ranks = [
            rank
            for rank, name in enumerate(retrieved, start=1)
            if name in expected
        ]
        selected_raw = [
            raw_by_name[name]
            for name in retrieved
            if name in raw_by_name
        ]
        selected_tokens = estimate_tokens(selected_raw)
        context_saved = 1.0 - (selected_tokens / all_tokens) if all_tokens else 0.0
        task_reports.append(
            {
                "query": task.query,
                "expected_tools": list(task.expected_tools),
                "retrieved_tools": retrieved,
                "hit": bool(relevant_ranks),
                "top_1_hit": bool(relevant_ranks and relevant_ranks[0] == 1),
                "reciprocal_rank": 1.0 / relevant_ranks[0] if relevant_ranks else 0.0,
                "estimated_all_tool_tokens": all_tokens,
                "estimated_selected_tool_tokens": selected_tokens,
                "estimated_context_saved": context_saved,
            }
        )

    return {
        "id": case.identifier,
        "server_name": snapshot.name,
        "server_version": snapshot.version,
        "available_tools": len(snapshot.tools),
        "metrics": _metrics(task_reports),
        "tasks": task_reports,
    }


def _metrics(tasks: list[dict[str, Any]]) -> dict[str, float]:
    count = len(tasks)
    if not count:
        return {
            "hit_rate": 0.0,
            "top_1_accuracy": 0.0,
            "mrr": 0.0,
            "mean_context_saved": 0.0,
        }
    return {
        "hit_rate": sum(float(task["hit"]) for task in tasks) / count,
        "top_1_accuracy": sum(float(task["top_1_hit"]) for task in tasks) / count,
        "mrr": sum(float(task["reciprocal_rank"]) for task in tasks) / count,
        "mean_context_saved": (
            sum(float(task["estimated_context_saved"]) for task in tasks) / count
        ),
    }
