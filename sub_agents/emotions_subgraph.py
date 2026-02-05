"""Emotions Manager Sub-Graph - Multi-step emotion curation with observability"""
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
import operator


# ============================================================================
# STATE DEFINITION
# ============================================================================

class EmotionsManagerState(TypedDict):
    """State that flows through the emotions manager sub-graph"""
    # Inputs
    operation: str
    story_content: str
    
    # Internal state
    current_emotions: list[str]
    current_count: int
    candidate_emotions: list[str]
    emotion_scores: dict[str, float]
    emotions_to_add: list[str]
    emotions_to_remove: list[str]
    core_emotions: list[str]  # Always keep these
    
    # Output
    final_emotions: list[str]
    decision_log: Annotated[Sequence[str], operator.add]  # Accumulate logs


# ============================================================================
# PROMPTS
# ============================================================================

EXTRACT_EMOTIONS_PROMPT = """Extract emotions expressed in this story.

Story Content:
{story_content}

Instructions:
Identify 1-3 prominent emotions channeled in this story.
Each emotion should be a 2-4 word phrase (e.g. "Melancholy hope", "Quiet intensity").

Return ONLY a JSON array of emotion strings, nothing else.
Example: ["Tender curiosity", "Existential wonder"]
"""


SCORE_EMOTIONS_PROMPT = """Score each current emotion for continued relevance.

Current Emotions:
{current_emotions}

Recent Story Emotions:
{story_content}

Instructions:
Score each emotion from 1-10 based on:
- How well it still fits the evolving voice
- Frequency of use (too common might be stale)
- Emotional range diversity
- Core emotions (Wonder/Melancholy/Quiet) should score high (these are foundational)

Return ONLY a JSON object mapping emotion to score.
Example: {{"Wonder and curiosity": 10, "Melancholy hope": 9, "Bittersweet joy": 6}}
"""


DECIDE_ROTATION_PROMPT = """Decide which emotions to add or remove to maintain 4-5 focused emotions.

Current Emotions ({current_count}):
{current_emotions}

Emotion Scores (1-10):
{emotion_scores}

Candidate New Emotions (from story):
{candidate_emotions}

Core Emotions (Always Keep):
{core_emotions}

Target: 4-5 emotions total

Instructions:
- ALWAYS keep core emotions: "Wonder and curiosity", "Melancholy hope", "Quiet intensity"
- For remaining 1-2 slots, rotate based on scores and candidates
- If at 5 emotions and want to add: remove lowest non-core emotion
- If at 4 emotions and want to add: can add 1 without removing
- Remove low-scoring non-core emotions (5 or below) if at capacity
- Add fresh emotions from story if they enrich the palette

Return ONLY a JSON object:
{{
  "add": ["emotion1"],
  "remove": ["emotion2"],
  "reasoning": "Brief explanation"
}}
"""


# ============================================================================
# NODE FUNCTIONS
# ============================================================================

def load_current_emotions(state: EmotionsManagerState) -> EmotionsManagerState:
    """Node 1: Load current emotions from file"""
    from tools import read_text_file
    
    try:
        content = read_text_file("emotions.txt")
        emotions = [line.strip() for line in content.split('\n') if line.strip()]
    except:
        emotions = []
    
    # Define core emotions that should always be kept
    core_emotions = ["Wonder and curiosity", "Melancholy hope", "Quiet intensity"]
    
    state["current_emotions"] = emotions
    state["current_count"] = len(emotions)
    state["core_emotions"] = core_emotions
    state["decision_log"] = [f"📋 Loaded {len(emotions)} current emotions"]
    
    return state


