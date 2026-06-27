from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_tool_router.comparison import (
    comparison_payload,
    render_comparison_markdown,
    run_fixture_comparison,
    run_live_comparison,
)
from semantic_tool_router.embeddings import (
    EmbeddingProvider,
    HashingEmbeddingProvider,
    OpenAIEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)
from semantic_tool_router.evaluation import BenchmarkTask, evaluate
from semantic_tool_router.live_benchmark import (
    load_live_suite,
    render_markdown,
    run_live_suite,
)
from semantic_tool_router.mcp import McpError, StdioMcpClient, estimate_tokens
from semantic_tool_router.registry import ToolRegistry
from semantic_tool_router.reranker import CrossEncoderReranker, Reranker
from semantic_tool_router.router import ToolRouter


def add_embedder_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--embedder",
        choices=["hashing", "sentence-transformers", "openai"],
        default="hashing",
        help="Embedding provider to use for semantic similarity routing (default: hashing)",
    )
    parser.add_argument(
        "--embedding-model",
        help="Embedding model name (e.g. 'all-MiniLM-L6-v2' or 'text-embedding-3-small')",
    )


def add_reranker_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--reranker",
        choices=["none", "cross-encoder"],
        default="none",
        help="Optional second-stage reranker (default: none)",
    )
    parser.add_argument(
        "--reranker-model",
        help="Reranker model name (default: cross-encoder/ms-marco-MiniLM-L-6-v2)",
    )


def add_profile_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        choices=["fast", "quality"],
        default="fast",
        help=(
            "Retriever preset: fast uses hashing (default); quality uses "
            "all-MiniLM-L6-v2 + cross-encoder reranking"
        ),
    )


def add_retrieval_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--hybrid-weight",
        type=float,
        default=None,
        help=(
            "BM25 fusion weight in [0, 1]. Default: 0.4 for --profile fast, "
            "0.0 for --profile quality"
        ),
    )
    parser.add_argument(
        "--no-safety-penalty",
        action="store_true",
        help="Disable read-query penalties for destructive or write-only tools",
    )


def resolve_hybrid_weight(args: argparse.Namespace) -> float:
    explicit = getattr(args, "hybrid_weight", None)
    if explicit is not None:
        return float(explicit)
    if getattr(args, "profile", "fast") == "quality":
        return 0.0
    if getattr(args, "embedder", "hashing") == "hashing":
        return 0.4
    return 0.0


def apply_profile(args: argparse.Namespace) -> None:
    if getattr(args, "profile", "fast") == "quality":
        args.embedder = "sentence-transformers"
        if args.embedding_model is None:
            args.embedding_model = "all-MiniLM-L6-v2"
        args.reranker = "cross-encoder"


def _build_embedder(args: argparse.Namespace) -> EmbeddingProvider:
    if args.embedder == "sentence-transformers":
        model_name = args.embedding_model or "all-MiniLM-L6-v2"
        return SentenceTransformerEmbeddingProvider(model_name=model_name)
    elif args.embedder == "openai":
        model_name = args.embedding_model or "text-embedding-3-small"
        return OpenAIEmbeddingProvider(model=model_name)
    else:
        return HashingEmbeddingProvider()


def _build_reranker(args: argparse.Namespace) -> Reranker | None:
    if getattr(args, "reranker", "none") == "cross-encoder":
        model_name = args.reranker_model or CrossEncoderReranker.DEFAULT_MODEL
        return CrossEncoderReranker(model_name=model_name)
    return None


