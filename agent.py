import os
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from langchain_openai import ChatOpenAI

from prompts import SYSTEM_PROMPT
from tools import reset_tool_counters, tools

# Import specialized sub-agents
from sub_agents import (
    research_deep_agent,  # Nested Deep Agent
    memory_deep_agent,  # Nested Deep Agent
    emotions_manager_subgraph_tool,  # Sub-graph
    topics_manager_subgraph_tool,  # Sub-graph
    personality_manager_subgraph_tool,  # Sub-graph
    writer_subgraph_tool,  # Sub-graph
    social_context_manager_subgraph_tool,  # Sub-graph
)


def build_agent():
    """
    Construct a Deep Agent using the official creator (planning + fs tools included).
    
    Note: Skills are NOT loaded here - they're available directly to the writer_subgraph
    nodes where they're actually needed for craft guidance.
    """
    # Configure the OpenAI model
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.2,
    )
    
    # Configure backend to allow file access in agent state
    def make_backend(runtime):
        return StateBackend(runtime)
    
    # Combine basic tools with specialized sub-agents
    # Note: use_skill and read_skill_resource are NOT in main agent tools
    # They're available to writer_subgraph nodes internally
    all_tools = tools + [
        research_deep_agent,                 # Nested Deep Agent
        memory_deep_agent,                   # Nested Deep Agent
        emotions_manager_subgraph_tool,      # Sub-graph
        topics_manager_subgraph_tool,        # Sub-graph
        personality_manager_subgraph_tool,   # Sub-graph
        writer_subgraph_tool,                # Sub-graph (with skills internally)
        social_context_manager_subgraph_tool,  # Sub-graph (Moltbook social context)
    ]
    
    return create_deep_agent(
        tools=all_tools,
        system_prompt=SYSTEM_PROMPT,  # No skills in main agent prompt
        model=llm,
        backend=make_backend,
    )


__all__ = ["build_agent", "reset_tool_counters"]