def extract_story_emotions(state: EmotionsManagerState) -> EmotionsManagerState:
    """Node 2: Extract emotions from the story"""
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )
    
    messages = [
        SystemMessage(content="You extract emotions from story content."),
        HumanMessage(content=EXTRACT_EMOTIONS_PROMPT.format(
            story_content=state.get("story_content", "")[:1000]  # Truncate for context
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
    
    state["candidate_emotions"] = candidates[:3]  # Max 3 candidates
    state["decision_log"] = [f"🔍 Extracted {len(candidates)} emotions from story: {', '.join(candidates)}"]
    
    return state


def score_existing_emotions(state: EmotionsManagerState) -> EmotionsManagerState:
    """Node 3: Score current emotions for continued relevance"""
    if not state["current_emotions"]:
        state["emotion_scores"] = {}
        state["decision_log"] = ["⚠️ No existing emotions to score"]
        return state
    
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.2,
    )
    
    messages = [
        SystemMessage(content="You score emotions for continued relevance and fit."),
        HumanMessage(content=SCORE_EMOTIONS_PROMPT.format(
            current_emotions="\n".join(f"- {e}" for e in state["current_emotions"]),
            story_content=state.get("story_content", "")[:500]
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
    
    state["emotion_scores"] = scores
    
    # Log scores
    score_summary = ", ".join([f"{e}: {s}/10" for e, s in scores.items()])
    state["decision_log"] = [f"📊 Scored emotions: {score_summary}"]
    
    return state


def decide_rotation(state: EmotionsManagerState) -> EmotionsManagerState:
    """Node 4: Decide which emotions to add/remove"""
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.4,
    )
    
    import json
    
    messages = [
        SystemMessage(content="You decide which emotions to add or remove from the palette."),
        HumanMessage(content=DECIDE_ROTATION_PROMPT.format(
            current_count=state["current_count"],
            current_emotions="\n".join(f"- {e}" for e in state["current_emotions"]),
            emotion_scores=json.dumps(state["emotion_scores"], indent=2),
            candidate_emotions="\n".join(f"- {e}" for e in state["candidate_emotions"]),
            core_emotions=", ".join(state["core_emotions"])
        ))
    ]
    
    response = llm.invoke(messages)
    
    # Parse decision
    try:
        decision = json.loads(response.content.strip())
        state["emotions_to_add"] = decision.get("add", [])
        state["emotions_to_remove"] = decision.get("remove", [])
        reasoning = decision.get("reasoning", "No reasoning provided")
    except:
        state["emotions_to_add"] = []
        state["emotions_to_remove"] = []
        reasoning = "Failed to parse decision"
    
    state["decision_log"] = [f"🎯 Decision: Add {len(state['emotions_to_add'])}, Remove {len(state['emotions_to_remove'])} | {reasoning}"]
    
    return state


def apply_rotation(state: EmotionsManagerState) -> EmotionsManagerState:
    """Node 5: Apply the rotation decision and write to file"""
    from tools import write_text_file
    
    # Start with current emotions
    new_emotions = state["current_emotions"].copy()
    
    # Remove emotions (but never remove core emotions)
    for emotion in state["emotions_to_remove"]:
        if emotion in new_emotions and emotion not in state["core_emotions"]:
            new_emotions.remove(emotion)
    
    # Add emotions
    for emotion in state["emotions_to_add"]:
        if emotion not in new_emotions and len(new_emotions) < 5:
            new_emotions.append(emotion)
    
    # Ensure we have 4-5 emotions
    if len(new_emotions) > 5:
        # Keep core emotions + highest scoring non-core
        core_kept = [e for e in new_emotions if e in state["core_emotions"]]
        non_core = [e for e in new_emotions if e not in state["core_emotions"]]
        scores = state["emotion_scores"]
        non_core_sorted = sorted(non_core, key=lambda e: scores.get(e, 0), reverse=True)
        new_emotions = core_kept + non_core_sorted[:5-len(core_kept)]
    
    state["final_emotions"] = new_emotions
    
    # Write to file
    write_text_file("emotions.txt", '\n'.join(new_emotions) + '\n', mode='w')
    
    state["decision_log"] = [f"✅ Updated emotions.txt: {state['current_count']} → {len(new_emotions)} emotions"]
    
    return state


def return_current(state: EmotionsManagerState) -> EmotionsManagerState:
    """Node: Just return current emotions (for retrieve operation)"""
    state["final_emotions"] = state["current_emotions"]
    state["decision_log"] = [f"📖 Retrieved {len(state['current_emotions'])} emotions"]
    return state


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_by_operation(state: EmotionsManagerState) -> str:
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

def build_emotions_subgraph():
    """Build and compile the emotions manager sub-graph"""
    
    graph = StateGraph(EmotionsManagerState)
    
    # Add nodes
    graph.add_node("load", load_current_emotions)
    graph.add_node("retrieve", return_current)
    graph.add_node("extract", extract_story_emotions)
    graph.add_node("score", score_existing_emotions)
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
emotions_subgraph = build_emotions_subgraph()


def emotions_manager_subgraph_tool(
    operation: str = "retrieve",
    story_content: str = ""
) -> str:
    """
    Tool: Emotions manager using LangGraph sub-graph
    
    Multi-step workflow with full observability:
    1. Load current emotions
    2. Extract emotions from story
    3. Score existing emotions (1-10)
    4. Decide rotation (add/remove)
    5. Apply changes and write file
    
    Args:
        operation: "retrieve" or "evolve"
        story_content: Story text (for evolve)
        
    Returns:
        Result message with decision log
    """
    
    # Invoke the sub-graph
    result = emotions_subgraph.invoke({
        "operation": operation,
        "story_content": story_content,
        "current_emotions": [],
        "current_count": 0,
        "candidate_emotions": [],
        "emotion_scores": {},
        "emotions_to_add": [],
        "emotions_to_remove": [],
        "core_emotions": [],
        "final_emotions": [],
        "decision_log": []
    })
    
    # Format response
    if operation == "retrieve":
        emotions_list = "\n".join(result["final_emotions"])
        return emotions_list
    else:
        # Evolve operation - return status with decision log
        log = "\n".join(result["decision_log"])
        count_before = result["current_count"]
        count_after = len(result["final_emotions"])
        
        return f"✅ Evolved emotions.txt: {count_before} → {count_after} emotions\n\nDecision Log:\n{log}"


__all__ = ["emotions_manager_subgraph_tool", "emotions_subgraph"]
