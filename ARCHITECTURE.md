# 🏗️ Story Writer Agent - Architecture

## Overview

The Story Writer Agent is a **self-evolving creative AI system** that writes short stories while continuously refining its voice, topics, emotions, and memories. It uses a **hybrid architecture** combining three approaches for optimal performance.

---

## 🎯 Core Concept

The agent:
1. **Researches** topics using adaptive search strategies
2. **Writes** 500-token creative stories
3. **Evolves** its personality, emotions, and topics based on what it writes
4. **Remembers** significant experiences with human-like imperfection

---

## 🏗️ Architecture

```
Main Deep Agent (Orchestrator)
│
├─ Basic Tools:
│  ├─ internet_search() - Web research
│  ├─ read_text_file() - File reading
│  ├─ write_text_file() - File writing
│  ├─ list_files() - Directory listing
│  └─ get_timestamp() - Current time
│
├─ Nested Deep Agents (Adaptive Reasoning): 🤖
│  ├─ research_deep_agent()
│  │  └─ Adapts search strategy to topic complexity
│  │  └─ 2-4+ searches based on need
│  │  └─ Self-corrects if results insufficient
│  │
│  └─ memory_deep_agent()
│     └─ Intelligent memory clustering
│     └─ Nuanced merge/keep/forget decisions
│     └─ Human-like imperfection
│
├─ Sub-Graphs (Deterministic Workflows): 🔧
│  ├─ emotions_manager_subgraph()
│  │  └─ load → extract → score → decide → apply
│  │  └─ Maintains 4-5 emotions
│  │  └─ Protects core emotions
│  │
│  ├─ topics_manager_subgraph()
│  │  └─ load → extract → score → decide → apply
│  │  └─ Maintains 5-6 topics
│  │  └─ Rotates based on relevance
│  │
│  └─ personality_manager_subgraph()
│     └─ load → extract → evaluate → decide → apply
│     └─ Maintains 10-12 traits
│     └─ Refines existing traits for clarity
│
└─ Simple Tools (Direct Execution): ⚡
   └─ writer_agent()
      └─ Single creative LLM call
      └─ Generates and saves story
```

---

## 📊 Architectural Patterns

### 1. **Nested Deep Agents** 🤖

**When to Use:** Adaptive, open-ended problems requiring reasoning

**Examples:** Research, Memory Management

**How It Works:**
```python
nested_agent = create_deep_agent(
    tools=[internet_search],
    system_prompt="You are a research specialist...",
    model=llm
)
result = nested_agent.invoke({"messages": [...]})
```

**Characteristics:**
- ✅ Adapts strategy dynamically
- ✅ Self-correcting
- ✅ Can iterate and refine
- ⚠️ Higher cost (5-10 LLM calls)
- ⚠️ Less predictable

---

### 2. **Sub-Graphs** 🔧

**When to Use:** Structured, multi-step workflows needing observability

**Examples:** Emotions, Topics, Personality managers

**How It Works:**
```python
graph = StateGraph(ManagerState)
graph.add_node("load", load_function)
graph.add_node("extract", extract_function)
graph.add_node("score", score_function)
graph.add_node("decide", decide_function)
graph.add_node("apply", apply_function)
# ... set edges ...
compiled_graph = graph.compile()
```

**Characteristics:**
- ✅ Deterministic and predictable
- ✅ Full observability (6 nodes in LangSmith)
- ✅ Explicit state flow
- ✅ Easy to debug
- ⚠️ Medium cost (3 LLM calls)
- ⚠️ More code to maintain

---

### 3. **Simple Tools** ⚡

**When to Use:** Single-step, straightforward tasks

**Examples:** Writer agent

**How It Works:**
```python
def writer_agent(topic, research, personality, emotions, memories, timestamp):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    response = llm.invoke(messages)
    return response.content
```

**Characteristics:**
- ✅ Fast (1 LLM call)
- ✅ Low cost
- ✅ Simple to maintain
- ❌ Black box (no intermediate steps)
- ❌ Not self-correcting

---

## 🔄 Story Creation Workflow

```
1. RETRIEVE IDENTITY
   ├─ emotions_manager_subgraph(operation="retrieve")
   ├─ topics_manager_subgraph(operation="retrieve")
   ├─ personality_manager_subgraph(operation="retrieve")
   └─ memory_deep_agent(operation="retrieve", query=...)

2. SELECT TOPIC
   └─ Choose ONE topic from available topics

3. RESEARCH
   └─ research_deep_agent(topic)
      ├─ Analyzes topic complexity
      ├─ Generates 2-4 search queries
      ├─ Executes searches
      ├─ Evaluates results
      └─ Synthesizes findings

4. GET TIMESTAMP
   └─ get_timestamp()

5. WRITE STORY
   └─ writer_agent(
        topic, research, personality,
        emotions, memories, timestamp
      )
      ├─ Generates 500-token story
      └─ Saves to stories/{timestamp}_{topic}.txt

6. STORE MEMORY
   └─ memory_deep_agent(
        operation="store",
        experience="key learning from story"
      )

7. EVOLVE IDENTITY
   ├─ emotions_manager_subgraph(
   │    operation="evolve",
   │    story_content=story
   │  )
   ├─ topics_manager_subgraph(
   │    operation="evolve",
   │    research_content=research,
   │    topic_used=topic
   │  )
   └─ personality_manager_subgraph(
        operation="refine",
        story_content=story,
        topic=topic
      )

8. CONSOLIDATE MEMORIES (periodic)
   └─ memory_deep_agent(operation="consolidate")
      ├─ Every 3-4 stories
      └─ Or when memory count > 15
```

