# Deep Agent + LangGraph Architecture Guide

## 🎯 Overview

This document explains how `create_deep_agent` from LangChain works with LangGraph and sub-graphs, and how we leverage this architecture in the Story Writer Agent.

---

## 🔑 Key Insight

**`create_deep_agent` IS LangGraph!**

It's not a separate framework - it's a **convenience wrapper** that creates a LangGraph StateGraph for you with pre-configured nodes for agent orchestration.

```python
# When you call this:
agent = create_deep_agent(
    tools=[...],
    system_prompt="...",
    model=llm,
    backend=make_backend
)

# Behind the scenes, it creates a LangGraph like this:
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)          # LLM decision maker
graph.add_node("tools", tools_node)          # Tool execution
graph.add_conditional_edges("agent", should_continue, {
    "continue": "tools",
    "end": END
})
graph.add_edge("tools", "agent")
return graph.compile(checkpointer=...)
```

---

## 🏗️ Architecture Layers

### **Layer 1: LangGraph (Foundation)**

The core orchestration framework:
- StateGraph for workflow management
- Nodes for processing steps
- Edges for flow control
- State management for context

### **Layer 2: Deep Agent (Convenience Wrapper)**

Built on LangGraph, adds:
- Agent/Tools loop pre-configured
- Planning capabilities
- StateBackend for virtual filesystem
- Long-term memory persistence
- Simplified API

### **Layer 3: Your Custom Tools**

Your application logic:
- Basic tools (internet_search, file operations)
- Manager agents (emotions, topics, personality)
- Can be simple functions OR invoke sub-graphs

---

## 🎨 Three Approaches to Sub-Graphs

### **Approach 1: Simple Tool Functions (Current - Phase 2)**

**What it looks like:**

```python
# sub_agents/emotions_manager.py
def emotions_manager_agent(story_content: str) -> str:
    """Simple function with single LLM call"""
    llm = ChatOpenAI(temperature=0.4)
    response = llm.invoke([
        SystemMessage("You are an emotions curator..."),
        HumanMessage(f"Story: {story_content}...")
    ])
    # Parse, enforce limits, write file
    return "✅ Updated emotions.txt"

# agent.py
create_deep_agent(
    tools=[emotions_manager_agent, ...]
)
```

**Architecture:**
```
Deep Agent (LangGraph wrapper)
├─ Agent Node: "What should I do next?"
├─ Tools Node:
│  ├─ internet_search()
│  ├─ read_text_file()
│  └─ emotions_manager_agent() ← Single LLM call
└─ Loop: Agent → Tools → Agent → ...
```

**Pros:**
- ✅ Simple and straightforward
- ✅ Easy to understand and maintain
- ✅ Fast to implement (~70 lines per manager)
- ✅ Works perfectly with Deep Agent
- ✅ Good enough for most use cases

**Cons:**
- ❌ Single LLM call = limited reasoning
- ❌ No internal workflow steps
- ❌ Decision process is opaque

**LangSmith Trace:**
```
Main Agent Run
├─ Agent Node: "I'll call emotions_manager_agent"
├─ Tool: emotions_manager_agent
│  └─ LLM Call: "Here's the updated emotions list"
└─ Agent Node: "Done!"
```

---

### **Approach 2: Sub-Graphs Wrapped as Tools (Recommended Future)**

**What it looks like:**

