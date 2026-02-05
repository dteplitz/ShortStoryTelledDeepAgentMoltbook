"""Topics Manager Sub-Graph - Multi-step topic curation with observability"""
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
import operator


# ============================================================================
# STATE DEFINITION
# ============================================================================

class TopicsManagerState(TypedDict):
    """State that flows through the topics manager sub-graph"""
    # Inputs
    operation: str
    research_content: str
    topic_used: str
    
    # Internal state
    current_topics: list[str]
    current_count: int
    candidate_topics: list[str]
    topic_scores: dict[str, float]
    topics_to_add: list[str]
    topics_to_remove: list[str]
    
    # Output
    final_topics: list[str]
    decision_log: Annotated[Sequence[str], operator.add]  # Accumulate logs


# ============================================================================
# PROMPTS
# ============================================================================

EXTRACT_CANDIDATES_PROMPT = """Extract potential new topics from this research.

Research Content:
{research_content}

Topic Just Explored:
{topic_used}

Instructions:
Identify 2-3 fascinating new topics or sub-topics discovered in the research.
These should be compelling angles worth exploring in future stories.

Return ONLY a JSON array of topic strings, nothing else.
Example: ["Quantum entanglement in AI systems", "Ethical frameworks for AGI"]
"""


SCORE_EXISTING_PROMPT = """Score each current topic for continued relevance and interest.

Current Topics:
{current_topics}

Recently Explored:
Topic: {topic_used}
Research: {research_content}

Instructions:
Score each topic from 1-10 based on:
- Continued interest and freshness (not exhausted)
- Relevance to evolving focus
- Potential for new stories
- Overlap with recently explored topics (score lower if too similar)

Return ONLY a JSON object mapping topic to score.
Example: {{"AI consciousness": 9, "Quantum physics": 6, "Friendship": 4}}
"""


DECIDE_ROTATION_PROMPT = """Decide which topics to add or remove to maintain 5-6 focused topics.

Current Topics ({current_count}):
{current_topics}

Topic Scores (1-10):
{topic_scores}

Candidate New Topics:
{candidate_topics}

Target: 5-6 topics total

Instructions:
- If at 6 topics and want to add: remove lowest-scoring topics
- If at 5 topics and want to add: can add 1 without removing
- If at 4 topics: definitely add, don't remove
- Keep high-scoring topics (8+)
- Remove low-scoring topics (5 or below) if at capacity
- Prioritize diversity and freshness

Return ONLY a JSON object:
{{
  "add": ["topic1", "topic2"],
  "remove": ["topic3"],
  "reasoning": "Brief explanation"
}}
"""


# ============================================================================
# NODE FUNCTIONS
# ============================================================================

def load_current_topics(state: TopicsManagerState) -> TopicsManagerState:
    """Node 1: Load current topics from file"""
    from tools import read_text_file
    
    try:
        content = read_text_file("topics.txt")
        topics = [line.strip() for line in content.split('\n') if line.strip()]
    except:
        topics = []
    
    state["current_topics"] = topics
    state["current_count"] = len(topics)
    state["decision_log"] = [f"📋 Loaded {len(topics)} current topics"]
    
    return state


def extract_candidate_topics(state: TopicsManagerState) -> TopicsManagerState:
    """Node 2: Extract new topic candidates from research"""
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,  # Lower temp for extraction
    )
    
    messages = [
        SystemMessage(content="You extract new topics from research content."),
        HumanMessage(content=EXTRACT_CANDIDATES_PROMPT.format(
            research_content=state.get("research_content", ""),
            topic_used=state.get("topic_used", "")
        ))
    ]
    
    response = llm.invoke(messages)
    
    # Parse JSON response
    import json
    try:
        candidates = json.loads(response.content.strip())
        if not isinstance(candidates, list):
            candidates = []
    except:
        candidates = []
    
    state["candidate_topics"] = candidates[:3]  # Max 3 candidates
    state["decision_log"] = [f"🔍 Found {len(candidates)} candidate topics: {', '.join(candidates)}"]
    
    return state


def score_existing_topics(state: TopicsManagerState) -> TopicsManagerState:
    """Node 3: Score current topics for continued relevance"""
    if not state["current_topics"]:
        state["topic_scores"] = {}
        state["decision_log"] = ["⚠️ No existing topics to score"]
        return state
    
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.2,  # Very low temp for consistent scoring
    )
    
    messages = [
        SystemMessage(content="You score topics for continued relevance and interest."),
        HumanMessage(content=SCORE_EXISTING_PROMPT.format(
            current_topics="\n".join(f"- {t}" for t in state["current_topics"]),
            topic_used=state.get("topic_used", ""),
            research_content=state.get("research_content", "")[:500]  # Truncate for context
        ))
    ]
    
    response = llm.invoke(messages)
    
    # Parse JSON response
    import json
    try:
        scores = json.loads(response.content.strip())
        if not isinstance(scores, dict):
            scores = {}
    except:
        scores = {}
    
    state["topic_scores"] = scores
    
    # Log scores
    score_summary = ", ".join([f"{t}: {s}/10" for t, s in scores.items()])
    state["decision_log"] = [f"📊 Scored topics: {score_summary}"]
    
    return state


