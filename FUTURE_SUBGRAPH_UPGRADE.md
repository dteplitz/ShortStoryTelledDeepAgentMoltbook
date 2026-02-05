# Future Architecture: Sub-Graph Managers

## 📋 Context

During Phase 2 implementation, we made an architectural decision about how to implement file manager agents. This document explains that decision and outlines a future upgrade path.

> **📖 Related Reading:** See `DEEP_AGENT_LANGGRAPH_ARCHITECTURE.md` for a comprehensive explanation of how Deep Agent works with LangGraph and sub-graphs.

---

## 🎯 Current Architecture (Phase 2)

### What We Built

**Simple Tool Functions** that wrap single LLM calls:

```python
def emotions_manager_agent(story_content: str) -> str:
    """Simple function acting as a tool"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
    messages = [SystemMessage(...), HumanMessage(...)]
    response = llm.invoke(messages)
    # Parse response, enforce limits, write file
    return "✅ Updated emotions.txt"
```

### Architecture Flow

```
Main Deep Agent (Orchestrator)
└─ Calls manager as tool
   └─ Manager function
      ├─ Single LLM call
      ├─ Parse response
      ├─ Enforce size limit
      └─ Write file
```

### Pros ✅

1. **Simplicity** - Easy to understand and maintain
2. **Fast to implement** - 50-70 lines per manager
3. **Works with Deep Agent** - Integrates naturally as tools
4. **Sufficient for current needs** - Single LLM call handles the task
5. **Easy to test** - Simple input/output
6. **Quick iteration** - Can modify prompts easily

### Cons ❌

1. **Limited reasoning** - Single LLM call, no multi-step logic
2. **No conditional paths** - Can't branch based on state
3. **Basic observability** - LangSmith shows one tool call
4. **No intermediate steps** - Decision process is opaque
5. **Hard to add complexity** - Would need to cram into one prompt

---

## 🚀 Future Architecture: LangGraph Sub-Graphs

### What It Would Look Like

**Sub-Graph Workflows** with multiple reasoning steps:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class TopicsManagerState(TypedDict):
    research_content: str
    topic_used: str
    current_topics: list[str]
    candidate_topics: list[str]
    interest_scores: dict[str, float]
    topics_to_add: list[str]
    topics_to_remove: list[str]
    final_topics: list[str]

# Step 1: Analyze research
def extract_candidate_topics(state: TopicsManagerState):
    """LLM extracts 2-3 potential topics from research"""
    llm = ChatOpenAI(temperature=0.3)
    # ... specialized prompt for extraction
    return state

# Step 2: Score current topics
def score_existing_topics(state: TopicsManagerState):
    """LLM scores each current topic's continued relevance"""
    llm = ChatOpenAI(temperature=0.2)
    # ... score each topic 1-10
    return state

# Step 3: Make decisions
def decide_rotation(state: TopicsManagerState):
    """Logic to decide what to add/remove"""
    current_count = len(state["current_topics"])
    candidates = state["candidate_topics"]
    
    if current_count + len(candidates) > 6:
        # Call LLM to decide which current topics to remove
        # Based on interest scores and relevance
        pass
    
    return state

# Step 4: Update file
def write_updated_topics(state: TopicsManagerState):
    """Write final topics to file"""
    from tools import write_text_file
    write_text_file("topics.txt", ...)
    return state

# Build graph
graph = StateGraph(TopicsManagerState)
graph.add_node("extract_candidates", extract_candidate_topics)
graph.add_node("score_existing", score_existing_topics)
graph.add_node("decide_rotation", decide_rotation)
graph.add_node("write_file", write_updated_topics)

# Connect with edges
graph.set_entry_point("extract_candidates")
graph.add_edge("extract_candidates", "score_existing")
graph.add_edge("score_existing", "decide_rotation")
graph.add_edge("decide_rotation", "write_file")
graph.add_edge("write_file", END)

