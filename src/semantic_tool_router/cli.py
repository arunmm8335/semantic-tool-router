from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_tool_router.evaluation import BenchmarkTask, evaluate
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.router import ToolRouter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="semantic-tool-router")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser("discover", help="Find relevant tools for a task")
    discover_parser.add_argument("query")
    discover_parser.add_argument("--registry", default="examples/tools.json")
    discover_parser.add_argument("--top-k", type=int, default=5)
    discover_parser.add_argument("--tag", action="append", default=[])
    discover_parser.add_argument("--allow-permission", action="append")

    benchmark_parser = subparsers.add_parser("benchmark", help="Evaluate retrieval on task fixtures")
    benchmark_parser.add_argument("--registry", default="examples/tools.json")
    benchmark_parser.add_argument("--tasks", default="benchmarks/tasks.json")
    benchmark_parser.add_argument("--top-k", type=int, default=3)
    benchmark_parser.add_argument("--json", action="store_true", dest="json_output")

    args = parser.parse_args(argv)

    if args.command == "discover":
        return _discover(args)
    if args.command == "benchmark":
        return _benchmark(args)
    return 1


def _discover(args: argparse.Namespace) -> int:
    registry = ToolRegistry.from_file(args.registry)
    router = ToolRouter(registry)
    allow_permissions = set(args.allow_permission) if args.allow_permission is not None else None
    results = router.discover(
        args.query,
        top_k=args.top_k,
        require_tags=set(args.tag) if args.tag else None,
        allow_permissions=allow_permissions,
    )

    for index, result in enumerate(results, start=1):
        print(f"{index}. {result.tool.name} ({result.score:.3f})")
        print(f"   {result.tool.description}")
        for reason in result.reasons:
            print(f"   - {reason}")
    return 0


def _benchmark(args: argparse.Namespace) -> int:
    registry = ToolRegistry.from_file(args.registry)
    router = ToolRouter(registry)
    task_data = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    tasks = tuple(BenchmarkTask.from_dict(item) for item in task_data)
    report = evaluate(router, tasks, top_k=args.top_k)

    if args.json_output:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        for item in report.evaluations:
            status = "PASS" if item.hit else "FAIL"
            print(f"{status} {item.task.query}")
            print(f"  expected: {', '.join(item.task.expected_tools)}")
            print(f"  ranked:   {', '.join(item.retrieved_tools)}")

        print(f"\ntasks:              {report.task_count}")
        print(f"hit rate@{args.top_k}:         {report.hit_rate:.2%}")
        print(f"top-1 accuracy:     {report.top_1_accuracy:.2%}")
        print(f"MRR:                {report.mean_reciprocal_rank:.3f}")
        print(f"mean recall@{args.top_k}:      {report.mean_recall:.2%}")
        print(f"mean precision@{args.top_k}:   {report.mean_precision:.2%}")

    return 0 if report.hit_rate == 1.0 else 1
