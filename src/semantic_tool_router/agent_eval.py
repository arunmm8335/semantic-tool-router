from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from semantic_tool_router.embeddings import tokenize
from semantic_tool_router.evaluation import BenchmarkTask
from semantic_tool_router.models import DiscoveryResult
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