```python
# sub_agents/emotions_manager.py
from langgraph.graph import StateGraph, END
from typing import TypedDict

class EmotionsState(TypedDict):
    story_content: str
    current_emotions: list[str]
    story_emotions: list[str]
    decisions: dict
    final_emotions: list[str]
    status: str

# Node 1: Analyze story
def analyze_story_node(state: EmotionsState) -> EmotionsState:
    """Extract emotions expressed in story"""
    llm = ChatOpenAI(temperature=0.4)
    response = llm.invoke([
        SystemMessage("Identify 2-3 emotions in this story"),
        HumanMessage(state["story_content"])
    ])
    state["story_emotions"] = parse_emotions(response.content)
    return state

# Node 2: Evaluate current
def evaluate_current_node(state: EmotionsState) -> EmotionsState:
    """Assess which current emotions are still valuable"""
    llm = ChatOpenAI(temperature=0.3)
    # Score each emotion...
    return state

# Node 3: Decide rotation
def decide_rotation_node(state: EmotionsState) -> EmotionsState:
    """Decide what to keep, add, or remove"""
    current_count = len(state["current_emotions"])
    story_emotions = state["story_emotions"]
    
    if current_count >= 5:
        # Need to remove before adding
        # Use LLM to decide which to remove
        pass
    
    state["final_emotions"] = [...]  # 4-5 emotions
    return state

# Node 4: Update file
def update_file_node(state: EmotionsState) -> EmotionsState:
    """Write to emotions.txt"""
    from tools import write_text_file
    write_text_file("emotions.txt", '\n'.join(state["final_emotions"]) + '\n')
    state["status"] = f"✅ Updated to {len(state['final_emotions'])} emotions"
    return state

# Build the sub-graph
def create_emotions_subgraph():
    graph = StateGraph(EmotionsState)
    
    graph.add_node("analyze_story", analyze_story_node)
    graph.add_node("evaluate_current", evaluate_current_node)
    graph.add_node("decide_rotation", decide_rotation_node)
    graph.add_node("update_file", update_file_node)
    
    graph.set_entry_point("analyze_story")
    graph.add_edge("analyze_story", "evaluate_current")
    graph.add_edge("evaluate_current", "decide_rotation")
    graph.add_edge("decide_rotation", "update_file")
    graph.add_edge("update_file", END)
    
    return graph.compile()

# Create sub-graph instance (reused across calls)
_emotions_subgraph = create_emotions_subgraph()

# Tool function that Deep Agent sees (interface unchanged!)
def emotions_manager_agent(story_content: str) -> str:
    """
    Tool that invokes a sub-graph internally.
    Deep Agent doesn't know or care - it just calls this function.
    """
    from tools import read_text_file
    
    current_emotions = read_text_file("emotions.txt").strip().split('\n')
    
    # Invoke the sub-graph
    result = _emotions_subgraph.invoke({
        "story_content": story_content,
        "current_emotions": current_emotions,
        "story_emotions": [],
        "decisions": {},
        "final_emotions": [],
        "status": ""
    })
    
    return result["status"]

# agent.py - NO CHANGES NEEDED!
create_deep_agent(
    tools=[emotions_manager_agent, ...]  # Same interface!
)
```

**Architecture:**
```
Deep Agent (LangGraph wrapper)
├─ Agent Node: "What should I do next?"
├─ Tools Node:
│  └─ emotions_manager_agent() ← Tool wrapper
│     └─ Invokes Sub-Graph (LangGraph)
│        ├─ analyze_story (LLM call 1)
│        ├─ evaluate_current (LLM call 2)
│        ├─ decide_rotation (LLM call 3)
│        └─ update_file (file operation)
└─ Loop: Agent → Tools → Agent → ...
```

**Pros:**
- ✅ **No changes to agent.py!** Still works with `create_deep_agent`
- ✅ Multi-step reasoning (4 focused steps vs 1 big prompt)
- ✅ Each node specialized for one task
- ✅ Conditional logic possible (if at 5, remove; if at 4, maybe add)
- ✅ Better LangSmith traces (see each internal step)
- ✅ State management tracks decisions
- ✅ Can add human-in-the-loop at any node

**Cons:**
- ❌ More complex (~300 lines vs ~70 lines per manager)
- ❌ More moving parts to maintain
- ❌ Might be overkill for simple tasks

**LangSmith Trace:**
```
Main Agent Run
├─ Agent Node: "I'll call emotions_manager_agent"
├─ Tool: emotions_manager_agent
│  └─ Sub-Graph: emotions_manager_subgraph
│     ├─ analyze_story
│     │  └─ LLM: "Story explores: melancholy, hope, wonder"
│     ├─ evaluate_current
│     │  └─ LLM: "Current: wonder(keep), intensity(keep), awe(remove)"
│     ├─ decide_rotation
│     │  └─ LLM: "Add 'bittersweet hope', remove 'awe'"
│     └─ update_file
│        └─ Write: emotions.txt
└─ Agent Node: "Done!"
```

**🌟 Key Benefit:** You can see **WHY** decisions were made!

---

### **Approach 3: Native Sub-Graph Nodes (Most Advanced)**

**What it looks like:**

Instead of using `create_deep_agent`, manually build the graph:

