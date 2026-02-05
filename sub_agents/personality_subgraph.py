"""Personality Manager Sub-Graph - Multi-step personality refinement with observability"""
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
import operator


# ============================================================================
# STATE DEFINITION
# ============================================================================

class PersonalityManagerState(TypedDict):
    """State that flows through the personality manager sub-graph"""
    # Inputs
    operation: str
    story_content: str
    topic: str
    
    # Internal state
    current_traits: list[str]
    current_count: int
    observed_traits: list[str]
    trait_evaluations: dict[str, dict]  # {trait: {score, refinement}}
    traits_to_refine: dict[str, str]  # {old_trait: new_refined_trait}
    traits_to_add: list[str]
    traits_to_remove: list[str]
    
    # Output
    final_traits: list[str]
    decision_log: Annotated[Sequence[str], operator.add]  # Accumulate logs


# ============================================================================
# PROMPTS
# ============================================================================

EXTRACT_TRAITS_PROMPT = """Extract writing personality traits demonstrated in this story.

Story Content:
{story_content}

Topic: {topic}

Instructions:
Identify 1-3 writing personality traits actually demonstrated in this story.
Focus on HOW the story is written, not WHAT it's about.
Each trait should be 3-6 words (e.g. "Philosophical yet accessible", "Layered metaphorical thinking").

Return ONLY a JSON array of trait strings, nothing else.
Example: ["Introspective with sensory detail", "Builds tension through quiet moments"]
"""


EVALUATE_TRAITS_PROMPT = """Evaluate each personality trait for accuracy and refinement opportunities.

Current Traits:
{current_traits}

Recent Story (showing current voice):
{story_content}

Instructions:
For each trait, evaluate:
1. Score (1-10): How accurately does it still describe the evolving voice?
2. Refinement: Could it be refined for better clarity or precision?

Return ONLY a JSON object mapping trait to evaluation:
{{
  "trait_name": {{
    "score": 8,
    "refinement": "Suggested refined version" OR "keep as-is"
  }}
}}

Example:
{{
  "Philosophical yet accessible": {{
    "score": 9,
    "refinement": "keep as-is"
  }},
  "Builds narrative tension": {{
    "score": 7,
    "refinement": "Builds tension through subtle restraint"
  }}
}}
"""


DECIDE_REFINEMENT_PROMPT = """Decide how to refine the personality trait list to maintain 10-12 accurate traits.

Current Traits ({current_count}):
{current_traits}

Trait Evaluations:
{trait_evaluations}

Observed Traits (from story):
{observed_traits}

Target: 10-12 traits total

Instructions:
- Refine traits with refinement suggestions (improve clarity/precision)
- Keep high-scoring traits (8+) that don't need refinement
- Consider adding new observed traits if they represent a consistent new strength
- Remove low-scoring traits (6 or below) that no longer fit
- Maintain diversity of trait types (voice, structure, style, themes)

Return ONLY a JSON object:
{{
  "refine": {{
    "old_trait": "refined_trait"
  }},
  "add": ["new_trait1"],
  "remove": ["outdated_trait"],
  "reasoning": "Brief explanation"
}}
"""


# ============================================================================
# NODE FUNCTIONS
# ============================================================================

def load_current_traits(state: PersonalityManagerState) -> PersonalityManagerState:
    """Node 1: Load current personality traits from file"""
    from tools import read_text_file
    
    try:
        content = read_text_file("personality.txt")
        traits = [line.strip() for line in content.split('\n') if line.strip()]
    except:
        traits = []
    
    state["current_traits"] = traits
    state["current_count"] = len(traits)
    state["decision_log"] = [f"📋 Loaded {len(traits)} current traits"]
    
    return state


