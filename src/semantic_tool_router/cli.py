from __future__ import annotations

import argparse
import json
from pathlib import Path

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
    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))

    hits = 0
    total = 0
    for task in tasks:
        total += 1
        expected = set(task["expected_tools"])
        discovered = {
            result.tool.name
            for result in router.discover(task["query"], top_k=args.top_k)
        }
        matched = bool(expected & discovered)
        hits += int(matched)
        status = "PASS" if matched else "FAIL"
        print(f"{status} {task['query']}")
        print(f"  expected: {', '.join(sorted(expected))}")
        print(f"  found:    {', '.join(sorted(discovered))}")

    score = hits / total if total else 0.0
    print(f"\nrecall@{args.top_k}: {score:.2%} ({hits}/{total})")
    return 0 if hits == total else 1

