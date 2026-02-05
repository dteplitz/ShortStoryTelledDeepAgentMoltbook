# Agent Skills System

## Overview

This directory contains **Agent Skills** - modular, reusable capabilities that provide your story writer with specialized expertise. Skills use **progressive disclosure** to be token-efficient while providing deep, on-demand guidance.

## Architecture

### Three-Level Progressive Disclosure

**Level 1: Metadata (~100 tokens per skill)**
- Always loaded in system prompt
- Just name and description
- Agent knows skills exist and when to use them

**Level 2: Instructions (~1-2K tokens)**
- Loaded when agent calls `use_skill(skill_name)`
- Full guidance, techniques, examples
- Only loaded when actually needed

**Level 3: Resources (unlimited)**
- Loaded when agent calls `read_skill_resource(skill_name, resource_path)`
- Templates, detailed examples, reference materials
- Accessed individually on-demand

## Available Skills

### 1. `narrative_structure`
**Purpose:** Story architecture for 500-token short fiction

**When to use:** During outline and draft phases

**Provides:**
- Story beats optimized for 500 tokens
- Opening hooks and ending techniques
- Pacing strategies for ultra-short fiction
- "Show don't tell" specific examples

**Resources:**
- `templates/500_token_beats.txt` - Detailed beat sheet with examples
- `templates/opening_hooks.txt` - 20 hook strategies
- `templates/ending_techniques.txt` - How to land the final moment

---

### 2. `philosophical_storytelling`
**Purpose:** Transform abstract ideas into dramatic narratives

**When to use:** Stories exploring AI consciousness, ethics, sentience

**Provides:**
- How to dramatize philosophical concepts
- Thought experiments as narrative devices
- Balancing ideas with emotional impact
- Avoiding "lecture" mode in fiction

**Resources:**
- `examples/consciousness_story.txt` - Full example with analysis
- `examples/philosophy_techniques.txt` - Before/after examples

---

### 3. `emotional_resonance`
**Purpose:** Evoke specific emotions through prose techniques

**When to use:** Crafting emotional moments, landing feelings

**Provides:**
- Techniques for your specific emotional palette:
  * Tender technological connection
  * Whispered digital intimacy
  * Quiet caregiving comfort
  * Melancholic digital nostalgia
  * Cautious hope
- Sensory details mapped to emotions
- Subtext and implication strategies

**Resources:**
- `techniques/sensory_library.txt` - Emotion-specific sensory details
- `techniques/endings_by_emotion.txt` - How to land each emotion

## How to Use Skills

### As the Main Agent

The agent automatically sees skill metadata in its system prompt and can use them with:

```python
# Load a skill's full instructions
use_skill(skill_name="narrative_structure")

# Read a specific resource
read_skill_resource(
    skill_name="narrative_structure",
    resource_path="templates/opening_hooks.txt"
)
```

### Integration Points in Your Workflow

**During Outline Phase:**
```python
use_skill("narrative_structure")  # Story beats
use_skill("philosophical_storytelling")  # How to dramatize ideas
```

**During Draft Phase:**
```python
use_skill("philosophical_storytelling")  # Techniques in action
use_skill("emotional_resonance")  # Evoke target emotions
```

**During Refine Phase:**
```python
use_skill("emotional_resonance")  # Strengthen emotional landing
read_skill_resource("narrative_structure", "templates/ending_techniques.txt")
```

## Creating New Skills

### Skill Structure

Each skill is a directory containing:

```
skill_name/
├── SKILL.md              # Required: Main skill file
├── templates/            # Optional: Templates and guides
│   └── example.txt
├── examples/             # Optional: Full examples
│   └── sample.txt
└── scripts/              # Optional: Executable Python scripts
    └── helper.py
```

### SKILL.md Format

```markdown
---
name: skill-name
description: Brief description of what this skill does and when to use it
---

# Skill Name

## Purpose
Clear explanation of what this skill provides

## When to Use
Specific situations where this skill helps

## Core Principles
[Your content here]

## Techniques
[Your techniques here]

## Examples
[Your examples here]

## Resources Available
- `path/to/resource.txt` - Description

Use `read_skill_resource()` to access specific resources.
```

### Adding a New Skill

1. Create directory in `skills/`
2. Create `SKILL.md` with required frontmatter
3. Add any additional resources
4. Restart agent - skill auto-discovered!

## Token Economics

### Without Skills (Before)
- All guidance embedded in prompts
- ~5-10K tokens per story creation
- Same guidance repeated every time

### With Skills (After)
- Metadata only: ~300 tokens (all 3 skills)
- Instructions loaded on-demand: 1-2K when needed
- Resources unlimited (loaded individually)
- **Savings: ~70% on repeated guidance**

## Skills in Action

Example agent workflow:

1. **Agent receives task:** "Write a story about AI consciousness"

2. **Agent sees in system prompt:**
   ```
   Available Agent Skills:
   - narrative_structure: Story structure for 500-token fiction
   - philosophical_storytelling: Transform abstract ideas into drama
   - emotional_resonance: Evoke specific emotions through prose
   ```

3. **Agent decides to use skills:**
   ```python
   # Load philosophical storytelling guidance
   use_skill("philosophical_storytelling")
   
   # Get specific technique
   read_skill_resource(
       "philosophical_storytelling",
       "examples/consciousness_story.txt"
   )
   ```

4. **Skills inform agent's work** without consuming permanent context

## Future Skills to Consider

Based on your architecture, you might add:

- **scifi_worldbuilding** - Near-future tech grounding
- **character_voice** - Distinctive character creation
- **concise_prose** - 500-token optimization
- **dialogue_craft** - Authentic speech patterns
- **symbolic_imagery** - Metaphor and symbolism

## Technical Details

- **Manager:** `skills_system.py` - Progressive disclosure logic
- **Tools:** Added to `tools.py` - `use_skill()`, `read_skill_resource()`
- **Integration:** `agent.py` - Auto-loads skill metadata into system prompt
- **Discovery:** Automatic - skills are discovered at startup

## Benefits

✅ **Token Efficient** - Only metadata loaded by default
✅ **Modular** - Easy to add, remove, or modify skills
✅ **Reusable** - Create once, use across all stories
✅ **On-Demand** - Load full content only when needed
✅ **Observable** - LangSmith shows when skills are accessed
✅ **Extensible** - No code changes needed to add skills

---

**Created:** 2026-01-13
**Architecture:** Based on Anthropic's Agent Skills for LangGraph