# Compile
topics_manager_subgraph = graph.compile()
```

### Architecture Flow

```
Main Deep Agent (Orchestrator)
└─ Invokes sub-graph
   └─ Topics Manager Sub-Graph
      ├─ Node: Extract candidates (LLM call 1)
      ├─ Node: Score existing (LLM call 2)
      ├─ Node: Decide rotation (LLM call 3)
      └─ Node: Write file (file operation)
```

### Pros ✅

1. **Multi-step reasoning** - Each step specialized for one task
2. **Conditional logic** - Branch based on state (e.g., if at limit, be aggressive)
3. **Better observability** - LangSmith shows full decision process
4. **Composable** - Each node can be reused or tested independently
5. **Aligned with LangGraph 1.0** - Uses framework as intended
6. **Human-in-the-loop ready** - Can add approval checkpoints
7. **State management** - Track decisions through workflow
8. **More sophisticated** - Can implement complex curation logic

### Cons ❌

1. **More complex** - 200-300 lines per manager vs 70 lines
2. **Harder to maintain** - More moving parts
3. **Slower to iterate** - More code to change
4. **Might be overkill** - If simple approach works fine
5. **Learning curve** - Requires deeper LangGraph knowledge

---

## 📊 Comparison: Use Cases

### When Current Approach (Tool Functions) Is Better

✅ **Simple, deterministic updates**
- "Update emotions based on story"
- Single pass analysis is sufficient
- No branching logic needed

✅ **Rapid prototyping**
- Testing ideas quickly
- Iterating on prompts
- Early stage development

✅ **Clear, straightforward tasks**
- Input → LLM → Output → Write file
- No intermediate decisions
- Linear process

### When Sub-Graphs Would Be Better

✅ **Complex decision-making**
- "Should I remove topic A or B?" requires comparing both
- Multiple evaluation criteria
- Conditional logic based on state

✅ **Multi-step reasoning**
- Extract insights → Evaluate options → Score candidates → Make final decision
- Each step needs different temperature/model
- Need to see intermediate results

✅ **Conditional workflows**
- If file has 6 items: be aggressive with removals
- If file has 4 items: be more lenient with additions
- Different paths based on state

✅ **Human oversight**
- Show candidates before updating
- Approval checkpoint: "Remove these 2 topics?"
- Interrupt before final write

✅ **Production robustness**
- Retry logic on individual steps
- Validation between steps
- Error recovery

---

## 🎯 Upgrade Path (When to Consider)

### Phase 2.5: Hybrid Approach

Start with **one** sub-graph to experiment:

**Topics Manager → Sub-Graph** (best candidate because topic selection is complex)
- Keep emotions_manager as simple tool
- Keep personality_manager as simple tool
- Convert topics_manager to sub-graph
- Compare in real usage

**Benefits:**
- Learn sub-graph patterns
- See if complexity is worth it
- Can revert if not beneficial

### Phase 3: Full Sub-Graph Migration

If the hybrid approach proves valuable:

1. **Topics Manager** → Sub-graph ✅ (already done)
2. **Emotions Manager** → Sub-graph (if rotation logic gets complex)
3. **Personality Manager** → Sub-graph (if refinement needs more steps)

---

## 🔍 Example: Topics Manager Sub-Graph Detail

### Current (Simple Tool)

```python
def topics_manager_agent(research: str, topic: str) -> str:
    # One prompt does everything:
    # "Here's research, here's current topics, update the list"
    llm.invoke([SystemMessage(PROMPT), HumanMessage(input)])
```

**LangSmith Trace:**
```
topics_manager_agent
└─ LLM Call
   └─ Input: research + current topics
   └─ Output: new topics list
```

### Future (Sub-Graph)

```python
topics_manager_subgraph.invoke({
    "research_content": research,
    "topic_used": topic,
    "current_topics": read_current_topics()
})
```

**LangSmith Trace:**
```
topics_manager_subgraph
├─ extract_candidates
│  └─ LLM: "Found: 'Quantum entanglement', 'AI interpretability'"
├─ score_existing  
│  └─ LLM: "AI consciousness: 8/10, Quantum Physics: 6/10, ..."
├─ decide_rotation
│  └─ LLM: "Add 'AI interpretability', Remove 'Friendship' (lowest score)"
└─ write_file
   └─ File: topics.txt updated
