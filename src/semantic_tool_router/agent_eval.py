from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from semantic_tool_router.embeddings import EmbeddingProvider, tokenize
from semantic_tool_router.evaluation import BenchmarkTask
from semantic_tool_router.live_benchmark import LiveServerCase
from semantic_tool_router.mcp import StdioMcpClient
from semantic_tool_router.mcp_execution import (
    execute_selected_tool,
    is_destructive_tool,
)
from semantic_tool_router.models import DiscoveryResult
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.reranker import Reranker
from semantic_tool_router.router import ToolRouter


class AgentSelector(Protocol):
    def select(self, query: str, candidates: tuple[DiscoveryResult, ...]) -> str | None: ...


@dataclass(frozen=True)
class RankOneSelector:
    """Agent that always picks the highest-ranked retrieved tool."""

    def select(self, query: str, candidates: tuple[DiscoveryResult, ...]) -> str | None:
        _ = query
        return candidates[0].tool.name if candidates else None


@dataclass(frozen=True)
class LexicalSelector:
    """Agent that picks the candidate with the strongest lexical overlap."""

    def select(self, query: str, candidates: tuple[DiscoveryResult, ...]) -> str | None:
        if not candidates:
            return None
        query_terms = set(tokenize(query))
        best_name = candidates[0].tool.name
        best_score = -1.0
        for item in candidates:
            tool_terms = set(tokenize(item.tool.searchable_text("full")))
            score = float(len(query_terms & tool_terms))
            if score > best_score:
                best_score = score
                best_name = item.tool.name
        return best_name


@dataclass(frozen=True)
class AgentTaskEvaluation:
    task: BenchmarkTask
    retrieved_tools: tuple[str, ...]
    selected_tool: str | None
    retrieval_hit: bool
    agent_success: bool
    execution_attempted: bool = False
    execution_success: bool = False
    execution_error: str | None = None

    @property
    def end_to_end_success(self) -> bool:
        return self.retrieval_hit and self.agent_success

    @property
    def end_to_end_execute_success(self) -> bool:
        if not self.end_to_end_success:
            return False
        if not self.execution_attempted:
            return True
        return self.execution_success


@dataclass(frozen=True)
class AgentEvalReport:
    evaluations: tuple[AgentTaskEvaluation, ...]
    selector_name: str
    top_k: int
    execute_tools: bool = False

    @property
    def task_count(self) -> int:
        return len(self.evaluations)

    def _mean(self, values: Iterable[float]) -> float:
        values = tuple(values)
        return sum(values) / len(values) if values else 0.0

    @property
    def retrieval_hit_rate(self) -> float:
        return self._mean(float(item.retrieval_hit) for item in self.evaluations)

    @property
    def agent_success_rate(self) -> float:
        return self._mean(float(item.agent_success) for item in self.evaluations)

    @property
    def end_to_end_success_rate(self) -> float:
        return self._mean(float(item.end_to_end_success) for item in self.evaluations)

    @property
    def execution_attempt_count(self) -> int:
        return sum(1 for item in self.evaluations if item.execution_attempted)

    @property
    def execution_success_rate(self) -> float:
        attempted = tuple(item for item in self.evaluations if item.execution_attempted)
        if not attempted:
            return 0.0
        return self._mean(float(item.execution_success) for item in attempted)

    @property
    def end_to_end_execute_success_rate(self) -> float:
        if not self.execute_tools:
            return self.end_to_end_success_rate
        return self._mean(float(item.end_to_end_execute_success) for item in self.evaluations)

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "selector": self.selector_name,
            "task_count": self.task_count,
            "top_k": self.top_k,
            "execute_tools": self.execute_tools,
            f"retrieval_hit_rate@{self.top_k}": self.retrieval_hit_rate,
            "agent_success_rate": self.agent_success_rate,
            "end_to_end_success_rate": self.end_to_end_success_rate,
        }
        if self.execute_tools:
            payload["execution_attempt_count"] = self.execution_attempt_count
            payload["execution_success_rate"] = self.execution_success_rate
            payload["end_to_end_execute_success_rate"] = self.end_to_end_execute_success_rate
        return payload


def evaluate_agent(
    router: ToolRouter,
    tasks: Iterable[BenchmarkTask],
    top_k: int,
    selector: AgentSelector,
    *,
    selector_name: str,
) -> AgentEvalReport:
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    evaluations: list[AgentTaskEvaluation] = []
    for task in tasks:
        retrieved = router.discover(task.query, top_k=top_k)
        retrieved_names = tuple(item.tool.name for item in retrieved)
        expected = set(task.expected_tools)
        selected = selector.select(task.query, tuple(retrieved))
        retrieval_hit = any(name in expected for name in retrieved_names)
        agent_success = selected in expected if selected is not None else False
        evaluations.append(
            AgentTaskEvaluation(
                task=task,
                retrieved_tools=retrieved_names,
                selected_tool=selected,
                retrieval_hit=retrieval_hit,
                agent_success=agent_success,
            )
        )

    return AgentEvalReport(
        evaluations=tuple(evaluations),
        selector_name=selector_name,
        top_k=top_k,
    )