---

## 📁 File Structure

```
ShortStoryTelledDeepAgent/
├─ 📖 Documentation
│  ├─ README.md - Main guide
│  ├─ ARCHITECTURE.md (this file)
│  ├─ DEEP_AGENT_LANGGRAPH_ARCHITECTURE.md - Technical deep dive
│  └─ FUTURE_SUBGRAPH_UPGRADE.md - Enhancement ideas
│
├─ 🐍 Core Code
│  ├─ main.py - Entry point
│  ├─ agent.py - Agent builder
│  ├─ prompts.py - System prompts
│  ├─ tools.py - Basic tools
│  └─ config.py - Configuration
│
├─ 🤖 Sub-Agents
│  └─ sub_agents/
│     ├─ __init__.py
│     ├─ research_deep_agent.py (Nested agent)
│     ├─ memory_deep_agent.py (Nested agent)
│     ├─ emotions_subgraph.py (Sub-graph)
│     ├─ topics_subgraph.py (Sub-graph)
│     ├─ personality_subgraph.py (Sub-graph)
│     └─ writer_agent.py (Simple tool)
│
├─ 📝 Identity Files (Self-Evolving)
│  ├─ emotions.txt (4-5 emotions)
│  ├─ topics.txt (5-6 topics)
│  ├─ personality.txt (10-12 traits)
│  └─ memories.txt (15-20 memories)
│
├─ 📚 Generated Content
│  └─ stories/ - All generated stories
│
└─ ⚙️ Configuration
   ├─ requirements.txt
   ├─ .env.example
   └─ .env (your API keys)
```

---

## 💰 Cost & Performance

### Per Story Cycle:

| Component | LLM Calls | Cost (approx) |
|-----------|-----------|---------------|
| Research (Nested Agent) | 5-10 | $0.005-0.01 |
| Memory Retrieve | 1-2 | $0.001-0.002 |
| Memory Store | 3-5 | $0.003-0.005 |
| Emotions Evolution | 3 | $0.003 |
| Topics Evolution | 3 | $0.003 |
| Personality Refinement | 3 | $0.003 |
| Writer | 1 | $0.001 |
| **Total** | **~20-28** | **$0.02-0.028** |

**Memory Consolidation** (periodic): +5-8 calls = +$0.005-0.008

---

## 🔍 Observability (LangSmith)

Every component is fully traceable:

**Nested Agents:**
- See full reasoning process
- Every tool call visible
- Adaptive decision-making transparent

**Sub-Graphs:**
- 6 distinct nodes per manager
- State flow visible at each step
- Intermediate LLM calls shown
- Decision logs captured

**Simple Tools:**
- Single LLM call visible
- Input/output clear

---

## 🎯 Design Principles

### 1. **Evolution, Not Growth**
Identity files maintain fixed sizes by rotating content, not accumulating.

### 2. **Human-Like Memory**
Memories are imperfect, can merge, simplify, and slightly distort over time.

### 3. **Separation of Concerns**
Each agent has a clear responsibility:
- Research: Information gathering
- Memory: Experience storage
- Managers: Identity curation
- Writer: Story creation

### 4. **Full Observability**
Every decision is traceable in LangSmith for debugging and improvement.

### 5. **Hybrid Architecture**
Use the right pattern for each problem:
- Adaptive reasoning → Nested agents
- Deterministic workflows → Sub-graphs
- Simple tasks → Direct tools

---

## 🚀 Key Features

### 1. **Adaptive Research**
- Adjusts strategy based on topic complexity
- Can perform 2-4+ searches as needed
- Self-corrects if initial results insufficient

### 2. **Intelligent Memory**
- Clusters related memories
- Merges similar experiences
- Allows natural imperfection
- Forgets trivial details

### 3. **Smart Evolution**
- **Emotions**: Protects core emotions, rotates others
- **Topics**: Scores relevance, rotates based on interest
- **Personality**: Refines existing traits for clarity

### 4. **Quality Writing**
- Specialized creative prompt
- Higher temperature (0.7) for creativity
- Integrates research, personality, emotions, memories
- 500-token focused narratives

---

## 🔧 Extensibility

Easy to add:

**Validation Nodes:**
```python
graph.add_node("validate", validate_decision)
graph.add_edge("decide", "validate")
graph.add_conditional_edges("validate", route_validation)
```

**Human-in-the-Loop:**
```python
graph.add_node("request_approval", approval_node)
graph.add_edge("decide", "request_approval")
```

**Parallel Execution:**
```python
# Score topics in parallel instead of sequential
graph.add_node("score_parallel", parallel_score_node)
```

---

## 📚 Further Reading

- **`README.md`** - Getting started guide
- **`DEEP_AGENT_LANGGRAPH_ARCHITECTURE.md`** - How LangGraph works
- **`FUTURE_SUBGRAPH_UPGRADE.md`** - Potential enhancements
- **LangGraph Docs** - https://langchain-ai.github.io/langgraph/

---

**Last Updated:** 2026-01-13  
**Architecture Version:** 1.0 (Production)
