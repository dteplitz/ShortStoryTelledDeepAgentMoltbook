# Skills Architecture Update - Writer-Focused Implementation

## Summary of Changes

Successfully moved the Agent Skills system from the **main orchestrator agent** to the **writer subgraph nodes** where they're actually needed for craft guidance.

## What Changed

### 1. **Writer Subgraph (`sub_agents/writer_subgraph.py`)** ✅

**Before:** Simple LLM calls with static prompts
**After:** Tool-using agents with skill access

#### Three Nodes Now Use Skills:

**`create_outline` node:**
- Can call: `use_skill("narrative_structure")`, `use_skill("philosophical_storytelling")`
- Decides whether to load story structure guidance
- Creates outline informed by craft skills

**`draft_story` node:**
- Can call: `use_skill("philosophical_storytelling")`, `use_skill("emotional_resonance")`
- Can access: `read_skill_resource("emotional_resonance", "techniques/sensory_library.txt")`
- Writes story with optional skill-based guidance

**`refine_and_format` node:**
- Can call: `use_skill("emotional_resonance")`
- Can access: `read_skill_resource("narrative_structure", "templates/ending_techniques.txt")`
- Polishes endings using skill techniques

#### Implementation:

Each node now uses `create_react_agent`:
```python
def create_outline(state: WriterState) -> WriterState:
    from tools import use_skill, read_skill_resource
    
    outline_agent = create_react_agent(
        model=llm,
        tools=[use_skill, read_skill_resource],
        state_modifier=OUTLINE_SYSTEM_PROMPT
    )
    
    result = outline_agent.invoke({"messages": [...]})
    # Extract outline from agent's final message
```

### 2. **Main Agent (`agent.py`)** ✅

**Before:** Skills metadata loaded into system prompt
**After:** Skills removed entirely from main agent

```python
# REMOVED: Loading skills into main agent
# from skills_system import get_skills_manager
# skills_manager = get_skills_manager()
# skills_prompt_section = skills_manager.generate_system_prompt_section()

# Main agent uses basic SYSTEM_PROMPT without skills
return create_deep_agent(
    tools=all_tools,
    system_prompt=SYSTEM_PROMPT,  # No skills here
    model=llm,
    backend=make_backend,
)
```

### 3. **Tools (`tools.py`)** ✅

**Before:** Skill tools in main agent's tool list
**After:** Skill tools available for import but not in main tools

```python
# Skill tools still exist but NOT in main agent's tools list
tools = [
    internet_search,
    read_text_file,
    write_text_file,
    list_files,
    get_timestamp,
    # Removed: use_skill, read_skill_resource, execute_skill_script
]
```

Skills are imported directly by writer nodes when needed.

## Architecture Diagram

```
Main Agent (Orchestrator)
├─ Tools:
│  ├─ internet_search
│  ├─ file operations
│  └─ get_timestamp
│
└─ Sub-Agents:
   ├─ research_deep_agent
   ├─ memory_deep_agent
   ├─ emotions_manager
   ├─ topics_manager
   ├─ personality_manager
   └─ writer_subgraph ⭐ (NEW: Has Skills!)
      │
      ├─ Node 1: create_outline
      │  └─ Tools: [use_skill, read_skill_resource]
      │     ├─ narrative_structure
      │     └─ philosophical_storytelling
      │
      ├─ Node 2: draft_story
      │  └─ Tools: [use_skill, read_skill_resource]
      │     ├─ philosophical_storytelling
      │     └─ emotional_resonance
      │
      ├─ Node 3: refine_and_format
      │  └─ Tools: [use_skill, read_skill_resource]
      │     ├─ emotional_resonance
      │     └─ narrative_structure (endings)
      │
      └─ Node 4: save_story
```

## How It Works Now

### Story Creation Flow:

1. **Main Agent** orchestrates:
   - Retrieves identity (emotions, topics, personality, memories)
   - Calls research agent
   - Gets timestamp
   - **Calls writer_subgraph_tool**

