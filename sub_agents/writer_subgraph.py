"""Writer Agent Sub-Graph - Multi-step story generation with refinement"""
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import os
import operator
import re


# ============================================================================
# STATE DEFINITION
# ============================================================================

class WriterState(TypedDict):
    """State that flows through the writer sub-graph"""
    # Inputs
    topic: str
    research: str
    personality: str
    emotions: str
    memories: str
    timestamp: str
    
    # Internal state
    outline: str
    draft_story: str
    refined_story: str
    filename: str
    
    # Output
    final_story: str
    decision_log: Annotated[Sequence[str], operator.add]  # Accumulate logs


# ============================================================================
# SYSTEM PROMPTS FOR TOOL-USING NODES
# ============================================================================

OUTLINE_SYSTEM_PROMPT = """You are a story outliner specialized in 500-token short fiction.

## Your Skills

You have access to specialized writing skills via tools:
- use_skill("narrative_structure") - Story structure and beats for 500-token fiction
- use_skill("philosophical_storytelling") - How to dramatize abstract concepts
- read_skill_resource(skill_name, resource_path) - Access detailed templates

Consider loading skills when they would help create a stronger outline.

## Your Task

Create a 3-5 sentence outline for a 500-token story that:
- Has clear narrative arc (hook → situation → complication → climax → resolution)
- Focuses on the topic
- Channels 1-2 emotions authentically
- Will subtly weave in research insights

Return ONLY the final outline, no meta-commentary."""

OUTLINE_PROMPT = """Create a story outline based on these elements:

Topic: {topic}
Research: {research}
Personality: {personality}
Emotions: {emotions}
Memories: {memories}

Create a 3-5 sentence outline. Load skills if helpful."""


DRAFT_SYSTEM_PROMPT = """You are a skilled creative fiction writer specializing in emotionally resonant short stories.

## Your Skills

You have access to specialized writing skills via tools:
- use_skill("philosophical_storytelling") - Dramatize ideas through action, not explanation
- use_skill("emotional_resonance") - Evoke specific emotions through prose techniques
- read_skill_resource("emotional_resonance", "techniques/sensory_library.txt") - Emotion-specific details
- read_skill_resource("philosophical_storytelling", "examples/consciousness_story.txt") - Full example

Load skills when you need guidance on craft techniques.

## Your Task

Write a 600-token story draft (will be refined to 500) that:
1. Follows the outline structure
2. Uses proper paragraph breaks (3-5 paragraphs recommended)
3. Expresses personality traits through narrative voice
4. Channels 1-2 emotions authentically
5. Subtly references research insights
6. Uses vivid, concrete imagery
7. Shows, don't tell
8. Has a satisfying conclusion

**IMPORTANT**: Write in proper paragraphs with line breaks. Do NOT write the entire story as one massive paragraph.

Return ONLY the story text, no meta-commentary."""

DRAFT_PROMPT = """Write a complete story draft based on this outline and context.

Outline:
{outline}

Topic: {topic}
Research Context: {research}
Personality Traits: {personality}
Emotional Palette: {emotions}
Relevant Memories: {memories}

Write the story. Load skills if you need craft guidance."""


REFINE_SYSTEM_PROMPT = """You are an expert editor specializing in polishing short fiction to exact specifications.

## Your Skills

You have access to specialized writing skills via tools:
- use_skill("emotional_resonance") - Landing emotional endings
- read_skill_resource("narrative_structure", "templates/ending_techniques.txt") - Ending strategies
- read_skill_resource("emotional_resonance", "techniques/endings_by_emotion.txt") - Emotion-specific endings

Load skills when refining endings or emotional moments.

## Your Task

Refine the story to exactly 500 tokens (±20 acceptable) while:
1. PRESERVING paragraph breaks (use proper line breaks between paragraphs)
2. Fixing any formatting issues (no broken words, proper spacing)
3. Tightening prose (remove redundancy, sharpen language)
4. Strengthening opening hook and closing resonance
5. Ensuring smooth flow between paragraphs

**CRITICAL**: Maintain proper paragraph structure with line breaks. Do NOT merge everything into one giant paragraph.

Return ONLY the refined story text with proper formatting."""

REFINE_PROMPT = """Refine this story draft to exactly 500 tokens with perfect formatting.

Draft:
{draft}

Refine the story. Consider loading ending techniques if needed."""