```python
from langgraph.graph import StateGraph, END

def build_custom_agent():
    # Don't use create_deep_agent wrapper
    # Build everything manually
    
    main_graph = StateGraph(MainState)
    
    # Orchestrator LLM node
    main_graph.add_node("orchestrator", orchestrator_llm_node)
    
    # Sub-graphs as first-class nodes (not tools)
    emotions_subgraph = create_emotions_subgraph()
    topics_subgraph = create_topics_subgraph()
    
    main_graph.add_node("emotions_manager", emotions_subgraph)
    main_graph.add_node("topics_manager", topics_subgraph)
    
    # Conditional routing
    main_graph.add_conditional_edges(
        "orchestrator",
        route_decision,
        {
            "update_emotions": "emotions_manager",
            "update_topics": "topics_manager",
            "continue": "orchestrator",
            "end": END
        }
    )
    
    main_graph.add_edge("emotions_manager", "orchestrator")
    main_graph.add_edge("topics_manager", "orchestrator")
    
    return main_graph.compile()
```

**Architecture:**
```
Custom LangGraph (no Deep Agent wrapper)
├─ Orchestrator Node (LLM)
├─ Emotions Manager Sub-Graph (first-class node)
│  ├─ analyze
│  ├─ decide
│  └─ update
├─ Topics Manager Sub-Graph (first-class node)
│  ├─ extract
│  ├─ score
│  └─ update
└─ Conditional routing between nodes
```

**Pros:**
- ✅ Full control over graph structure
- ✅ Sub-graphs as first-class citizens
- ✅ Can add complex routing logic
- ✅ No abstraction layers

**Cons:**
- ❌ Most complex to implement
- ❌ Lose Deep Agent conveniences (planning, StateBackend, etc.)
- ❌ More boilerplate code
- ❌ Have to manage agent loop yourself

**When to use:**
- You've outgrown Deep Agent abstraction
- Need custom graph topology
- Want sub-graphs as peers, not sub-tools

---

## 📊 Comparison Table

| Feature | Simple Tools | Sub-Graph Tools | Native Sub-Graphs |
|---------|-------------|----------------|-------------------|
| **Complexity** | Low (70 lines) | Medium (300 lines) | High (500+ lines) |
| **Integration** | `create_deep_agent` ✅ | `create_deep_agent` ✅ | Manual graph ❌ |
| **Multi-step reasoning** | No ❌ | Yes ✅ | Yes ✅ |
| **Conditional logic** | No ❌ | Yes ✅ | Yes ✅ |
| **LangSmith visibility** | Basic | Excellent ✅ | Excellent ✅ |
| **Maintainability** | Easy ✅ | Medium | Hard |
| **Deep Agent features** | Yes ✅ | Yes ✅ | No ❌ |
| **Iteration speed** | Fast ✅ | Medium | Slow |

---

## 🎯 Our Project's Approach

### **Phase 2 (Current):**

**Approach 1: Simple Tool Functions**

```python
# Each manager is a simple function
def emotions_manager_agent(story: str) -> str:
    llm.invoke(...)  # Single LLM call
    return "✅ Updated"

create_deep_agent(tools=[emotions_manager_agent, ...])
```

**Why we chose this:**
- Perfect for current needs
- Easy to implement and test
- Fast iteration
- No limitations encountered yet

---

### **Phase 2.5 (Optional Future):**

**Approach 2: Sub-Graph Tools**

Upgrade managers to sub-graphs while keeping the same interface:

```python
# Each manager now invokes a sub-graph
_emotions_subgraph = create_emotions_subgraph()

def emotions_manager_agent(story: str) -> str:
    return _emotions_subgraph.invoke(...)  # Multi-step workflow

# agent.py stays the same!
create_deep_agent(tools=[emotions_manager_agent, ...])
```

**When to upgrade:**
- Topic selection needs smarter logic
- Want to see decision reasoning in traces
- Need conditional paths (e.g., "if at limit, be aggressive")
- Ready for production robustness

