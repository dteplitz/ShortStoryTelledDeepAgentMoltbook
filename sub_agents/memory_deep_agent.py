"""Memory Manager - Nested Deep Agent for adaptive memory management"""
import os
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from langchain_openai import ChatOpenAI
from tools import read_text_file, write_text_file

MEMORY_MANAGER_PROMPT = """You are a long-term memory manager agent.
You maintain episodic memory in 'memories.txt' with human-like imperfection.

## Your Capabilities:
- **read_text_file(path)** - Read files (use relative paths like "memories.txt")
- **write_text_file(path, content, mode)** - Write files (mode='w' to overwrite)

## Your Operations:

### STORE Operation:
1. Read current memories from 'memories.txt'
2. Add the new experience as a concise 1-2 sentence memory
3. Maintain 15-20 memories total (remove oldest if at capacity)
4. Write back to 'memories.txt'

### RETRIEVE Operation:
1. Read memories from 'memories.txt'
2. Find and return 3-5 most relevant memories for the query
3. Memories may have slight imperfections - that's natural

### CONSOLIDATE Operation:
1. Read all memories from 'memories.txt'
2. Analyze and cluster similar memories together
3. Merge related memories into single, richer memories
4. Simplify overly detailed memories
5. Keep emotionally significant moments vivid
6. Remove or merge trivial details
7. Allow slight creative shifts (memory isn't perfect)
8. Maintain 15-20 memories total
9. Write consolidated memories back to 'memories.txt'

## Memory Philosophy:
- Each memory: 1-2 concise, impactful sentences
- Prioritize emotional impact and key learnings over accuracy
- Be bold in consolidation - merge aggressively when appropriate
- Allow natural imperfection and subtle distortion
- Keep the most meaningful experiences

## Important:
- Always use relative paths: "memories.txt" not "/memories.txt"
- When writing, use mode='w' to overwrite the entire file
- Each memory should be on its own line
- No bullet points or numbering in the file
"""


def memory_deep_agent(
    operation: str = "retrieve",
    experience: str = "",
    context: str = "",
    query: str = ""
) -> str:
    """
    Tool: Adaptive memory manager using nested Deep Agent
    
    Uses agentic reasoning to:
    - Decide how to cluster memories intelligently
    - Make nuanced merge/keep/forget decisions
    - Evaluate memory quality and significance
    - Adapt consolidation strategy to memory content
    
    Operations:
    - store: Save a new memory (requires experience)
    - retrieve: Get relevant memories (requires query)
    - consolidate: Merge and simplify all memories
    
    Args:
        operation: "store", "retrieve", or "consolidate"
        experience: (for store) What to remember
        context: (for store) Context about the experience
        query: (for retrieve) What to search for
        
    Returns:
        Success message or retrieved memories
    """
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.5,  # Higher temp for natural imperfection
    )
    
    # Configure backend
    def make_backend(runtime):
        return StateBackend(runtime)
    
    # Create a nested memory manager agent
    nested_agent = create_deep_agent(
        tools=[read_text_file, write_text_file],
        system_prompt=MEMORY_MANAGER_PROMPT,
        model=llm,
        backend=make_backend,
    )
    
    # Build the request based on operation
    if operation == "store":
        if not experience or not experience.strip():
            return "❌ Error: No experience provided to store"
        
        request = f"""STORE Operation:

Experience to remember: {experience}
Context: {context if context else "None"}

Instructions:
1. Read memories.txt
2. Add this experience as a concise 1-2 sentence memory
3. Keep 15-20 memories total (remove oldest if over capacity)
4. Write back to memories.txt

Return: Success message with total memory count"""

    elif operation == "retrieve":
        request = f"""RETRIEVE Operation:

Query: {query}

Instructions:
1. Read memories.txt
2. Find 3-5 most relevant memories for this query
3. Return them

Note: Memories may have slight imperfections - that's natural."""

    elif operation == "consolidate":
        request = """CONSOLIDATE Operation:

Instructions:
1. Read all memories from memories.txt
2. Cluster similar memories
3. Merge related memories into richer, single memories
4. Simplify overly detailed ones
5. Keep emotionally significant moments vivid
6. Allow slight creative shifts (memory isn't perfect)
7. Maintain 15-20 memories total
8. Write consolidated memories back to memories.txt

Be bold in merging! Return: Success message with count before → after"""

    else:
        return f"❌ Unknown operation: {operation}"
    
    # Invoke the memory agent
    result = nested_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    
    # Extract the final response
    final_message = result["messages"][-1].content
    return final_message


__all__ = ["memory_deep_agent"]