2. **Writer Subgraph** (with skills):
   - **Outline Node**: May load `narrative_structure` skill
     - Decides: "Do I need story beat guidance?"
     - If yes: Calls `use_skill("narrative_structure")`
     - Creates outline informed by 500-token beat structure
   
   - **Draft Node**: May load `philosophical_storytelling` and `emotional_resonance`
     - Decides: "Do I need help dramatizing concepts or evoking emotions?"
     - If yes: Loads appropriate skills
     - Writes story using craft techniques
   
   - **Refine Node**: May load ending techniques
     - Decides: "Do I need help with emotional landing?"
     - If yes: Loads ending resources
     - Polishes ending for resonance
   
   - **Save Node**: Saves final story

3. **Main Agent** continues:
   - Stores memory
   - Evolves identity files

## Benefits of This Architecture

### ✅ **Targeted Skill Usage**
Skills are available exactly where writing happens, not in orchestration layer

### ✅ **Token Efficient**
Main agent doesn't carry skill metadata it never uses

### ✅ **Flexible**
Writer nodes decide when skills are helpful (not mandatory)

### ✅ **Observable**
LangSmith shows when each node loads skills:
```
create_outline
  ├─ use_skill("narrative_structure")
  └─ Created outline using 500-token beats

draft_story
  ├─ use_skill("emotional_resonance")
  ├─ read_skill_resource("emotional_resonance", "sensory_library.txt")
  └─ Wrote story with tender connection techniques
```

### ✅ **Progressive Disclosure**
- Skills only loaded when nodes determine they're needed
- Full resources accessed on-demand
- No token waste on unused guidance

### ✅ **Cleaner Separation**
- **Main agent**: Workflow orchestration
- **Writer nodes**: Craft execution (with craft tools)

## Cost Implications

### Token Usage Per Story:

**Before (Skills in Main Agent):**
- Main agent system prompt: ~6,800 tokens (includes 300 for skill metadata)
- Writer subgraph: ~3 simple LLM calls
- **Total**: ~6,800 + writer calls

**After (Skills in Writer Nodes):**
- Main agent system prompt: ~6,500 tokens (no skill metadata)
- Writer subgraph: ~6-12 LLM calls (if skills used)
  - Outline: 2-4 calls (agent decides + maybe loads skills)
  - Draft: 2-4 calls
  - Refine: 2-4 calls
- **Total**: ~6,500 + more writer calls

**Tradeoff:**
- ✅ Main agent: -300 tokens saved
- ❌ Writer: +3-9 extra LLM calls (if skills used)
- ✅ Quality: Craft guidance applied when needed

### When Skills Are Used:
- If nodes **don't** use skills: Same cost as before
- If nodes **do** use skills: +$0.002-0.005 per story (worth it for quality)

## Testing the New System

Run a story creation and watch LangSmith to see:

1. Main agent orchestrates (no skill calls)
2. Writer subgraph nodes:
   - **May** call `use_skill()`
   - **May** call `read_skill_resource()`
   - Create better-structured stories

Expected behavior:
- Not every story uses skills (agent decides)
- Skills more likely used for complex/philosophical topics
- LangSmith shows skill usage in writer subgraph traces

## Files Modified

- ✅ `sub_agents/writer_subgraph.py` - Added tool-using agents to 3 nodes
- ✅ `agent.py` - Removed skills from main agent
- ✅ `tools.py` - Removed skill tools from main tools list

## Files Unchanged

- ✅ `skills_system.py` - Skills manager still works
- ✅ `skills/` - All 3 skills still available
- ✅ Main agent workflow still the same

## Next Steps

### Immediate:
Test with: `python main.py` and observe in LangSmith whether skills are used

### Future Enhancements:
- **Add more skills** as needed (scifi_worldbuilding, character_voice)
- **Tune prompts** to encourage skill usage when beneficial
- **Monitor metrics** to see if skills improve story quality

---

**Updated:** 2026-01-13
**Architecture Version:** 2.0 - Skills in Writer Subgraph
**Status:** ✅ Complete and Ready to Test
