from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_tool_router.evaluation import BenchmarkTask, evaluate
from semantic_tool_router.live_benchmark import (
    load_live_suite,
    render_markdown,
    run_live_suite,
)
from semantic_tool_router.mcp import McpError, StdioMcpClient, estimate_tokens
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

    mcp_parser = subparsers.add_parser(
        "mcp-discover",
        help="Import and rank tools from a live stdio MCP server",
    )
    mcp_parser.add_argument("query")
    mcp_parser.add_argument("--top-k", type=int, default=3)
    mcp_parser.add_argument("--timeout", type=float, default=30.0)
    mcp_parser.add_argument("--json", action="store_true", dest="json_output")
    mcp_parser.add_argument("--allow-permission", action="append")
    mcp_parser.add_argument(
        "--call-arguments",
        help="JSON object used to execute the highest-ranked tool",
    )
    mcp_parser.add_argument(
        "--call-argument",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Repeatable tool argument; JSON values are decoded when possible",
    )
    mcp_parser.add_argument(
        "--expect-tool",
        help="Abort execution unless this tool is ranked first",
    )
    mcp_parser.add_argument(
        "--server",
        required=True,
        nargs=argparse.REMAINDER,
        help="MCP server command; place this option after router options",
    )

    live_parser = subparsers.add_parser(
        "mcp-benchmark",
        help="Evaluate discovery across multiple live MCP servers",
    )
    live_parser.add_argument("--suite", default="benchmarks/live_mcp_suite.json")
    live_parser.add_argument("--workspace", default=".")
    live_parser.add_argument("--timeout", type=float, default=60.0)
    live_parser.add_argument("--json-output")
    live_parser.add_argument("--markdown-output")

    args = parser.parse_args(argv)

    if args.command == "discover":
        return _discover(args)
    if args.command == "benchmark":
        return _benchmark(args)
    if args.command == "mcp-discover":
        return _mcp_discover(args)
    if args.command == "mcp-benchmark":
        return _mcp_benchmark(args)
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


def _mcp_discover(args: argparse.Namespace) -> int:
    command = list(args.server)
    if not command:
        raise SystemExit("mcp-discover requires a command after --server")

    try:
        with StdioMcpClient(command, timeout=args.timeout) as client:
            snapshot = client.snapshot()
            registry = ToolRegistry(list(snapshot.tools))
            allow_permissions = (
                set(args.allow_permission)
                if args.allow_permission is not None
                else None
            )
            results = ToolRouter(registry).discover(
                args.query,
                top_k=args.top_k,
                allow_permissions=allow_permissions,
            )
            call_result = None
            should_call = args.call_arguments is not None or bool(args.call_argument)
            if should_call:
                if not results:
                    raise McpError("No tool was selected for execution")
                if not args.expect_tool:
                    raise McpError("Execution requires --expect-tool")
                if results[0].tool.name != args.expect_tool:
                    raise McpError(
                        f"Expected {args.expect_tool!r}, but selected "
                        f"{results[0].tool.name!r}"
                    )
                arguments = _call_arguments(args)
                call_result = client.call_tool(results[0].tool.name, arguments)
    except (json.JSONDecodeError, McpError, OSError, TimeoutError) as error:
        print(f"MCP connection failed: {error}")
        return 2

    selected_names = {result.tool.name for result in results}
    selected_raw = [
        tool for tool in snapshot.raw_tools if str(tool.get("name")) in selected_names
    ]
    all_tokens = estimate_tokens(snapshot.raw_tools)
    selected_tokens = estimate_tokens(selected_raw)
    savings = 1.0 - (selected_tokens / all_tokens) if all_tokens else 0.0

    if args.json_output:
        print(
            json.dumps(
                {
                    "server": {
                        "name": snapshot.name,
                        "version": snapshot.version,
                    },
                    "query": args.query,
                    "available_tools": len(snapshot.tools),
                    "selected_tools": [
                        {"name": item.tool.name, "score": item.score}
                        for item in results
                    ],
                    "estimated_context_tokens": {
                        "all_tools": all_tokens,
                        "selected_tools": selected_tokens,
                        "saved_fraction": savings,
                    },
                    "call_result": call_result,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    print(f"Connected: {snapshot.name} {snapshot.version}")
    print(f"Imported:  {len(snapshot.tools)} live MCP tools")
    print(f"Task:      {args.query}")
    print()
    for index, result in enumerate(results, start=1):
        print(f"{index}. {result.tool.name} ({result.score:.3f})")
        print(f"   {result.tool.description}")
    print()
    print(f"Estimated tool context: {all_tokens} -> {selected_tokens} tokens")
    print(f"Estimated context saved: {savings:.1%}")
    if call_result is not None:
        print()
        print(f"Executed: {results[0].tool.name}")
        print(_format_call_result(call_result))
    return 0


def _format_call_result(result: dict[str, object]) -> str:
    content = result.get("content", [])
    if not isinstance(content, list):
        return json.dumps(result, indent=2)
    text_parts = [
        str(item["text"])
        for item in content
        if isinstance(item, dict) and "text" in item
    ]
    return "\n".join(text_parts) if text_parts else json.dumps(result, indent=2)


def _call_arguments(args: argparse.Namespace) -> dict[str, object]:
    if args.call_arguments is not None and args.call_argument:
        raise McpError("Use either --call-arguments or --call-argument, not both")
    if args.call_arguments is not None:
        value = json.loads(args.call_arguments)
        if not isinstance(value, dict):
            raise McpError("--call-arguments must be a JSON object")
        return value

    arguments: dict[str, object] = {}
    for item in args.call_argument:
        key, separator, raw_value = item.partition("=")
        if not separator or not key:
            raise McpError("--call-argument must use KEY=VALUE")
        try:
            arguments[key] = json.loads(raw_value)
        except json.JSONDecodeError:
            arguments[key] = raw_value
    return arguments


def _mcp_benchmark(args: argparse.Namespace) -> int:
    try:
        top_k, cases = load_live_suite(args.suite, args.workspace)
        report = run_live_suite(cases, top_k=top_k, timeout=args.timeout)
    except (McpError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Live MCP benchmark failed: {error}")
        return 2

    markdown = render_markdown(report)
    print(markdown)
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.markdown_output:
        Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_output).write_text(markdown + "\n", encoding="utf-8")
    return 0