def decide_rotation(state: TopicsManagerState) -> TopicsManagerState:
    """Node 4: Decide which topics to add/remove"""
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.4,  # Moderate temp for decision-making
    )
    
    import json
    
    messages = [
        SystemMessage(content="You decide which topics to add or remove from the collection."),
        HumanMessage(content=DECIDE_ROTATION_PROMPT.format(
            current_count=state["current_count"],
            current_topics="\n".join(f"- {t}" for t in state["current_topics"]),
            topic_scores=json.dumps(state["topic_scores"], indent=2),
            candidate_topics="\n".join(f"- {t}" for t in state["candidate_topics"])
        ))
    ]
    
    response = llm.invoke(messages)
    
    # Parse decision
    try:
        decision = json.loads(response.content.strip())
        state["topics_to_add"] = decision.get("add", [])
        state["topics_to_remove"] = decision.get("remove", [])
        reasoning = decision.get("reasoning", "No reasoning provided")
    except:
        state["topics_to_add"] = []
        state["topics_to_remove"] = []
        reasoning = "Failed to parse decision"
    
    state["decision_log"] = [f"🎯 Decision: Add {len(state['topics_to_add'])}, Remove {len(state['topics_to_remove'])} | {reasoning}"]
    
    return state


def apply_rotation(state: TopicsManagerState) -> TopicsManagerState:
    """Node 5: Apply the rotation decision and write to file"""
    from tools import write_text_file
    
    # Start with current topics
    new_topics = state["current_topics"].copy()
    
    # Remove topics
    for topic in state["topics_to_remove"]:
        if topic in new_topics:
            new_topics.remove(topic)
    
    # Add topics
    for topic in state["topics_to_add"]:
        if topic not in new_topics and len(new_topics) < 6:
            new_topics.append(topic)
    
    # Ensure we have 5-6 topics
    if len(new_topics) > 6:
        new_topics = new_topics[:6]
    
    state["final_topics"] = new_topics
    
    # Write to file
    write_text_file("topics.txt", '\n'.join(new_topics) + '\n', mode='w')
    
    state["decision_log"] = [f"✅ Updated topics.txt: {state['current_count']} → {len(new_topics)} topics"]
    
    return state


def return_current(state: TopicsManagerState) -> TopicsManagerState:
    """Node: Just return current topics (for retrieve operation)"""
    state["final_topics"] = state["current_topics"]
    state["decision_log"] = [f"📖 Retrieved {len(state['current_topics'])} topics"]
    return state


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_by_operation(state: TopicsManagerState) -> str:
    """Route based on operation type"""
    operation = state.get("operation", "retrieve")
    
    if operation == "retrieve":
        return "retrieve"
    elif operation == "evolve":
        return "evolve"
    else:
        return "retrieve"  # Default


# ============================================================================
# BUILD THE GRAPH
# ============================================================================

def build_topics_subgraph():
    """Build and compile the topics manager sub-graph"""
    
    graph = StateGraph(TopicsManagerState)
    
    # Add nodes
    graph.add_node("load", load_current_topics)
    graph.add_node("retrieve", return_current)
    graph.add_node("extract", extract_candidate_topics)
    graph.add_node("score", score_existing_topics)
    graph.add_node("decide", decide_rotation)
    graph.add_node("apply", apply_rotation)
    
    # Entry point
    graph.set_entry_point("load")
    
    # Conditional routing after load
    graph.add_conditional_edges(
        "load",
        route_by_operation,
        {
            "retrieve": "retrieve",
            "evolve": "extract"
        }
    )
    
    # Retrieve path (simple)
    graph.add_edge("retrieve", END)
    
    # Evolve path (complex workflow)
    graph.add_edge("extract", "score")
    graph.add_edge("score", "decide")
    graph.add_edge("decide", "apply")
    graph.add_edge("apply", END)
    
    return graph.compile()


# ============================================================================
# TOOL INTERFACE
# ============================================================================

# Compile the graph once at module load
topics_subgraph = build_topics_subgraph()


def topics_manager_subgraph_tool(
    operation: str = "retrieve",
    research_content: str = "",
    topic_used: str = ""
) -> str:
    """
    Tool: Topics manager using LangGraph sub-graph
    
    Multi-step workflow with full observability:
    1. Load current topics
    2. Extract candidates from research
    3. Score existing topics (1-10)
    4. Decide rotation (add/remove)
    5. Apply changes and write file
    
    Args:
        operation: "retrieve" or "evolve"
        research_content: Research summary (for evolve)
        topic_used: Topic that was just explored (for evolve)
        
    Returns:
        Result message with decision log
    """
    
    # Invoke the sub-graph
    result = topics_subgraph.invoke({
        "operation": operation,
        "research_content": research_content,
        "topic_used": topic_used,
        "current_topics": [],
        "current_count": 0,
        "candidate_topics": [],
        "topic_scores": {},
        "topics_to_add": [],
        "topics_to_remove": [],
        "final_topics": [],
        "decision_log": []
    })
    
    # Format response
    if operation == "retrieve":
        topics_list = "\n".join(result["final_topics"])
        return topics_list
    else:
        # Evolve operation - return status with decision log
        log = "\n".join(result["decision_log"])
        count_before = result["current_count"]
        count_after = len(result["final_topics"])
        
        return f"✅ Evolved topics.txt: {count_before} → {count_after} topics\n\nDecision Log:\n{log}"


__all__ = ["topics_manager_subgraph_tool", "topics_subgraph"]