def run_live_agent_eval(
    cases: tuple[LiveServerCase, ...],
    top_k: int,
    selector: AgentSelector,
    *,
    selector_name: str,
    timeout: float = 60.0,
    embedding_provider: EmbeddingProvider | None = None,
    reranker: Reranker | None = None,
    hybrid_bm25_weight: float = 0.0,
    execute_tools: bool = False,
    workspace: str | Path = ".",
    skip_destructive_execution: bool = True,
) -> tuple[AgentEvalReport, list[dict[str, Any]]]:
    evaluations: list[AgentTaskEvaluation] = []
    task_rows: list[dict[str, Any]] = []

    for case in cases:
        with StdioMcpClient(list(case.command), timeout=timeout) as client:
            snapshot = client.snapshot()
            raw_by_name = {str(tool.get("name")): tool for tool in snapshot.raw_tools}
            router = ToolRouter(
                ToolRegistry(list(snapshot.tools)),
                embedding_provider=embedding_provider,
                reranker=reranker,
                hybrid_bm25_weight=hybrid_bm25_weight,
            )
            for task in case.tasks:
                benchmark = BenchmarkTask(query=task.query, expected_tools=task.expected_tools)
                item = evaluate_agent(
                    router,
                    [benchmark],
                    top_k=top_k,
                    selector=selector,
                    selector_name=selector_name,
                ).evaluations[0]

                execution_attempted = False
                execution_success = False
                execution_error: str | None = None

                if execute_tools and task.execute and item.selected_tool is not None:
                    raw_tool = raw_by_name.get(item.selected_tool)
                    if (
                        skip_destructive_execution
                        and raw_tool is not None
                        and is_destructive_tool(raw_tool)
                    ):
                        execution_error = "Skipped destructive tool execution"
                    else:
                        execution_attempted = True
                        execution_success, execution_error = execute_selected_tool(
                            client,
                            tool_name=item.selected_tool,
                            raw_tool=raw_tool,
                            workspace=workspace,
                            query=task.query,
                            arguments=task.execute_arguments,
                        )

                if execute_tools:
                    item = replace(
                        item,
                        execution_attempted=execution_attempted,
                        execution_success=execution_success,
                        execution_error=execution_error,
                    )

                evaluations.append(item)
                row: dict[str, Any] = {
                    "server": case.identifier,
                    "query": task.query,
                    "expected_tools": list(task.expected_tools),
                    "retrieved_tools": list(item.retrieved_tools),
                    "selected_tool": item.selected_tool,
                    "retrieval_hit": item.retrieval_hit,
                    "agent_success": item.agent_success,
                    "end_to_end_success": item.end_to_end_success,
                }
                if execute_tools:
                    row.update(
                        {
                            "execution_attempted": item.execution_attempted,
                            "execution_success": item.execution_success,
                            "execution_error": item.execution_error,
                            "end_to_end_execute_success": item.end_to_end_execute_success,
                        }
                    )
                task_rows.append(row)

    return (
        AgentEvalReport(
            evaluations=tuple(evaluations),
            selector_name=selector_name,
            top_k=top_k,
            execute_tools=execute_tools,
        ),
        task_rows,
    )


def render_live_agent_markdown(
    report: AgentEvalReport,
    task_rows: list[dict[str, Any]],
    *,
    suite_path: str,
    profile: str,
) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Live MCP Agent Evaluation",
        "",
        f"Generated: `{generated}`",
        "",
        f"Suite: `{suite_path}`  ",
        f"Profile: `{profile}`  ",
        f"Selector: `{report.selector_name}`  ",
        f"Execute tools: `{report.execute_tools}`  ",
        f"Tasks: {report.task_count} | top-k: {report.top_k}",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Retrieval hit@{report.top_k} | {report.retrieval_hit_rate:.1%} |",
        f"| Agent success | {report.agent_success_rate:.1%} |",
        f"| End-to-end success | {report.end_to_end_success_rate:.1%} |",
    ]
    if report.execute_tools:
        lines.extend(
            [
                f"| Execution success | {report.execution_success_rate:.1%} |",
                f"| End-to-end + execute | {report.end_to_end_execute_success_rate:.1%} |",
            ]
        )
    lines.extend(["", "## Task Results", ""])
    for row in task_rows:
        if report.execute_tools:
            status = "PASS" if row["end_to_end_execute_success"] else "FAIL"
        else:
            status = "PASS" if row["end_to_end_success"] else "FAIL"
        expected = ", ".join(row["expected_tools"])
        retrieved = ", ".join(row["retrieved_tools"])
        detail = (
            f"Expected: `{expected}`; retrieved: `{retrieved}`; selected: `{row['selected_tool']}`"
        )
        if report.execute_tools:
            detail += (
                f"; executed: `{row['execution_success']}`"
                if row["execution_attempted"]
                else "; executed: `skipped`"
            )
            if row.get("execution_error"):
                detail += f" ({row['execution_error']})"
        lines.append(f"- **{status}** [{row['server']}] `{row['query']}`  \n  {detail}")
    lines.append("")
    return "\n".join(lines)
