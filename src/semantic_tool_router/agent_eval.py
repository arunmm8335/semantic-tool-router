from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from semantic_tool_router.embeddings import EmbeddingProvider, tokenize
from semantic_tool_router.evaluation import BenchmarkTask
from semantic_tool_router.live_benchmark import LiveServerCase
from semantic_tool_router.mcp import StdioMcpClient
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

    @property
    def end_to_end_success(self) -> bool:
        return self.retrieval_hit and self.agent_success


@dataclass(frozen=True)
class AgentEvalReport:
    evaluations: tuple[AgentTaskEvaluation, ...]
    selector_name: str
    top_k: int

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

    def as_dict(self) -> dict[str, float | int | str]:
        return {
            "selector": self.selector_name,
            "task_count": self.task_count,
            "top_k": self.top_k,
            f"retrieval_hit_rate@{self.top_k}": self.retrieval_hit_rate,
            "agent_success_rate": self.agent_success_rate,
            "end_to_end_success_rate": self.end_to_end_success_rate,
        }


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
) -> tuple[AgentEvalReport, list[dict[str, Any]]]:
    evaluations: list[AgentTaskEvaluation] = []
    task_rows: list[dict[str, Any]] = []

    for case in cases:
        with StdioMcpClient(list(case.command), timeout=timeout) as client:
            snapshot = client.snapshot()
        router = ToolRouter(
            ToolRegistry(list(snapshot.tools)),
            embedding_provider=embedding_provider,
            reranker=reranker,
            hybrid_bm25_weight=hybrid_bm25_weight,
        )
        for task in case.tasks:
            benchmark = BenchmarkTask(query=task.query, expected_tools=task.expected_tools)
            report = evaluate_agent(
                router,
                [benchmark],
                top_k=top_k,
                selector=selector,
                selector_name=selector_name,
            )
            item = report.evaluations[0]
            evaluations.append(item)
            task_rows.append(
                {
                    "server": case.identifier,
                    "query": task.query,
                    "expected_tools": list(task.expected_tools),
                    "retrieved_tools": list(item.retrieved_tools),
                    "selected_tool": item.selected_tool,
                    "retrieval_hit": item.retrieval_hit,
                    "agent_success": item.agent_success,
                    "end_to_end_success": item.end_to_end_success,
                }
            )

    return (
        AgentEvalReport(
            evaluations=tuple(evaluations),
            selector_name=selector_name,
            top_k=top_k,
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
        f"Tasks: {report.task_count} | top-k: {report.top_k}",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Retrieval hit@{report.top_k} | {report.retrieval_hit_rate:.1%} |",
        f"| Agent success | {report.agent_success_rate:.1%} |",
        f"| End-to-end success | {report.end_to_end_success_rate:.1%} |",
        "",
        "## Task Results",
        "",
    ]
    for row in task_rows:
        status = "PASS" if row["end_to_end_success"] else "FAIL"
        expected = ", ".join(row["expected_tools"])
        retrieved = ", ".join(row["retrieved_tools"])
        lines.append(
            f"- **{status}** [{row['server']}] `{row['query']}`  \n"
            f"  Expected: `{expected}`; retrieved: `{retrieved}`; "
            f"selected: `{row['selected_tool']}`"
        )
    lines.append("")
    return "\n".join(lines)