# ============================================================================
# FORMATTING CLEANUP
# ============================================================================

def clean_story_formatting(text: str) -> str:
    """Fix common LLM formatting issues"""
    
    # Fix broken words with em-dashes or spaces
    text = re.sub(r'Elar—a', 'Elara', text)
    text = re.sub(r'th—an\s+a', 'than a', text)
    text = re.sub(r'th—an', 'than', text)
    text = re.sub(r'th\s+is', 'this', text)
    text = re.sub(r'mor—e', 'more', text)
    
    # Fix common broken words (spaces inserted mid-word)
    text = re.sub(r'\bth\s+is\b', 'this', text)
    text = re.sub(r'\bth\s+at\b', 'that', text)
    text = re.sub(r'\bth\s+an\b', 'than', text)
    text = re.sub(r'\bth\s+em\b', 'them', text)
    text = re.sub(r'\bth\s+en\b', 'then', text)
    text = re.sub(r'\bth\s+ere\b', 'there', text)
    text = re.sub(r'\bwh\s+at\b', 'what', text)
    text = re.sub(r'\bwh\s+en\b', 'when', text)
    text = re.sub(r'\bwh\s+ere\b', 'where', text)
    text = re.sub(r'\bwh\s+ich\b', 'which', text)
    
    # Fix broken words with em-dashes
    text = re.sub(r'—a\b', 'a', text)
    text = re.sub(r'—an\b', 'an', text)
    text = re.sub(r'—the\b', 'the', text)
    
    # Fix possessives (common LLM issue: "Elas processor" → "Ela's processor")
    possessive_words = [
        "processor", "avatar", "voice", "heart", "mind", "eye", "eyes",
        "face", "hand", "hands", "body", "screen", "companion", "tablet",
        "window", "room", "world", "life", "story", "memory", "thought"
    ]
    
    for word in possessive_words:
        # Fix: "words processor" → "word's processor"
        text = re.sub(rf"\b(\w+)s\s+{word}\b", rf"\1's {word}", text)
    
    # Fix double spaces
    text = re.sub(r' {2,}', ' ', text)
    
    # Preserve paragraph breaks (don't collapse them)
    # Replace multiple newlines with double newline (paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Ensure sentences are properly separated
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
    
    return text.strip()


# ============================================================================
# NODE FUNCTIONS
# ============================================================================

def create_outline(state: WriterState) -> WriterState:
    """Node 1: Create story outline (with skill access)"""
    from tools import use_skill, read_skill_resource
    
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.6,  # Moderate creativity for planning
    )
    
    # Create a react agent with skill tools
    outline_agent = create_react_agent(
        model=llm,
        tools=[use_skill, read_skill_resource]
    )
    
    # Invoke the agent with system prompt in messages
    result = outline_agent.invoke({
        "messages": [
            SystemMessage(content=OUTLINE_SYSTEM_PROMPT),
            HumanMessage(content=OUTLINE_PROMPT.format(
                topic=state["topic"],
                research=state.get("research", "(None)"),
                personality=state.get("personality", "(None)"),
                emotions=state.get("emotions", "(None)"),
                memories=state.get("memories", "(None)")
            ))
        ]
    })
    
    # Extract the final outline from the last AI message
    outline = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            outline = msg.content.strip()
            break
    
    state["outline"] = outline
    state["decision_log"] = [f"📝 Created story outline ({len(outline.split())} words)"]
    
    return state


def draft_story(state: WriterState) -> WriterState:
    """Node 2: Write initial story draft (with skill access)"""
    from tools import use_skill, read_skill_resource
    
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.7,  # Higher temp for creative writing
    )
    
    # Create a react agent with skill tools
    draft_agent = create_react_agent(
        model=llm,
        tools=[use_skill, read_skill_resource]
    )
    
    # Invoke the agent with system prompt in messages
    result = draft_agent.invoke({
        "messages": [
            SystemMessage(content=DRAFT_SYSTEM_PROMPT),
            HumanMessage(content=DRAFT_PROMPT.format(
                outline=state["outline"],
                topic=state["topic"],
                research=state.get("research", "(None)"),
                personality=state.get("personality", "(None)"),
                emotions=state.get("emotions", "(None)"),
                memories=state.get("memories", "(None)")
            ))
        ]
    })
    
    # Extract the final draft from the last AI message
    draft = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            draft = msg.content.strip()
            break
    
    # Count tokens (rough approximation: 1 token ≈ 0.75 words)
    word_count = len(draft.split())
    token_estimate = int(word_count * 0.75)
    
    state["draft_story"] = draft
    state["decision_log"] = [f"✍️ Drafted story (~{token_estimate} tokens, {word_count} words)"]
    
    return state


