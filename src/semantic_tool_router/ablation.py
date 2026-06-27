from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from semantic_tool_router.embeddings import HashingEmbeddingProvider
from semantic_tool_router.evaluation import BenchmarkTask, evaluate
from semantic_tool_router.models import SEARCH_INDEX_MODES, SearchIndexMode
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.router import ToolRouter


def run_input_ablation(
    registry_path: str | Path,
    tasks_path: str | Path,
    top_k: int,
    modes: tuple[SearchIndexMode, ...] = SEARCH_INDEX_MODES,
) -> list[dict[str, Any]]:
    registry = ToolRegistry.from_file(registry_path)
    task_data = json.loads(Path(tasks_path).read_text(encoding="utf-8"))
    tasks = tuple(BenchmarkTask.from_dict(item) for item in task_data)
    embedder = HashingEmbeddingProvider()

    results: list[dict[str, Any]] = []
    for mode in modes:
        router = ToolRouter(
            registry,
            embedding_provider=embedder,
            hybrid_bm25_weight=0.4,
            index_mode=mode,
        )
        report = evaluate(router, tasks, top_k=top_k)
        results.append(
            {
                "index_mode": mode,
                "metrics": {
                    "task_count": report.task_count,
                    "top_k": report.top_k,
                    f"hit_rate@{report.top_k}": report.hit_rate,
                    "top_1_accuracy": report.top_1_accuracy,
                    "mrr": report.mean_reciprocal_rank,
                },
            }
        )
    return results


def render_ablation_markdown(
    results: list[dict[str, Any]],
    *,
    registry_path: str,
    tasks_path: str,
) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Retrieval Input Ablation",
        "",
        f"Generated: `{generated}`",
        "",
        f"Registry: `{registry_path}`  ",
        f"Tasks: `{tasks_path}`  ",
        "Embedder: hashing (BM25 weight 0.4)",
        "",
        "| Index mode | Hit rate@k | Top-1 | MRR |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in results:
        metrics = item["metrics"]
        top_k = int(metrics["top_k"])
        lines.append(
            f"| `{item['index_mode']}` "
            f"| {metrics[f'hit_rate@{top_k}']:.1%} "
            f"| {metrics['top_1_accuracy']:.1%} "
            f"| {metrics['mrr']:.3f} |"
        )
    lines.extend(
        [
            "",
            "Reproduce:",
            "",
            "```bash",
            "python -m semantic_tool_router ablation \\",
            f"  --registry {registry_path} \\",
            f"  --tasks {tasks_path} \\",
            "  --markdown-output benchmarks/results/ablation.md",
            "```",
            "",
        ]
    )
    return "\n".join(lines)