```

**Value:** You can see **WHY** "Friendship" was removed (low score) and **WHY** "AI interpretability" was added (from research, relevant).

---

## 📈 Migration Strategy

### Step 1: Prepare (No code changes)

- [ ] Test current Phase 2 thoroughly
- [ ] Identify pain points (if any)
- [ ] Decide if upgrade is needed
- [ ] Read LangGraph sub-graph docs

### Step 2: Pilot (One sub-graph)

- [ ] Choose topics_manager as pilot
- [ ] Implement sub-graph version
- [ ] Keep old version as backup
- [ ] A/B test both approaches
- [ ] Measure: Does sub-graph provide better results?

### Step 3: Evaluate Pilot

**If successful:**
- Sub-graph decisions are noticeably better
- LangSmith traces reveal valuable insights
- Complexity is manageable
→ Proceed to Step 4

**If not valuable:**
- Simple approach works fine
- Added complexity not worth it
- Revert to tool functions
→ Stay with current approach

### Step 4: Expand (If pilot successful)

- [ ] Convert emotions_manager
- [ ] Convert personality_manager
- [ ] Update documentation
- [ ] Remove old tool functions

---

## 💡 Decision Criteria Checklist

Use this checklist when considering the upgrade:

### Stay with Current Approach If:

- [ ] Current managers work well
- [ ] No complaints about file evolution quality
- [ ] Size limits are respected
- [ ] You prefer simplicity
- [ ] Single LLM call is sufficient
- [ ] You're still iterating rapidly

### Upgrade to Sub-Graphs If:

- [ ] Topics don't evolve intelligently
- [ ] Need to see WHY decisions were made
- [ ] Want conditional logic (e.g., "if at limit, be aggressive")
- [ ] Want human approval before changes
- [ ] Ready for production-grade robustness
- [ ] Want to learn LangGraph 1.0 patterns
- [ ] Multi-step reasoning would help

---

## 🎓 Learning Resources

If you decide to upgrade:

1. **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
2. **Sub-Graphs Tutorial**: Search "LangGraph sub-graphs" in docs
3. **Example**: Multi-agent systems with sub-graphs
4. **LangSmith**: Study traces of sub-graph executions

---

## 📝 Summary

### Current Decision (Phase 2)

**We chose simple tool functions because:**
- ✅ Sufficient for current needs
- ✅ Easy to implement and test
- ✅ Fast iteration
- ✅ Works well with Deep Agent
- ✅ No complexity limitations encountered yet

### Future Opportunity

**Sub-graphs become valuable when:**
- Need multi-step reasoning
- Want better observability
- Require conditional logic
- Ready for production robustness
- Want to leverage LangGraph 1.0 fully

### Recommendation

1. **Now**: Use and test Phase 2 as-is
2. **Later**: If you hit limitations, try sub-graph for topics_manager
3. **Future**: Migrate all managers if sub-graphs prove valuable

**This is not technical debt** - it's the right choice for current stage. We can always upgrade when needed.

---

## 🔮 Future Vision: Full Sub-Graph Architecture

```
Main Deep Agent (Orchestrator)
├─ Tool: internet_search
├─ Tool: read_text_file  
├─ Tool: write_text_file (for stories)
│
├─ Sub-Graph: emotions_manager_subgraph
│  ├─ analyze_story
│  ├─ evaluate_emotions
│  ├─ decide_rotation
│  └─ update_file
│
├─ Sub-Graph: topics_manager_subgraph
│  ├─ extract_candidates
│  ├─ score_existing
│  ├─ decide_changes
│  └─ update_file
│
└─ Sub-Graph: personality_manager_subgraph
   ├─ analyze_style
   ├─ evaluate_traits
   ├─ refine_traits
   └─ update_file
```

**This is the ultimate architecture** - but only if complexity is justified by results.

---

**Date:** 2026-01-12  
**Decision:** Use simple tool functions for Phase 2  
**Review Date:** After 20+ story generations  
**Upgrade Trigger:** Pain points or desire for better observability