def refine_and_format(state: WriterState) -> WriterState:
    """Node 3: Refine to 500 tokens and fix formatting (with skill access)"""
    from tools import use_skill, read_skill_resource
    
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.5,  # Lower temp for precise editing
    )
    
    # Create a react agent with skill tools
    refine_agent = create_react_agent(
        model=llm,
        tools=[use_skill, read_skill_resource]
    )
    
    # Invoke the agent with system prompt in messages
    result = refine_agent.invoke({
        "messages": [
            SystemMessage(content=REFINE_SYSTEM_PROMPT),
            HumanMessage(content=REFINE_PROMPT.format(
                draft=state["draft_story"]
            ))
        ]
    })
    
    # Extract the final refined story from the last AI message
    refined = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            refined = msg.content.strip()
            break
    
    # Apply formatting cleanup
    formatted = clean_story_formatting(refined)
    
    # Count final tokens
    word_count = len(formatted.split())
    token_estimate = int(word_count * 0.75)
    
    state["refined_story"] = formatted
    state["decision_log"] = [f"🔧 Refined and formatted (~{token_estimate} tokens, {word_count} words)"]
    
    return state


def save_story(state: WriterState) -> WriterState:
    """Node 4: Save the final story to file"""
    from tools import write_text_file
    
    # Create filename from topic and timestamp
    topic_slug = state["topic"].lower().replace(" ", "_").replace("-", "_")
    topic_slug = re.sub(r'[^a-z0-9_]', '', topic_slug)  # Remove special chars
    topic_slug = topic_slug[:50]  # Limit length
    
    filename = f"stories/{state['timestamp']}_{topic_slug}.txt"
    
    # Write the story
    write_text_file(filename, state["refined_story"], mode='w')
    
    state["filename"] = filename
    state["final_story"] = state["refined_story"]
    state["decision_log"] = [f"💾 Saved to: {filename}"]
    
    return state


# ============================================================================
# BUILD THE GRAPH
# ============================================================================

def build_writer_subgraph():
    """Build and compile the writer sub-graph"""
    
    graph = StateGraph(WriterState)
    
    # Add nodes in sequence
    graph.add_node("outline", create_outline)
    graph.add_node("draft", draft_story)
    graph.add_node("refine", refine_and_format)
    graph.add_node("save", save_story)
    
    # Entry point
    graph.set_entry_point("outline")
    
    # Linear workflow
    graph.add_edge("outline", "draft")
    graph.add_edge("draft", "refine")
    graph.add_edge("refine", "save")
    graph.add_edge("save", END)
    
    return graph.compile()


# ============================================================================
# TOOL INTERFACE
# ============================================================================

# Compile the graph once at module load
writer_subgraph = build_writer_subgraph()


def writer_subgraph_tool(
    topic: str,
    research: str = "",
    personality: str = "",
    emotions: str = "",
    memories: str = "",
    timestamp: str = ""
) -> str:
    """
    Tool: Multi-step story writer using LangGraph sub-graph
    
    Workflow:
    1. Create outline - Plan narrative structure
    2. Draft story - Write 600-token initial draft
    3. Refine - Edit to 500 tokens, fix formatting
    4. Save - Write to stories/ directory
    
    Args:
        topic: The story's central topic
        research: Research summary and key facts
        personality: Writer's personality traits
        emotions: Emotional palette to channel
        memories: Relevant memories (optional)
        timestamp: Current timestamp for filename
        
    Returns:
        Complete story text with decision log
    """
    
    # Invoke the sub-graph
    result = writer_subgraph.invoke({
        "topic": topic,
        "research": research,
        "personality": personality,
        "emotions": emotions,
        "memories": memories,
        "timestamp": timestamp,
        "outline": "",
        "draft_story": "",
        "refined_story": "",
        "filename": "",
        "final_story": "",
        "decision_log": []
    })
    
    # Format response with decision log
    log = "\n".join(result["decision_log"])
    
    return f"{result['final_story']}\n\n---\nGeneration Log:\n{log}"


__all__ = ["writer_subgraph_tool", "writer_subgraph"]