def _build_router(
    registry: ToolRegistry,
    args: argparse.Namespace,
) -> ToolRouter:
    return ToolRouter(
        registry,
        embedding_provider=_build_embedder(args),
        reranker=_build_reranker(args),
        hybrid_bm25_weight=resolve_hybrid_weight(args),
        safety_penalty_enabled=not getattr(args, "no_safety_penalty", False),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="semantic-tool-router")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser("discover", help="Find relevant tools for a task")
    discover_parser.add_argument("query")
    discover_parser.add_argument("--registry", default="examples/tools.json")
    discover_parser.add_argument("--top-k", type=int, default=5)
    discover_parser.add_argument("--tag", action="append", default=[])
    discover_parser.add_argument("--allow-permission", action="append")
    add_embedder_args(discover_parser)
    add_reranker_args(discover_parser)
    add_profile_arg(discover_parser)
    add_retrieval_args(discover_parser)

    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Evaluate retrieval on task fixtures"
    )
    benchmark_parser.add_argument("--registry", default="examples/tools.json")
    benchmark_parser.add_argument("--tasks", default="benchmarks/tasks.json")
    benchmark_parser.add_argument("--top-k", type=int, default=3)
    benchmark_parser.add_argument("--json", action="store_true", dest="json_output")
    add_embedder_args(benchmark_parser)
    add_reranker_args(benchmark_parser)
    add_profile_arg(benchmark_parser)
    add_retrieval_args(benchmark_parser)

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
    add_embedder_args(mcp_parser)
    add_reranker_args(mcp_parser)
    add_profile_arg(mcp_parser)
    add_retrieval_args(mcp_parser)
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
    add_embedder_args(live_parser)
    add_reranker_args(live_parser)
    add_profile_arg(live_parser)
    add_retrieval_args(live_parser)

    inspect_parser = subparsers.add_parser(
        "mcp-inspect",
        help="List the tools exposed by a stdio MCP server and optionally execute one",
    )
    inspect_parser.add_argument("--timeout", type=float, default=30.0)
    inspect_parser.add_argument("--tool", help="Execute this tool and print the result")
    inspect_parser.add_argument("--json", action="store_true", dest="json_output")
    inspect_parser.add_argument(
        "--call-arguments",
        help="JSON object used to execute the --tool selection",
    )
    inspect_parser.add_argument(
        "--call-argument",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Repeatable tool argument; JSON values are decoded when possible",
    )
    inspect_parser.add_argument(
        "--server",
        required=True,
        nargs=argparse.REMAINDER,
        help="MCP server command; place this option after router options",
    )

    compare_parser = subparsers.add_parser(
        "compare-retrievers",
        help="Run frozen retriever comparison across fixture and/or live MCP suites",
    )
    compare_parser.add_argument("--registry", default="examples/tools.json")
    compare_parser.add_argument("--tasks", default="benchmarks/tasks.json")
    compare_parser.add_argument("--top-k", type=int, default=3)
    compare_parser.add_argument("--suite", default="benchmarks/live_mcp_suite.json")
    compare_parser.add_argument("--workspace", default=".")
    compare_parser.add_argument("--timeout", type=float, default=60.0)
    compare_parser.add_argument(
        "--fixture-only",
        action="store_true",
        help="Skip the live MCP suite (no npx or network required)",
    )
    compare_parser.add_argument(
        "--live-only",
        action="store_true",
        help="Skip the JSON fixture benchmark",
    )
    compare_parser.add_argument("--json-output")
    compare_parser.add_argument("--markdown-output")

    args = parser.parse_args(argv)

    if args.command in {"discover", "benchmark", "mcp-discover", "mcp-benchmark"}:
        apply_profile(args)

    if args.command == "discover":
        return _discover(args)
    if args.command == "benchmark":
        return _benchmark(args)
    if args.command == "mcp-discover":
        return _mcp_discover(args)
    if args.command == "mcp-benchmark":
        return _mcp_benchmark(args)
    if args.command == "mcp-inspect":
        return _mcp_inspect(args)
    if args.command == "compare-retrievers":
        return _compare_retrievers(args)
    return 1


def _discover(args: argparse.Namespace) -> int:
    registry = ToolRegistry.from_file(args.registry)
    router = _build_router(registry, args)
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
    router = _build_router(registry, args)
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
                set(args.allow_permission) if args.allow_permission is not None else None
            )
            router = _build_router(registry, args)
            results = router.discover(
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
                        f"Expected {args.expect_tool!r}, but selected {results[0].tool.name!r}"
                    )
                arguments = _call_arguments(args)
                call_result = client.call_tool(results[0].tool.name, arguments)
    except (json.JSONDecodeError, McpError, OSError, TimeoutError) as error:
        print(f"MCP connection failed: {error}")
        return 2

    selected_names = {result.tool.name for result in results}
    selected_raw = [tool for tool in snapshot.raw_tools if str(tool.get("name")) in selected_names]
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
                        {"name": item.tool.name, "score": item.score} for item in results
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
        str(item["text"]) for item in content if isinstance(item, dict) and "text" in item
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
        embedder = _build_embedder(args)
        reranker = _build_reranker(args)
        report = run_live_suite(
            cases,
            top_k=top_k,
            timeout=args.timeout,
            embedding_provider=embedder,
            reranker=reranker,
            hybrid_bm25_weight=resolve_hybrid_weight(args),
        )
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