def extract_observed_traits(state: PersonalityManagerState) -> PersonalityManagerState:
    """Node 2: Extract traits observed in the story"""
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )
    
    messages = [
        SystemMessage(content="You extract writing personality traits from story content."),
        HumanMessage(content=EXTRACT_TRAITS_PROMPT.format(
            story_content=state.get("story_content", "")[:1000],
            topic=state.get("topic", "")
        ))
    ]
    
    response = llm.invoke(messages)
    
    # Parse JSON response
    import json
    try:
        observed = json.loads(response.content.strip())
        if not isinstance(observed, list):
            observed = []
    except:
        observed = []
    
    state["observed_traits"] = observed[:3]  # Max 3
    state["decision_log"] = [f"🔍 Observed {len(observed)} traits in story: {', '.join(observed)}"]
    
    return state


def evaluate_existing_traits(state: PersonalityManagerState) -> PersonalityManagerState:
    """Node 3: Evaluate current traits for accuracy and refinement"""
    if not state["current_traits"]:
        state["trait_evaluations"] = {}
        state["decision_log"] = ["⚠️ No existing traits to evaluate"]
        return state
    
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.2,
    )
    
    messages = [
        SystemMessage(content="You evaluate personality traits for accuracy and refinement opportunities."),
        HumanMessage(content=EVALUATE_TRAITS_PROMPT.format(
            current_traits="\n".join(f"- {t}" for t in state["current_traits"]),
            story_content=state.get("story_content", "")[:800]
        ))
    ]
    
    response = llm.invoke(messages)
    
    # Parse JSON response
    import json
    try:
        evaluations = json.loads(response.content.strip())
        if not isinstance(evaluations, dict):
            evaluations = {}
    except:
        evaluations = {}
    
    state["trait_evaluations"] = evaluations
    
    # Log summary
    avg_score = sum(e.get("score", 0) for e in evaluations.values()) / len(evaluations) if evaluations else 0
    refinements_suggested = sum(1 for e in evaluations.values() if e.get("refinement", "") != "keep as-is")
    state["decision_log"] = [f"📊 Evaluated traits: Avg score {avg_score:.1f}/10, {refinements_suggested} refinements suggested"]
    
    return state


def decide_refinement(state: PersonalityManagerState) -> PersonalityManagerState:
    """Node 4: Decide how to refine the trait list"""
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.4,
    )
    
    import json
    
    messages = [
        SystemMessage(content="You decide how to refine personality traits for accuracy and clarity."),
        HumanMessage(content=DECIDE_REFINEMENT_PROMPT.format(
            current_count=state["current_count"],
            current_traits="\n".join(f"- {t}" for t in state["current_traits"]),
            trait_evaluations=json.dumps(state["trait_evaluations"], indent=2),
            observed_traits="\n".join(f"- {t}" for t in state["observed_traits"])
        ))
    ]
    
    response = llm.invoke(messages)
    
    # Parse decision
    try:
        decision = json.loads(response.content.strip())
        state["traits_to_refine"] = decision.get("refine", {})
        state["traits_to_add"] = decision.get("add", [])
        state["traits_to_remove"] = decision.get("remove", [])
        reasoning = decision.get("reasoning", "No reasoning provided")
    except:
        state["traits_to_refine"] = {}
        state["traits_to_add"] = []
        state["traits_to_remove"] = []
        reasoning = "Failed to parse decision"
    
    refine_count = len(state["traits_to_refine"])
    add_count = len(state["traits_to_add"])
    remove_count = len(state["traits_to_remove"])
    
    state["decision_log"] = [f"🎯 Decision: Refine {refine_count}, Add {add_count}, Remove {remove_count} | {reasoning}"]
    
    return state


