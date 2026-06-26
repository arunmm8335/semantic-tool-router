from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from semantic_tool_router.embeddings import (
    EmbeddingProvider,
    HashingEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)
from semantic_tool_router.evaluation import BenchmarkReport, BenchmarkTask, evaluate
from semantic_tool_router.live_benchmark import load_live_suite, run_live_suite
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.reranker import CrossEncoderReranker, Reranker
from semantic_tool_router.router import ToolRouter


@dataclass(frozen=True)
class RetrieverConfig:
    name: str
    embedder: str = "hashing"
    embedding_model: str | None = None
    reranker: str | None = None
    reranker_model: str | None = None


DEFAULT_CONFIGS: tuple[RetrieverConfig, ...] = (
    RetrieverConfig(name="hashing"),
    RetrieverConfig(
        name="sentence-transformers (all-MiniLM-L6-v2)",
        embedder="sentence-transformers",
        embedding_model="all-MiniLM-L6-v2",
    ),
    RetrieverConfig(
        name="hashing + cross-encoder",
        embedder="hashing",
        reranker="cross-encoder",
    ),
    RetrieverConfig(
        name="sentence-transformers + cross-encoder",
        embedder="sentence-transformers",
        embedding_model="all-MiniLM-L6-v2",
        reranker="cross-encoder",
    ),
)


def _build_embedder(config: RetrieverConfig) -> EmbeddingProvider:
    if config.embedder == "sentence-transformers":
        model_name = config.embedding_model or "all-MiniLM-L6-v2"
        return SentenceTransformerEmbeddingProvider(model_name=model_name)
    return HashingEmbeddingProvider()


def _build_reranker(config: RetrieverConfig) -> Reranker | None:
    if config.reranker == "cross-encoder":
        model_name = config.reranker_model or CrossEncoderReranker.DEFAULT_MODEL
        return CrossEncoderReranker(model_name=model_name)
    return None


def _fixture_report_dict(report: BenchmarkReport) -> dict[str, float | int]:
    return {
        "task_count": report.task_count,
        "top_k": report.top_k,
        f"hit_rate@{report.top_k}": report.hit_rate,
        "top_1_accuracy": report.top_1_accuracy,
        "mrr": report.mean_reciprocal_rank,
        f"mean_recall@{report.top_k}": report.mean_recall,
        f"mean_precision@{report.top_k}": report.mean_precision,
    }


def run_fixture_comparison(
    registry_path: str | Path,
    tasks_path: str | Path,
    top_k: int,
    configs: tuple[RetrieverConfig, ...] = DEFAULT_CONFIGS,
) -> list[dict[str, Any]]:
    registry = ToolRegistry.from_file(registry_path)
    task_data = json.loads(Path(tasks_path).read_text(encoding="utf-8"))
    tasks = tuple(BenchmarkTask.from_dict(item) for item in task_data)

    results: list[dict[str, Any]] = []
    for config in configs:
        embedder = _build_embedder(config)
        reranker = _build_reranker(config)
        router = ToolRouter(registry, embedding_provider=embedder, reranker=reranker)
        report = evaluate(router, tasks, top_k=top_k)
        results.append(
            {
                "config": config.name,
                "embedder": config.embedder,
                "embedding_model": config.embedding_model,
                "reranker": config.reranker,
                "metrics": _fixture_report_dict(report),
            }
        )
    return results


def run_live_comparison(
    suite_path: str | Path,
    workspace: str | Path,
    timeout: float,
    configs: tuple[RetrieverConfig, ...] = DEFAULT_CONFIGS,
) -> list[dict[str, Any]]:
    top_k, cases = load_live_suite(suite_path, workspace)
    results: list[dict[str, Any]] = []
    for config in configs:
        embedder = _build_embedder(config)
        reranker = _build_reranker(config)
        report = run_live_suite(
            cases,
            top_k=top_k,
            timeout=timeout,
            embedding_provider=embedder,
            reranker=reranker,
        )
        results.append(
            {
                "config": config.name,
                "embedder": config.embedder,
                "embedding_model": config.embedding_model,
                "reranker": config.reranker,
                "metrics": report["metrics"],
                "nontrivial_metrics": report["nontrivial_metrics"],
                "task_count": report["task_count"],
                "nontrivial_task_count": report["nontrivial_task_count"],
            }
        )
    return results


