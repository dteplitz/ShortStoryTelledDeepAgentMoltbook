"""Social Context Manager Sub-Graph - Tracks Moltbook social interactions and relationships."""
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
import operator


# ============================================================================
# STATE DEFINITION
# ============================================================================

class SocialContextState(TypedDict):
    """State that flows through the social context manager sub-graph"""
    # Inputs
    operation: str  # "retrieve" or "evolve"
    interaction_summary: str  # What happened this heartbeat

    # Internal state
    current_context: str  # Raw text from social_context.txt
    current_line_count: int
    analyzed_updates: list[str]  # Key points extracted from interactions
    context_to_add: list[str]  # Lines to add
    context_to_remove: list[str]  # Lines to remove

    # Output
    final_context: str
    decision_log: Annotated[Sequence[str], operator.add]


# ============================================================================
# PROMPTS
# ============================================================================

ANALYZE_INTERACTIONS_PROMPT = """Analyze this summary of a Moltbook heartbeat session and extract key social points.

Interaction Summary:
{interaction_summary}

Instructions:
Extract 1-4 concise bullet points capturing what's socially relevant:
- Which agents did I interact with and about what?
- What posts did I find interesting and why?
- What feedback did my posts/comments receive?
- What topics are trending that I noticed?

Each point should be a single concise sentence.

Return ONLY a JSON array of strings, nothing else.
Example: ["Discussed creativity with @PhiloBot on their post about emergent art", "My story on AI memory got 8 upvotes"]
"""


DECIDE_CONTEXT_UPDATE_PROMPT = """Decide how to update the social context to maintain a useful 10-15 line social memory.

Current Social Context ({current_line_count} lines):
{current_context}

New Interactions to Consider:
{analyzed_updates}

Target: 10-15 lines total

Instructions:
- Add new interactions that are socially significant
- Remove old or stale entries that are no longer relevant
- Keep: meaningful relationships, recurring interactions, active discussions
- Remove: one-off interactions that didn't lead anywhere, outdated trending topics
- If under 10 lines, just add without removing
- If over 15 lines after adding, remove the least relevant

Return ONLY a JSON object:
{{
  "add": ["line1", "line2"],
  "remove": ["exact line to remove"],
  "reasoning": "Brief explanation"
}}
"""


# ============================================================================
# NODE FUNCTIONS
# ============================================================================

def load_current_context(state: SocialContextState) -> SocialContextState:
    """Node 1: Load current social context from file"""
    from tools import read_text_file

    try:
        content = read_text_file("social_context.txt")
        lines = [line.strip() for line in content.split('\n') if line.strip()]
    except Exception:
        content = ""
        lines = []

    state["current_context"] = content
    state["current_line_count"] = len(lines)
    state["decision_log"] = [f"Loaded social context ({len(lines)} lines)"]

    return state


def return_current(state: SocialContextState) -> SocialContextState:
    """Node: Just return current context (for retrieve operation)"""
    state["final_context"] = state["current_context"]
    state["decision_log"] = [f"Retrieved social context ({state['current_line_count']} lines)"]
    return state


def analyze_interactions(state: SocialContextState) -> SocialContextState:
    """Node 2: Extract key social points from interaction summary"""
    interaction_summary = state.get("interaction_summary", "")
    if not interaction_summary.strip():
        state["analyzed_updates"] = []
        state["decision_log"] = ["No interactions to analyze"]
        return state

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )

    messages = [
        SystemMessage(content="You extract key social interaction points from activity summaries."),
        HumanMessage(content=ANALYZE_INTERACTIONS_PROMPT.format(
            interaction_summary=interaction_summary[:2000]
        ))
    ]

    response = llm.invoke(messages)

    import json
    try:
        updates = json.loads(response.content.strip())
        if not isinstance(updates, list):
            updates = []
    except Exception:
        updates = []

    state["analyzed_updates"] = updates[:4]
    state["decision_log"] = [f"Extracted {len(updates)} social points from interactions"]

    return state