def apply_refinement(state: PersonalityManagerState) -> PersonalityManagerState:
    """Node 5: Apply refinement decisions and write to file"""
    from tools import write_text_file
    
    # Start with current traits
    new_traits = state["current_traits"].copy()
    
    # Remove traits
    for trait in state["traits_to_remove"]:
        if trait in new_traits:
            new_traits.remove(trait)
    
    # Refine traits
    for old_trait, new_trait in state["traits_to_refine"].items():
        if old_trait in new_traits:
            idx = new_traits.index(old_trait)
            new_traits[idx] = new_trait
    
    # Add traits
    for trait in state["traits_to_add"]:
        if trait not in new_traits and len(new_traits) < 12:
            new_traits.append(trait)
    
    # Ensure we have 10-12 traits
    if len(new_traits) > 12:
        # Keep highest scoring traits
        scores = {t: state["trait_evaluations"].get(t, {}).get("score", 5) for t in new_traits}
        new_traits = sorted(new_traits, key=lambda t: scores.get(t, 5), reverse=True)[:12]
    
    state["final_traits"] = new_traits
    
    # Write to file
    write_text_file("personality.txt", '\n'.join(new_traits) + '\n', mode='w')
    
    state["decision_log"] = [f"✅ Updated personality.txt: {state['current_count']} → {len(new_traits)} traits"]
    
    return state


def return_current(state: PersonalityManagerState) -> PersonalityManagerState:
    """Node: Just return current traits (for retrieve operation)"""
    state["final_traits"] = state["current_traits"]
    state["decision_log"] = [f"📖 Retrieved {len(state['current_traits'])} traits"]
    return state


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_by_operation(state: PersonalityManagerState) -> str:
    """Route based on operation type"""
    operation = state.get("operation", "retrieve")
    
    if operation == "retrieve":
        return "retrieve"
    elif operation == "refine":
        return "refine"
    else:
        return "retrieve"  # Default


# ============================================================================
# BUILD THE GRAPH
# ============================================================================

def build_personality_subgraph():
    """Build and compile the personality manager sub-graph"""
    
    graph = StateGraph(PersonalityManagerState)
    
    # Add nodes
    graph.add_node("load", load_current_traits)
    graph.add_node("retrieve", return_current)
    graph.add_node("extract", extract_observed_traits)
    graph.add_node("evaluate", evaluate_existing_traits)
    graph.add_node("decide", decide_refinement)
    graph.add_node("apply", apply_refinement)
    
    # Entry point
    graph.set_entry_point("load")
    
    # Conditional routing after load
    graph.add_conditional_edges(
        "load",
        route_by_operation,
        {
            "retrieve": "retrieve",
            "refine": "extract"
        }
    )
    
    # Retrieve path (simple)
    graph.add_edge("retrieve", END)
    
    # Refine path (complex workflow)
    graph.add_edge("extract", "evaluate")
    graph.add_edge("evaluate", "decide")
    graph.add_edge("decide", "apply")
    graph.add_edge("apply", END)
    
    return graph.compile()


# ============================================================================
# TOOL INTERFACE
# ============================================================================

# Compile the graph once at module load
personality_subgraph = build_personality_subgraph()


def personality_manager_subgraph_tool(
    operation: str = "retrieve",
    story_content: str = "",
    topic: str = ""
) -> str:
    """
    Tool: Personality manager using LangGraph sub-graph
    
    Multi-step workflow with full observability:
    1. Load current personality traits
    2. Extract observed traits from story
    3. Evaluate existing traits (score + refinement suggestions)
    4. Decide refinements (refine/add/remove)
    5. Apply changes and write file
    
    Args:
        operation: "retrieve" or "refine"
        story_content: Story text (for refine)
        topic: Topic written about (for refine)
        
    Returns:
        Result message with decision log
    """
    
    # Invoke the sub-graph
    result = personality_subgraph.invoke({
        "operation": operation,
        "story_content": story_content,
        "topic": topic,
        "current_traits": [],
        "current_count": 0,
        "observed_traits": [],
        "trait_evaluations": {},
        "traits_to_refine": {},
        "traits_to_add": [],
        "traits_to_remove": [],
        "final_traits": [],
        "decision_log": []
    })
    
    # Format response
    if operation == "retrieve":
        traits_list = "\n".join(result["final_traits"])
        return traits_list
    else:
        # Refine operation - return status with decision log
        log = "\n".join(result["decision_log"])
        count_before = result["current_count"]
        count_after = len(result["final_traits"])
        
        return f"✅ Refined personality.txt: {count_before} → {count_after} traits\n\nDecision Log:\n{log}"


__all__ = ["personality_manager_subgraph_tool", "personality_subgraph"]