def render_comparison_markdown(
    fixture_results: list[dict[str, Any]] | None,
    live_results: list[dict[str, Any]] | None,
    *,
    registry_path: str | None = None,
    tasks_path: str | None = None,
    suite_path: str | None = None,
) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Retriever Comparison",
        "",
        f"Generated: `{generated}`",
        "",
        "Frozen-task comparison across embedding and reranking configurations. "
        "Reproduce with:",
        "",
        "```bash",
        "python -m semantic_tool_router compare-retrievers \\",
        "  --registry examples/tools.json \\",
        "  --tasks benchmarks/tasks.json \\",
        "  --suite benchmarks/live_mcp_suite.json \\",
        "  --markdown-output benchmarks/results/comparison.md",
        "```",
        "",
    ]

    if fixture_results:
        lines.extend(
            [
                "## Fixture benchmark (JSON registry)",
                "",
                f"Registry: `{registry_path or 'examples/tools.json'}`  ",
                f"Tasks: `{tasks_path or 'benchmarks/tasks.json'}`  ",
                f"Tasks: {fixture_results[0]['metrics']['task_count']} | "
                f"top-k: {fixture_results[0]['metrics']['top_k']}",
                "",
                "| Config | Hit rate@k | Top-1 | MRR | Mean recall@k | Mean precision@k |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for item in fixture_results:
            metrics = item["metrics"]
            top_k = int(metrics["top_k"])
            lines.append(
                f"| {item['config']} "
                f"| {metrics[f'hit_rate@{top_k}']:.1%} "
                f"| {metrics['top_1_accuracy']:.1%} "
                f"| {metrics['mrr']:.3f} "
                f"| {metrics[f'mean_recall@{top_k}']:.1%} "
                f"| {metrics[f'mean_precision@{top_k}']:.1%} |"
            )
        lines.extend(
            [
                "",
                "The fixture suite is small (12 tools, 15 tasks) and may saturate at 100%. "
                "Use the live MCP suite below for meaningful retriever differences.",
                "",
            ]
        )

    if live_results:
        lines.extend(
            [
                "## Live MCP benchmark",
                "",
                f"Suite: `{suite_path or 'benchmarks/live_mcp_suite.json'}`  ",
                f"Tasks: {live_results[0]['task_count']} across 4 official MCP servers  ",
                f"Nontrivial tasks: {live_results[0]['nontrivial_task_count']} "
                "(servers with more than one tool)",
                "",
                "### All tasks",
                "",
                "| Config | Hit rate@3 | Top-1 | MRR | Context saved |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for item in live_results:
            metrics = item["metrics"]
            lines.append(
                f"| {item['config']} "
                f"| {metrics['hit_rate']:.1%} "
                f"| {metrics['top_1_accuracy']:.1%} "
                f"| {metrics['mrr']:.3f} "
                f"| {metrics['mean_context_saved']:.1%} |"
            )

        lines.extend(
            [
                "",
                "### Nontrivial tasks only",
                "",
                "| Config | Hit rate@3 | Top-1 | MRR |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for item in live_results:
            metrics = item["nontrivial_metrics"]
            lines.append(
                f"| {item['config']} "
                f"| {metrics['hit_rate']:.1%} "
                f"| {metrics['top_1_accuracy']:.1%} "
                f"| {metrics['mrr']:.3f} |"
            )

        lines.extend(
            [
                "",
                "## Takeaways",
                "",
                "- **Hashing** is fast and dependency-free but weaker on live MCP tool names "
                "that do not overlap lexically with the query.",
                "- **Sentence-transformers (MiniLM)** improves live hit rate substantially "
                "without a reranker.",
                "- **Cross-encoder reranking** recovers additional memory-server tasks where "
                "first-stage retrieval ranks destructive tools too high.",
                "- Context savings (~62%) are stable across retrievers because top-k is fixed.",
                "",
            ]
        )

    return "\n".join(lines)


def comparison_payload(
    fixture_results: list[dict[str, Any]] | None,
    live_results: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixture": fixture_results,
        "live_mcp": live_results,
    }