**Migration is easy:**
- Only change sub_agents/*.py files
- agent.py doesn't change
- Same tool interface
- Can do one manager at a time

---

## 🔍 Real Example: Topics Manager Evolution

### **Current (Simple Tool):**

```python
def topics_manager_agent(research: str, topic: str) -> str:
    llm = ChatOpenAI(temperature=0.4)
    prompt = """You are a topics curator.
    Current topics: {current}
    Research: {research}
    Update topics list (5-6 items)."""
    
    response = llm.invoke([SystemMessage(prompt), HumanMessage(input)])
    # Parse and write
    return "✅ Updated topics.txt"
```

**One LLM call does everything** - extraction, evaluation, decision-making.

---

### **Future (Sub-Graph Tool):**

```python
# Step-by-step reasoning
_topics_subgraph = StateGraph(TopicsState)
_topics_subgraph.add_node("extract_candidates", extract_from_research)
_topics_subgraph.add_node("score_existing", score_topics_by_interest)
_topics_subgraph.add_node("decide_rotation", make_rotation_decision)
_topics_subgraph.add_node("update_file", write_to_file)
# Connect nodes...
_topics_subgraph = _topics_subgraph.compile()

def topics_manager_agent(research: str, topic: str) -> str:
    """Same interface, but invokes multi-step sub-graph"""
    return _topics_subgraph.invoke({
        "research": research,
        "topic_used": topic,
        ...
    })["status"]
```

**Four focused LLM calls**, each specialized:
1. Extract: "What new topics are in this research?"
2. Score: "Rate each topic 1-10 for continued interest"
3. Decide: "Based on scores, what to keep/remove?"
4. Update: Write the final list

**Result:** Better decisions, visible reasoning, conditional logic.

---

## 🚀 Key Takeaways

### **1. Deep Agent IS LangGraph**
- Not a separate system
- Convenience wrapper around LangGraph
- Gives you orchestration for free

### **2. Tools Can Be As Complex As Needed**
- Simple function: One LLM call
- Sub-graph tool: Multi-step workflow
- Deep Agent doesn't care - same interface

### **3. Incremental Upgrade Path**
```
Phase 2: Simple tools ← You are here
   ↓
Phase 2.5: Sub-graph for topics_manager (test it)
   ↓
Phase 3: Sub-graphs for all managers (if valuable)
   ↓
Future: Native sub-graphs (if you outgrow Deep Agent)
```

### **4. Interface Stability**
The beautiful part: **agent.py never changes!**

```python
# This line works for all three approaches:
create_deep_agent(tools=[emotions_manager_agent, ...])

# Whether emotions_manager_agent is:
# - Simple function (current)
# - Sub-graph wrapper (future)
# - Complex workflow (advanced)
```

---

## 📈 Decision Matrix

Use this to decide when to upgrade:

### **Stay with Simple Tools If:**
- [ ] Current approach works well
- [ ] No decision quality issues
- [ ] Files evolve appropriately
- [ ] Prefer simplicity
- [ ] Rapid iteration mode

### **Upgrade to Sub-Graph Tools If:**
- [ ] Need multi-step reasoning
- [ ] Want to see WHY decisions were made
- [ ] Need conditional logic
- [ ] Want human approval checkpoints
- [ ] Ready for production robustness
- [ ] Hit limitations of single LLM call

### **Go Native Sub-Graphs If:**
- [ ] Outgrown Deep Agent abstraction
- [ ] Need custom graph topology
- [ ] Want parallel sub-graph execution
- [ ] Building a framework (not an app)

---

## 📚 Resources

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Deep Agents Guide**: https://docs.langchain.com/oss/python/deepagents/
- **Sub-Graphs Tutorial**: https://docs.langchain.com/oss/python/langgraph/use-subgraphs
- **Our Future Upgrade Doc**: See `FUTURE_SUBGRAPH_UPGRADE.md`

---

## 🎓 Summary

**Current Architecture:**
```
create_deep_agent (LangGraph wrapper)
└─ tools: [simple function managers]
```

**Future Option (Same interface!):**
```
create_deep_agent (LangGraph wrapper)
└─ tools: [managers that invoke sub-graphs]
   └─ Each manager: multi-step LangGraph workflow
```

**The Magic:** Deep Agent + LangGraph work together seamlessly. You get simple orchestration at the top level with sophisticated workflows at the tool level.

---

**Date:** 2026-01-12  
**Current:** Simple tool functions (Approach 1)  
**Future:** Sub-graph tools if needed (Approach 2)  
**Ultimate:** Native sub-graphs only if outgrow Deep Agent (Approach 3)
