from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from semantic_tool_router.router import ToolRouter


@dataclass(frozen=True)
class BenchmarkTask:
    query: str
    expected_tools: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "BenchmarkTask":
        query = str(data.get("query", "")).strip()
        expected = tuple(str(item) for item in data.get("expected_tools", []))
        if not query:
            raise ValueError("Benchmark task is missing a query")
        if not expected:
            raise ValueError(f"Benchmark task has no expected tools: {query}")
        return cls(query=query, expected_tools=expected)


@dataclass(frozen=True)
class TaskEvaluation:
    task: BenchmarkTask
    retrieved_tools: tuple[str, ...]
    relevant_retrieved: tuple[str, ...]
    reciprocal_rank: float

    @property
    def hit(self) -> bool:
        return bool(self.relevant_retrieved)

    @property
    def top_1_hit(self) -> bool:
        return bool(self.retrieved_tools) and self.retrieved_tools[0] in self.task.expected_tools

    @property
    def recall(self) -> float:
        return len(self.relevant_retrieved) / len(self.task.expected_tools)

    @property
    def precision(self) -> float:
        if not self.retrieved_tools:
            return 0.0
        return len(self.relevant_retrieved) / len(self.retrieved_tools)


@dataclass(frozen=True)
class BenchmarkReport:
    evaluations: tuple[TaskEvaluation, ...]
    top_k: int

    @property
    def task_count(self) -> int:
        return len(self.evaluations)

    def _mean(self, values: Iterable[float]) -> float:
        values = tuple(values)
        return sum(values) / len(values) if values else 0.0

    @property
    def hit_rate(self) -> float:
        return self._mean(float(item.hit) for item in self.evaluations)

    @property
    def top_1_accuracy(self) -> float:
        return self._mean(float(item.top_1_hit) for item in self.evaluations)

    @property
    def mean_reciprocal_rank(self) -> float:
        return self._mean(item.reciprocal_rank for item in self.evaluations)

    @property
    def mean_recall(self) -> float:
        return self._mean(item.recall for item in self.evaluations)

    @property
    def mean_precision(self) -> float:
        return self._mean(item.precision for item in self.evaluations)

    def as_dict(self) -> dict[str, float | int]:
        return {
            "task_count": self.task_count,
            "top_k": self.top_k,
            f"hit_rate@{self.top_k}": self.hit_rate,
            "top_1_accuracy": self.top_1_accuracy,
            "mrr": self.mean_reciprocal_rank,
            f"mean_recall@{self.top_k}": self.mean_recall,
            f"mean_precision@{self.top_k}": self.mean_precision,
        }


def evaluate(router: ToolRouter, tasks: Iterable[BenchmarkTask], top_k: int) -> BenchmarkReport:
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    evaluations = []
    for task in tasks:
        retrieved = tuple(
            result.tool.name for result in router.discover(task.query, top_k=top_k)
        )
        expected = set(task.expected_tools)
        relevant = tuple(name for name in retrieved if name in expected)
        reciprocal_rank = next(
            (1.0 / rank for rank, name in enumerate(retrieved, start=1) if name in expected),
            0.0,
        )
        evaluations.append(
            TaskEvaluation(
                task=task,
                retrieved_tools=retrieved,
                relevant_retrieved=relevant,
                reciprocal_rank=reciprocal_rank,
            )
        )

    return BenchmarkReport(evaluations=tuple(evaluations), top_k=top_k)