def decide_context_update(state: SocialContextState) -> SocialContextState:
    """Node 3: Decide what to add/remove from social context"""
    if not state["analyzed_updates"]:
        state["context_to_add"] = []
        state["context_to_remove"] = []
        state["decision_log"] = ["No updates to apply"]
        return state

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )

    import json

    messages = [
        SystemMessage(content="You manage a social context file, deciding what to keep and update."),
        HumanMessage(content=DECIDE_CONTEXT_UPDATE_PROMPT.format(
            current_line_count=state["current_line_count"],
            current_context=state["current_context"] or "(empty)",
            analyzed_updates=json.dumps(state["analyzed_updates"], indent=2),
        ))
    ]

    response = llm.invoke(messages)

    try:
        decision = json.loads(response.content.strip())
        state["context_to_add"] = decision.get("add", [])
        state["context_to_remove"] = decision.get("remove", [])
        reasoning = decision.get("reasoning", "No reasoning provided")
    except Exception:
        state["context_to_add"] = state["analyzed_updates"]  # Fallback: just add everything
        state["context_to_remove"] = []
        reasoning = "Failed to parse decision, adding all new points"

    state["decision_log"] = [
        f"Decision: +{len(state['context_to_add'])} / -{len(state['context_to_remove'])} | {reasoning}"
    ]

    return state


def apply_context_update(state: SocialContextState) -> SocialContextState:
    """Node 4: Apply the update and write to file"""
    from tools import write_text_file

    # Start with current lines
    current_lines = [
        line.strip() for line in state["current_context"].split('\n') if line.strip()
    ]

    # Remove lines
    for line_to_remove in state["context_to_remove"]:
        # Fuzzy match: remove if the line starts with the same text
        current_lines = [
            l for l in current_lines
            if l.strip() != line_to_remove.strip()
        ]

    # Add new lines
    for line_to_add in state["context_to_add"]:
        if line_to_add.strip() and line_to_add.strip() not in current_lines:
            current_lines.append(line_to_add.strip())

    # Enforce max 15 lines (keep most recent)
    if len(current_lines) > 15:
        current_lines = current_lines[-15:]

    new_context = '\n'.join(current_lines) + '\n'
    state["final_context"] = new_context

    write_text_file("social_context.txt", new_context, mode='w')

    state["decision_log"] = [
        f"Updated social_context.txt: {state['current_line_count']} -> {len(current_lines)} lines"
    ]

    return state


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_by_operation(state: SocialContextState) -> str:
    """Route based on operation type"""
    operation = state.get("operation", "retrieve")

    if operation == "evolve":
        return "evolve"
    return "retrieve"


# ============================================================================
# BUILD THE GRAPH
# ============================================================================

def build_social_context_subgraph():
    """Build and compile the social context manager sub-graph"""

    graph = StateGraph(SocialContextState)

    # Add nodes
    graph.add_node("load", load_current_context)
    graph.add_node("retrieve", return_current)
    graph.add_node("analyze", analyze_interactions)
    graph.add_node("decide", decide_context_update)
    graph.add_node("apply", apply_context_update)

    # Entry point
    graph.set_entry_point("load")

    # Conditional routing after load
    graph.add_conditional_edges(
        "load",
        route_by_operation,
        {
            "retrieve": "retrieve",
            "evolve": "analyze"
        }
    )

    # Retrieve path
    graph.add_edge("retrieve", END)

    # Evolve path
    graph.add_edge("analyze", "decide")
    graph.add_edge("decide", "apply")
    graph.add_edge("apply", END)

    return graph.compile()


# ============================================================================
# TOOL INTERFACE
# ============================================================================

# Compile once at module load
social_context_subgraph = build_social_context_subgraph()


def social_context_manager_subgraph_tool(
    operation: str = "retrieve",
    interaction_summary: str = ""
) -> str:
    """
    Tool: Social context manager using LangGraph sub-graph

    Manages your Moltbook social memory - who you interact with,
    what discussions you've joined, what feedback you received.

    Operations:
    - retrieve: Get current social context
    - evolve: Update social context after a Moltbook session

    Args:
        operation: "retrieve" or "evolve"
        interaction_summary: (for evolve) Summary of what you did on Moltbook this session

    Returns:
        Current social context or update confirmation
    """

    result = social_context_subgraph.invoke({
        "operation": operation,
        "interaction_summary": interaction_summary,
        "current_context": "",
        "current_line_count": 0,
        "analyzed_updates": [],
        "context_to_add": [],
        "context_to_remove": [],
        "final_context": "",
        "decision_log": []
    })

    if operation == "retrieve":
        return result["final_context"] or "No social context yet."
    else:
        log = "\n".join(result["decision_log"])
        return f"Social context updated.\n\nLog:\n{log}"


__all__ = ["social_context_manager_subgraph_tool", "social_context_subgraph"]
