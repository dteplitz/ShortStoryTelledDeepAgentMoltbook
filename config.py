import os

from dotenv import load_dotenv

# Load environment variables (e.g., OPENAI_API_KEY, TAVILY_API_KEY, OPENAI_MODEL)
load_dotenv()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "512"))
MAX_SEARCHES = int(os.getenv("MAX_SEARCHES", "3"))
DEFAULT_SEARCH_MAX_RESULTS = int(os.getenv("DEFAULT_SEARCH_MAX_RESULTS", "5"))

# LangSmith Configuration for observability
LANGSMITH_ENABLED = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "story-writer-agent")

if LANGSMITH_ENABLED and os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    print(f"✅ LangSmith tracing enabled (project: {LANGSMITH_PROJECT})")
elif LANGSMITH_ENABLED:
    print("⚠️  LANGSMITH_TRACING=true but LANGCHAIN_API_KEY not found")
