import argparse
import os
from langchain_core.messages import HumanMessage

from agent import build_agent, reset_tool_counters


def run_once(query: str, thread_id: str = "demo-run"):
    graph_app = build_agent()
    reset_tool_counters()
    initial_state = {"messages": [HumanMessage(content=query)]}

    # Stream events for visibility and capture final state
    final_state = None
    for event in graph_app.stream(
        initial_state, {"configurable": {"thread_id": thread_id}}
    ):
        for _, value in event.items():
            print(value)
            final_state = value  # Capture the last state

    # Display final response from the single execution
    if final_state and "messages" in final_state:
        print("\nFinal response:\n", final_state["messages"][-1].content)
    
    # Show LangSmith trace link if enabled
    if os.getenv("LANGCHAIN_TRACING_V2") == "true":
        print(f"\n📊 View detailed trace at: https://smith.langchain.com/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creative Story Writer Agent - Automatically generates stories based on interesting topics."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="Create a story.",
        help="Custom prompt to send to the agent (optional - defaults to automatic story creation).",
    )
    parser.add_argument(
        "--thread-id",
        default="story-writer",
        help="Thread ID for LangGraph configurable context.",
    )
    args = parser.parse_args()
    run_once(args.query, thread_id=args.thread_id)

