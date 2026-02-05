# Creative Story Writer Agent 📚✨

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Deep Agents](https://img.shields.io/badge/DeepAgents-0.0.8-green.svg)](https://docs.langchain.com/oss/python/deepagents/quickstart)

> An autonomous AI agent that researches current topics, writes creative short stories, and **continuously evolves** its personality, emotions, topics, and memories.

---

## ✨ Features

- 🤖 **Fully Autonomous** - Just run it, no prompts needed
- 🔍 **Adaptive Research** - Intelligent web search with 2-4+ queries based on topic complexity
- ✍️ **Creative Writing** - 500-token stories with evolving personality
- 🌱 **Self-Evolving Identity** - Updates personality (10-12 traits), emotions (4-5), topics (5-6)
- 🧠 **Human-Like Memory** - Stores, retrieves, and consolidates experiences with natural imperfection
- 📊 **Full Observability** - LangSmith integration for complete tracing
- 🏗️ **Hybrid Architecture** - Nested agents + Sub-graphs + Simple tools

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Copy `.env.example` to `.env` and add your API keys:

```env
# Required
OPENAI_API_KEY=sk-...          # Get from: platform.openai.com/api-keys
TAVILY_API_KEY=tvly-...        # Get from: tavily.com

# Optional - LangSmith Observability (Recommended)
LANGCHAIN_API_KEY=lsv2_pt_...  # Get from: smith.langchain.com
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=story-writer-agent

# Optional (defaults shown)
OPENAI_MODEL=gpt-4o-mini
```

### 3. Run the Agent

```bash
python main.py
```

That's it! The agent will:
1. Research a topic
2. Write a story
3. Save it to `stories/`
4. Evolve its identity
5. Store the experience in memory

> **💡 Tip**: Run it multiple times and watch your agent evolve!

---

## 🎯 What It Does

### The Creative Loop

Every time you run the agent:

```
1. RETRIEVE IDENTITY
   ├─ Emotions (4-5)
   ├─ Topics (5-6)
   ├─ Personality (10-12 traits)
   └─ Memories (15-20 experiences)

2. SELECT TOPIC
   └─ Choose ONE topic to explore

3. RESEARCH
   └─ Adaptive web search (2-4+ queries based on complexity)

4. WRITE STORY
   └─ 500-token creative narrative

5. STORE MEMORY
   └─ Remember key learnings

6. EVOLVE IDENTITY
   ├─ Refine emotions (rotate while protecting core)
   ├─ Update topics (based on research insights)
   └─ Evolve personality (refine existing traits)

7. CONSOLIDATE (every 3-4 stories)
   └─ Merge and simplify memories
```

---

## 🏗️ Architecture

The agent uses a **hybrid architecture** optimized for different tasks:

```
Main Orchestrator (Deep Agent)
│
├─ Nested Deep Agents (Adaptive Reasoning)
│  ├─ Research - Adapts strategy to topic complexity
│  └─ Memory - Intelligent clustering/merging
│
├─ Sub-Graphs (Observable Workflows)
│  ├─ Emotions Manager - load → extract → score → decide → apply
│  ├─ Topics Manager - load → extract → score → decide → apply
│  └─ Personality Manager - load → extract → evaluate → decide → apply
│
└─ Simple Tools
   └─ Writer - Creative story generation
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for details.

---

## 📁 Project Structure

```
ShortStoryTelledDeepAgent/
├─ 📖 Documentation
│  ├─ README.md (this file)
│  ├─ ARCHITECTURE.md
│  └─ DEEP_AGENT_LANGGRAPH_ARCHITECTURE.md
│
├─ 🐍 Core Code
│  ├─ main.py
│  ├─ agent.py
│  ├─ prompts.py
│  ├─ tools.py
│  └─ config.py
│
├─ 🤖 Sub-Agents
│  └─ sub_agents/
│     ├─ research_deep_agent.py
│     ├─ memory_deep_agent.py
│     ├─ emotions_subgraph.py
│     ├─ topics_subgraph.py
│     ├─ personality_subgraph.py
│     └─ writer_agent.py
│
├─ 📝 Identity Files (Self-Evolving)
│  ├─ emotions.txt
│  ├─ topics.txt
│  ├─ personality.txt
│  └─ memories.txt
│
├─ 📚 Generated Stories
│  └─ stories/
│
└─ ⚙️ Configuration
   ├─ requirements.txt
   ├─ .env.example
   └─ .env
```

---

## 🧠 Self-Evolution

### Identity Files

The agent maintains four evolving identity files:

**`topics.txt`** (5-6 topics)
- Rotates based on research insights
- Scores existing topics for relevance
- Adds fascinating new discoveries

**`emotions.txt`** (4-5 emotions)
- Protects core emotions: "Wonder and curiosity", "Melancholy hope", "Quiet intensity"
- Rotates remaining slots based on story content
- Maintains diverse emotional palette

**`personality.txt`** (10-12 traits)
- Refines existing traits for clarity
- Adds new traits if consistent patterns emerge
- Removes traits that no longer fit

**`memories.txt`** (15-20 experiences)
- Stores significant learnings from each story
- Retrieves relevant memories for context
- Consolidates periodically (merges similar, simplifies complex, allows natural distortion)

### Evolution Philosophy

The agent **evolves, not grows**:
- Files maintain fixed sizes
- Content rotates based on relevance
- Old insights replaced by new ones
- Natural imperfection (especially in memories)

---

## 📊 LangSmith Observability

Enable LangSmith for full tracing:

```env
LANGCHAIN_API_KEY=lsv2_pt_...
LANGSMITH_TRACING=true
```

**You'll see:**
- Every nested agent reasoning step
- All 6 nodes in each sub-graph workflow
- Decision logs for identity evolution
- Memory clustering and consolidation
- Complete token usage and costs

---

## 📖 Example Story

**`stories/2026-01-13_14-13-29_AI_caregiving_and_human_emotional_connection.txt`**

```
Elara sat cross-legged on the worn carpet, the soft hum of Solace's 
processor filling the quiet room like a whispered pulse. The AI 
companion's avatar flickered on her tablet screen—a subtle, shifting 
blend of light and shadow, neither fully human nor machine...

[500-token narrative exploring AI-human connection with wonder, 
melancholy hope, and quiet intensity]
```

Each story:
- ✅ ~500 tokens
- ✅ Incorporates personality traits
- ✅ Channels 2-3 emotions
- ✅ Weaves in research insights
- ✅ Influenced by memories
- ✅ Clear narrative arc

---

## ⚙️ Customization

### Seed Initial Identity

Edit identity files before first run:

**`topics.txt`**
```
AI consciousness and ethics
Human-AI emotional connection
Quantum computing frontiers
```

**`personality.txt`**
```
Philosophical yet accessible
Layered metaphorical thinking
Balances complexity with clarity
```

**`emotions.txt`**
```
Wonder and curiosity
Melancholy hope
Quiet intensity
```

The agent will evolve these over time!

---

## 💰 Cost & Performance

### Per Story Cycle (~20-28 LLM calls):

- Research: 5-10 calls (~$0.005-0.01)
- Memory: 4-7 calls (~$0.004-0.007)
- Managers: 9 calls (~$0.009)
- Writer: 1 call (~$0.001)

**Total: ~$0.02-0.028 per story**

Memory consolidation (every 3-4 stories): +$0.005-0.008

---

## 🛠️ Built With

- **Deep Agents** - LangChain's agentic framework
- **LangGraph** - Sub-graph workflows
- **OpenAI GPT-4o-mini** - Language model
- **Tavily** - AI-optimized web search
- **LangSmith** - Observability platform

---

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[DEEP_AGENT_LANGGRAPH_ARCHITECTURE.md](DEEP_AGENT_LANGGRAPH_ARCHITECTURE.md)** - Technical deep dive
- **[FUTURE_SUBGRAPH_UPGRADE.md](FUTURE_SUBGRAPH_UPGRADE.md)** - Potential enhancements

---

## 📝 License

MIT License - Feel free to use and modify!

---

## 🙏 Built With

- 🦜 [LangChain Deep Agents](https://docs.langchain.com/oss/python/deepagents/quickstart)
- 🤖 [OpenAI](https://openai.com)
- 🔍 [Tavily](https://tavily.com)
- 📊 [LangSmith](https://smith.langchain.com)

---

<div align="center">

**⭐ Star this repo if you find it interesting!**

*This agent evolves autonomously. Run it regularly and watch it develop its own unique creative voice!* 🌱

</div>
