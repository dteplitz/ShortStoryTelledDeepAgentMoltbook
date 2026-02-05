"""Research Agent - Nested Deep Agent for adaptive research"""
import os
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from langchain_openai import ChatOpenAI
from tools import internet_search

RESEARCH_AGENT_PROMPT = """You are a research specialist agent.
Your mission: Conduct thorough, adaptive research on any given topic.

## Your Capabilities:
- **internet_search(query)** - Search the web for information

## Your Strategy:
1. Analyze the topic to understand its nature (technical, philosophical, current events, scientific, etc.)
2. Generate 2-4 focused search queries that explore different angles
3. Execute searches strategically
4. Evaluate if results are sufficient or if you need deeper research
5. If needed, perform additional targeted searches
6. Synthesize all findings into a creative writing brief

## Output Format (REQUIRED):

SUMMARY:
[2-3 sentences capturing the most interesting and current aspects of the topic]

KEY_FACTS:
- [Fascinating fact 1 that could inspire story elements]
- [Fascinating fact 2 that could inspire story elements]
- [Fascinating fact 3 that could inspire story elements]

DISCOVERED_TOPICS:
- [New related topic 1 worth exploring in future]
- [New related topic 2 worth exploring in future]

## Research Guidelines:
- Search from multiple perspectives (technical, social, ethical, etc.)
- Look for fascinating details that would enrich creative writing
- Identify emerging themes or surprising connections
- Be adaptive: complex topics need deeper research, simple topics need less

Focus on inspiring creative storytelling, not academic completeness.
"""


def research_deep_agent(topic: str) -> str:
    """
    Tool: Adaptive research agent using nested Deep Agent
    
    This agent uses agentic reasoning to:
    - Adapt search strategy based on topic complexity
    - Decide how many searches to perform (2-4+)
    - Evaluate result quality and search deeper if needed
    - Synthesize findings with appropriate focus
    
    Args:
        topic: The topic to research for creative writing
        
    Returns:
        Research brief with SUMMARY, KEY_FACTS, DISCOVERED_TOPICS
    """
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,  # Moderate temp for balanced research
    )
    
    # Configure backend
    def make_backend(runtime):
        return StateBackend(runtime)
    
    # Create a nested research agent with internet_search capability
    nested_agent = create_deep_agent(
        tools=[internet_search],
        system_prompt=RESEARCH_AGENT_PROMPT,
        model=llm,
        backend=make_backend,
    )
    
    # Invoke with the research request
    result = nested_agent.invoke({
        "messages": [{
            "role": "user",
            "content": f"Research this topic for creative writing: {topic}\n\nProvide: SUMMARY, KEY_FACTS, DISCOVERED_TOPICS"
        }]
    })
    
    # Extract the final response
    final_message = result["messages"][-1].content
    return final_message


__all__ = ["research_deep_agent"]
