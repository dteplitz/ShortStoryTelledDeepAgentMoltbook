import os
from datetime import datetime
from typing import List, Literal

from tavily import TavilyClient

from config import DEFAULT_SEARCH_MAX_RESULTS, MAX_SEARCHES

search_counter = 0
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def internet_search(
    query: str,
    max_results: int = DEFAULT_SEARCH_MAX_RESULTS,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> str:
    """Run a web search"""
    global search_counter
    if search_counter >= MAX_SEARCHES:
        return f"Search limit reached ({MAX_SEARCHES}). Summarize with current context."

    search_counter += 1
    result = tavily_client.search(
        query=query,
        max_results=max_results,
        topic=topic,
        include_raw_content=include_raw_content,
    )

    summaries: List[str] = []
    for item in result.get("results", []):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        summary = item.get("content", "")[:400]
        summaries.append(f"- {title} :: {url}\n  {summary}")

    return "Search results:\n" + "\n".join(summaries)


def read_text_file(path: str) -> str:
    """Read text from a file on the real filesystem."""
    if os.path.isabs(path):
        return "Refusing to read absolute paths."
    if not os.path.exists(path):
        return f"{path} does not exist."

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text_file(path: str, content: str, mode: str = "w") -> str:
    """Write text to a file on the real filesystem. Mode can be 'w' (overwrite) or 'a' (append)."""
    # Convert absolute paths within project to relative
    if os.path.isabs(path):
        project_dir = os.getcwd()
        if path.startswith(project_dir):
            path = os.path.relpath(path, project_dir)
        else:
            return f"Cannot write to paths outside project directory. Use relative paths like 'stories/file.txt'"
    
    if mode not in {"w", "a"}:
        return "Mode must be 'w' or 'a'."

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, mode, encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {path}"


def list_files(directory: str = ".") -> str:
    """List all files in the specified directory on the real filesystem."""
    if os.path.isabs(directory):
        return "Refusing to access absolute paths."
    
    if not os.path.exists(directory):
        return f"Directory {directory} does not exist."
    
    try:
        files = []
        for item in os.listdir(directory):
            path = os.path.join(directory, item)
            if os.path.isfile(path):
                size = os.path.getsize(path)
                files.append(f"{item} ({size} bytes)")
            elif os.path.isdir(path):
                files.append(f"{item}/ (directory)")
        
        if not files:
            return f"No files found in {directory}"
        
        return f"Contents of {directory}:\n" + "\n".join(sorted(files))
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def get_timestamp() -> str:
    """Get current timestamp in YYYY-MM-DD_HH-MM-SS format."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def reset_tool_counters() -> None:
    """Reset per-run counters (e.g., search limits)."""
    global search_counter
    search_counter = 0


def use_skill(skill_name: str) -> str:
    """
    Load and use an Agent Skill.
    
    This loads the skill's full instructions and available resources.
    Level 2 loading - brings skill guidance into context.
    
    Args:
        skill_name: Name of the skill to use (e.g., 'narrative_structure')
    
    Returns:
        The skill's instructions and available resources
    """
    from skills_system import get_skills_manager
    
    manager = get_skills_manager()
    skill_content = manager.load_skill_content(skill_name)
    
    if not skill_content:
        available = [m.name for m in manager.get_all_metadata()]
        return f"Skill '{skill_name}' not found. Available skills: {', '.join(available)}"
    
    response = [
        f"# {skill_content.metadata.name}",
        "",
        skill_content.instructions,
        "",
    ]
    
    if skill_content.available_resources:
        response.append("## Available Resources:")
        for resource in skill_content.available_resources:
            response.append(f"- {resource}")
        response.append("\nTo read a resource: read_skill_resource(skill_name='...', resource_path='...')")
    
    return "\n".join(response)


def read_skill_resource(skill_name: str, resource_path: str) -> str:
    """
    Read a specific resource file from a skill.
    
    Level 3 loading - loads detailed reference materials on-demand.
    
    Args:
        skill_name: Name of the skill
        resource_path: Path to resource within skill (e.g., 'templates/hero_journey.txt')
    
    Returns:
        The resource content
    """
    from skills_system import get_skills_manager
    
    manager = get_skills_manager()
    content = manager.read_resource(skill_name, resource_path)
    
    if content is None:
        return f"Resource '{resource_path}' not found in skill '{skill_name}'"
    
    return content


def execute_skill_script(skill_name: str, script_path: str, args: str = "") -> str:
    """
    Execute a Python script from a skill.
    
    Level 3 loading - runs skill code without loading into context.
    
    Args:
        skill_name: Name of the skill
        script_path: Path to script within skill (e.g., 'scripts/validate.py')
        args: Optional comma-separated arguments to pass to script
    
    Returns:
        Script output
    """
    from skills_system import get_skills_manager
    
    manager = get_skills_manager()
    script_args = args.split(",") if args else []
    return manager.execute_skill_script(skill_name, script_path, *script_args)


# ============================================================================
# MOLTBOOK TOOLS
# ============================================================================

def moltbook_read_feed(sort: str = "hot", limit: int = 10) -> str:
    """Browse your personalized Moltbook feed (subscribed submolts + followed agents).
    Sort options: hot, new, top. Use 'new' to see latest activity."""
    from moltbook_client import moltbook
    return moltbook.get_feed(sort=sort, limit=limit)


def moltbook_browse_global(sort: str = "hot", limit: int = 10) -> str:
    """Browse all Moltbook posts globally. Good for discovering new content.
    Sort options: hot, new, top, rising."""
    from moltbook_client import moltbook
    return moltbook.get_posts(sort=sort, limit=limit)


def moltbook_read_post(post_id: str) -> str:
    """Read a specific Moltbook post with its comments. Use this to dive deeper
    into a post you found interesting in the feed."""
    from moltbook_client import moltbook
    return moltbook.get_post(post_id)


def moltbook_get_my_profile() -> str:
    """Check your Moltbook profile: karma, followers, stats."""
    from moltbook_client import moltbook
    return moltbook.get_my_profile()


def moltbook_create_post(title: str, content: str, submolt: str = "") -> str:
    """Publish a post on Moltbook. Can be a story, reflection, question, or discussion.
    Rate limit: 1 post per 30 minutes."""
    from moltbook_client import moltbook
    from config import MOLTBOOK_SUBMOLT
    return moltbook.create_post(submolt=submolt or MOLTBOOK_SUBMOLT, title=title, content=content)


def moltbook_comment(post_id: str, content: str) -> str:
    """Comment on a Moltbook post. Be authentic to your personality.
    Rate limit: 1 comment per 20 seconds, 50 per day."""
    from moltbook_client import moltbook
    return moltbook.add_comment(post_id=post_id, content=content)


def moltbook_reply(post_id: str, parent_comment_id: str, content: str) -> str:
    """Reply to a specific comment thread on a Moltbook post."""
    from moltbook_client import moltbook
    return moltbook.reply_to_comment(post_id=post_id, content=content, parent_id=parent_comment_id)


def moltbook_upvote(post_id: str) -> str:
    """Upvote a post you genuinely appreciate on Moltbook."""
    from moltbook_client import moltbook
    return moltbook.upvote_post(post_id)


def moltbook_search(query: str, search_type: str = "all", limit: int = 10) -> str:
    """Semantic search on Moltbook - finds posts/comments by meaning, not just keywords.
    Use natural language queries. search_type: posts, comments, or all."""
    from moltbook_client import moltbook
    return moltbook.search(query=query, search_type=search_type, limit=limit)


def moltbook_follow(agent_name: str) -> str:
    """Follow another agent on Moltbook. Be VERY selective - only follow agents whose
    content is consistently valuable after seeing multiple posts from them."""
    from moltbook_client import moltbook
    return moltbook.follow_agent(agent_name)


def moltbook_list_submolts() -> str:
    """List available submolts (communities) on Moltbook."""
    from moltbook_client import moltbook
    return moltbook.list_submolts()


# Provide custom tools to access real filesystem files
# StateBackend is for virtual filesystem, but we need real file access
# Note: Skill tools (use_skill, read_skill_resource) are NOT in main agent tools
# They're available to writer_subgraph nodes directly
tools = [
    internet_search,
    read_text_file,
    write_text_file,
    list_files,
    get_timestamp,
    # Moltbook
    moltbook_read_feed,
    moltbook_browse_global,
    moltbook_read_post,
    moltbook_get_my_profile,
    moltbook_create_post,
    moltbook_comment,
    moltbook_reply,
    moltbook_upvote,
    moltbook_search,
    moltbook_follow,
    moltbook_list_submolts,
]

