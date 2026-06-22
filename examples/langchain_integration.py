"""
Example showing how to integrate semantic-tool-router with LangChain.

This demonstrates using semantic-tool-router to dynamically select
a subset of tools from a large registry before passing them to a LangChain agent,
reducing context size and improving routing accuracy.
"""

from __future__ import annotations

import os

from semantic_tool_router import ToolRegistry, ToolRouter, ToolSpec


# 1. Define typical tool functions
def read_database(query: str) -> str:
    """Execute a query against the local SQLite database."""
    return f"Result for database query: {query}"


def fetch_web_page(url: str) -> str:
    """Fetch and extract text content from a web page."""
    return f"Web page content of {url}"


def generate_image(prompt: str) -> str:
    """Generate an image using a text description."""
    return f"Image generated for: {prompt}"


def run_langchain_agent_with_routing(user_query: str) -> None:
    # 2. Build a registry of ToolSpecs for routing
    tool_specs = [
        ToolSpec(
            name="read_database",
            description="Execute a query against the local SQLite database.",
            input_schema={"query": {"type": "string"}},
            tags=("database",),
        ),
        ToolSpec(
            name="fetch_web_page",
            description="Fetch and extract text content from a web page.",
            input_schema={"url": {"type": "string"}},
            tags=("web",),
        ),
        ToolSpec(
            name="generate_image",
            description="Generate an image using a text description.",
            input_schema={"prompt": {"type": "string"}},
            tags=("graphics",),
        ),
    ]

    registry = ToolRegistry(tool_specs)
    router = ToolRouter(registry)

    # 3. Discover relevant tools (retrieve top-2 candidates for the specific task)
    print(f"User Query: {user_query}")
    results = router.discover(user_query, top_k=2)

    print("Dynamically selected tools:")
    selected_names = []
    for res in results:
        print(f" - {res.tool.name} (score: {res.score:.3f})")
        selected_names.append(res.tool.name)

    # 4. Try constructing the LangChain agent.
    # Since LangChain's Pydantic v1 dependency is currently incompatible with Python 3.14+,
    # we catch import errors gracefully so the routing part still runs and validates.
    try:
        from langchain.agents import AgentExecutor, create_openai_tools_agent
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_core.tools import tool
        from langchain_openai import ChatOpenAI
    except Exception as err:
        print(
            f"\nSkipping LangChain agent execution: LangChain library could not be imported on this Python version ({err})."
        )
        print("Note: The semantic tool routing succeeded perfectly above!")
        return

    # Wrap the functions as LangChain tools
    lc_tools_map = {
        "read_database": tool(read_database),
        "fetch_web_page": tool(fetch_web_page),
        "generate_image": tool(generate_image),
    }
    selected_lc_tools = [lc_tools_map[name] for name in selected_names]

    if not os.environ.get("OPENAI_API_KEY"):
        print("\nSkipping LLM agent execution (OPENAI_API_KEY environment variable is not set).")
        return

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant with access to a dynamically retrieved subset of tools.",
            ),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_openai_tools_agent(llm, selected_lc_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=selected_lc_tools, verbose=True)

    print("Executing agent...")
    agent_executor.invoke({"input": user_query})


if __name__ == "__main__":
    run_langchain_agent_with_routing(
        "Find user orders where status is pending and check their shipping info on the web."
    )