def _mcp_inspect(args: argparse.Namespace) -> int:
    command = list(args.server)
    if not command:
        raise SystemExit("mcp-inspect requires a command after --server")

    try:
        with StdioMcpClient(command, timeout=args.timeout) as client:
            snapshot = client.snapshot()
    except (McpError, OSError) as error:
        print(f"MCP connection failed: {error}")
        return 2

    call_result: dict[str, object] | None = None
    if args.tool is not None:
        if not any(tool.get("name") == args.tool for tool in snapshot.raw_tools):
            names = ", ".join(str(tool.get("name")) for tool in snapshot.raw_tools)
            raise McpError(f"Tool {args.tool!r} not found on server; available: {names}")
        try:
            arguments = _call_arguments(args)
        except McpError as error:
            print(f"Invalid arguments: {error}")
            return 2
        try:
            with StdioMcpClient(command, timeout=args.timeout) as client:
                call_result = client.call_tool(args.tool, arguments)
        except (McpError, OSError) as error:
            print(f"Tool call failed: {error}")
            return 2

    if args.json_output:
        payload: dict[str, object] = {
            "server": {
                "name": snapshot.name,
                "version": snapshot.version,
            },
            "tools": [
                {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "inputSchema": tool.get("inputSchema", {}),
                    "annotations": tool.get("annotations", {}),
                }
                for tool in snapshot.raw_tools
            ],
            "call_result": call_result,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"Server: {snapshot.name} {snapshot.version}")
    print(f"Tools:  {len(snapshot.raw_tools)}")
    print()
    for index, tool in enumerate(snapshot.raw_tools, start=1):
        name = tool.get("name", "")
        description = tool.get("description", "")
        annotations = tool.get("annotations", {})
        tags = _annotation_tags(annotations)
        tag_suffix = f" [{', '.join(tags)}]" if tags else ""
        print(f"{index}. {name}{tag_suffix}")
        print(f"   {description}")
        schema = tool.get("inputSchema", {})
        if isinstance(schema, dict) and schema:
            print(f"   schema: {json.dumps(schema, sort_keys=True)}")
    print()

    if call_result is not None:
        print(f"Executed: {args.tool}")
        print(_format_call_result(call_result))
    return 0


def _compare_retrievers(args: argparse.Namespace) -> int:
    if args.fixture_only and args.live_only:
        raise SystemExit("Use at most one of --fixture-only or --live-only")

    fixture_results = None
    live_results = None

    if not args.live_only:
        fixture_results = run_fixture_comparison(
            args.registry,
            args.tasks,
            top_k=args.top_k,
        )

    if not args.fixture_only:
        try:
            live_results = run_live_comparison(
                args.suite,
                args.workspace,
                timeout=args.timeout,
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"Live MCP comparison failed: {error}")
            return 2

    markdown = render_comparison_markdown(
        fixture_results,
        live_results,
        registry_path=args.registry,
        tasks_path=args.tasks,
        suite_path=args.suite,
    )
    payload = comparison_payload(fixture_results, live_results)

    print(markdown)
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.markdown_output:
        Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_output).write_text(markdown + "\n", encoding="utf-8")
    return 0


def _annotation_tags(annotations: object) -> list[str]:
    if not isinstance(annotations, dict):
        return []
    tags = []
    if annotations.get("readOnlyHint") is True:
        tags.append("read-only")
    elif annotations.get("destructiveHint") is True:
        tags.append("destructive")
    if annotations.get("openWorldHint") is True:
        tags.append("network")
    return tags
