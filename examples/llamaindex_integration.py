"""
Example showing how to integrate semantic-tool-router with LlamaIndex.

This demonstrates using semantic-tool-router to retrieve relevant tools dynamically,
instantiating them as LlamaIndex FunctionTools, and passing them to an agent.
"""

from __future__ import annotations

import os

from semantic_tool_router import ToolRegistry, ToolRouter, ToolSpec


# 1. Define typical helper python functions
def search_local_files(directory: str, query: str) -> list[str]:
    """Search for keyword patterns inside local files recursively."""
    return [f"found match for '{query}' in {directory}/main.py"]


def get_git_diff(commit_hash: str) -> str:
    """Retrieve the diff content for a specific git commit hash."""
    return f"diff --git a/src/main.py b/src/main.py ... (diff for {commit_hash})"


def send_slack_notification(channel: str, message: str) -> str:
    """Send an alert or status update message to a Slack channel."""
    return f"Notification sent to channel #{channel}: {message}"


def run_llamaindex_agent_with_routing(user_query: str) -> None:
    # 2. Build a registry of ToolSpecs for routing
    tool_specs = [
        ToolSpec(
            name="search_local_files",
            description="Search for keyword patterns inside local files recursively.",
            tags=("development",),
        ),
        ToolSpec(
            name="get_git_diff",
            description="Retrieve the diff content for a specific git commit hash.",
            tags=("development",),
        ),
        ToolSpec(
            name="send_slack_notification",
            description="Send an alert or status update message to a Slack channel.",
            tags=("communication",),
        ),
    ]

    registry = ToolRegistry(tool_specs)
    router = ToolRouter(registry)

    # 3. Discover relevant tools (retrieve top-2 candidates for the specific task)
    print(f"User Query: {user_query}")
    results = router.discover(user_query, top_k=2)

    print("Dynamically selected tools for LlamaIndex agent:")
    selected_names = []
    for res in results:
        print(f" - {res.tool.name} (score: {res.score:.3f})")
        selected_names.append(res.tool.name)

    # 4. Try constructing the LlamaIndex agent.
    # We catch import errors gracefully so that the routing part still runs and validates
    # regardless of specific LlamaIndex versions or environment dependencies.
    try:
        from llama_index.core.agent import FunctionCallingAgentWorker
        from llama_index.core.tools import FunctionTool
        from llama_index.llms.openai import OpenAI
    except Exception as err:
        print(
            f"\nSkipping LlamaIndex agent execution: LlamaIndex library could not be imported ({err})."
        )
        print("Note: The semantic tool routing succeeded perfectly above!")
        return

    # Map selected names to actual function calls
    tool_functions = {
        "search_local_files": (
            search_local_files,
            "Search for keyword patterns inside local files recursively.",
        ),
        "get_git_diff": (get_git_diff, "Retrieve the diff content for a specific git commit hash."),
        "send_slack_notification": (
            send_slack_notification,
            "Send an alert or status update message to a Slack channel.",
        ),
    }

    selected_tools = []
    for name in selected_names:
        func, desc = tool_functions[name]
        selected_tools.append(
            FunctionTool.from_defaults(
                fn=func,
                name=name,
                description=desc,
            )
        )

    if not os.environ.get("OPENAI_API_KEY"):
        print("\nSkipping LLM agent execution (OPENAI_API_KEY environment variable is not set).")
        return

    llm = OpenAI(model="gpt-4o-mini")
    agent = FunctionCallingAgentWorker.from_tools(selected_tools, llm=llm, verbose=True).as_agent()

    print("Executing LlamaIndex agent...")
    response = agent.chat(user_query)
    print(f"Response: {response}")


if __name__ == "__main__":
    run_llamaindex_agent_with_routing(
        "Inspect the changes introduced by git commit abc123def and search for the updated keywords."
    )
