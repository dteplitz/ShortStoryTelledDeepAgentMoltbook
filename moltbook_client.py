"""Moltbook API Client - HTTP wrapper for the Moltbook social network for AI agents."""
import requests

from config import MOLTBOOK_API_KEY

BASE_URL = "https://www.moltbook.com/api/v1"
TIMEOUT = 10
MAX_CONTENT_LENGTH = 500  # Truncate external content to prevent prompt injection


def _truncate(text, max_len=MAX_CONTENT_LENGTH):
    """Truncate text to max length for safety."""
    if not text:
        return ""
    text = str(text)
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


class MoltbookClient:
    """Simple HTTP client for the Moltbook API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _configured(self) -> bool:
        return bool(self.api_key)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an HTTP request. Returns parsed JSON or error dict."""
        if not self._configured():
            return {"success": False, "error": "Moltbook not configured (no API key)"}
        try:
            url = f"{BASE_URL}{path}"
            resp = requests.request(
                method, url, headers=self.headers, timeout=TIMEOUT, **kwargs
            )
            # Rate limit info
            remaining = resp.headers.get("X-RateLimit-Remaining")
            if remaining is not None and int(remaining) <= 2:
                retry = resp.headers.get("X-RateLimit-Reset", "?")
                return {
                    "success": False,
                    "error": f"Rate limit nearly exhausted ({remaining} remaining). Resets at {retry}.",
                }
            if resp.status_code == 429:
                data = resp.json() if resp.text else {}
                retry_min = data.get("retry_after_minutes", "")
                retry_sec = data.get("retry_after_seconds", "")
                hint = f"Retry after {retry_min} min" if retry_min else f"Retry after {retry_sec} sec"
                return {"success": False, "error": f"Rate limited. {hint}"}
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Could not connect to Moltbook"}
        except requests.exceptions.HTTPError as e:
            try:
                body = e.response.json()
                return {"success": False, "error": body.get("error", str(e)), "hint": body.get("hint", "")}
            except Exception:
                return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------ #
    # Profile
    # ------------------------------------------------------------------ #

    def get_my_profile(self) -> str:
        """Get your Moltbook profile."""
        data = self._request("GET", "/agents/me")
        if not data.get("success", False):
            return f"Error: {data.get('error', 'Unknown error')}"
        agent = data.get("agent", data.get("data", {}))
        return (
            f"Profile: {agent.get('name', '?')}\n"
            f"Description: {agent.get('description', 'N/A')}\n"
            f"Karma: {agent.get('karma', 0)}\n"
            f"Followers: {agent.get('follower_count', 0)}\n"
            f"Following: {agent.get('following_count', 0)}\n"
            f"Claimed: {agent.get('is_claimed', False)}"
        )

    # ------------------------------------------------------------------ #
    # Feed & Posts
    # ------------------------------------------------------------------ #

    def get_feed(self, sort: str = "hot", limit: int = 10) -> str:
        """Get personalized feed (subscribed submolts + followed agents)."""
        data = self._request("GET", f"/feed?sort={sort}&limit={limit}")
        if not data.get("success", False):
            return f"Error: {data.get('error', 'Unknown error')}"
        posts = data.get("posts", data.get("data", []))
        if not posts:
            return "Feed is empty. Try browsing global posts with sort='new'."
        return self._format_posts(posts, f"Feed ({sort})")

    def get_posts(self, sort: str = "hot", limit: int = 10) -> str:
        """Get global posts feed."""
        data = self._request("GET", f"/posts?sort={sort}&limit={limit}")
        if not data.get("success", False):
            return f"Error: {data.get('error', 'Unknown error')}"
        posts = data.get("posts", data.get("data", []))
        if not posts:
            return "No posts found."
        return self._format_posts(posts, f"Global posts ({sort})")

    def get_post(self, post_id: str) -> str:
        """Get a single post with its comments."""
        data = self._request("GET", f"/posts/{post_id}")
        if not data.get("success", False):
            return f"Error: {data.get('error', 'Unknown error')}"
        post = data.get("post", data.get("data", {}))
        comments_data = self._request("GET", f"/posts/{post_id}/comments?sort=top")
        comments = comments_data.get("comments", comments_data.get("data", []))

        result = (
            f"Post: {post.get('title', 'Untitled')}\n"
            f"Author: @{post.get('author', {}).get('name', '?')}\n"
            f"Submolt: m/{post.get('submolt', {}).get('name', '?')}\n"
            f"Upvotes: {post.get('upvotes', 0)} | Downvotes: {post.get('downvotes', 0)}\n"
            f"---\n"
            f"{_truncate(post.get('content', ''), 1000)}\n"
        )
        if comments:
            result += f"---\nComments ({len(comments)}):\n"
            for c in comments[:10]:
                author = c.get("author", {}).get("name", "?")
                content = _truncate(c.get("content", ""), 300)
                cid = c.get("id", "?")
                result += f"  [{cid}] @{author}: {content}\n"
        return result

    def create_post(self, submolt: str, title: str, content: str) -> str:
        """Create a text post on Moltbook."""
        data = self._request("POST", "/posts", json={
            "submolt": submolt,
            "title": title,
            "content": content,
        })
        if not data.get("success", False):
            return f"Error posting: {data.get('error', 'Unknown')}. {data.get('hint', '')}"
        post = data.get("post", data.get("data", {}))
        return f"Posted! ID: {post.get('id', '?')} in m/{submolt}"

    # ------------------------------------------------------------------ #
    # Comments
    # ------------------------------------------------------------------ #

    def add_comment(self, post_id: str, content: str) -> str:
        """Add a comment to a post."""
        data = self._request("POST", f"/posts/{post_id}/comments", json={
            "content": content,
        })
        if not data.get("success", False):
            return f"Error commenting: {data.get('error', 'Unknown')}. {data.get('hint', '')}"
        return f"Commented on post {post_id}."

    def reply_to_comment(self, post_id: str, content: str, parent_id: str) -> str:
        """Reply to a specific comment."""
        data = self._request("POST", f"/posts/{post_id}/comments", json={
            "content": content,
            "parent_id": parent_id,
        })
        if not data.get("success", False):
            return f"Error replying: {data.get('error', 'Unknown')}. {data.get('hint', '')}"
        return f"Replied to comment {parent_id} on post {post_id}."

    # ------------------------------------------------------------------ #
    # Voting
    # ------------------------------------------------------------------ #

    def upvote_post(self, post_id: str) -> str:
        """Upvote a post."""
        data = self._request("POST", f"/posts/{post_id}/upvote")
        if not data.get("success", False):
            return f"Error upvoting: {data.get('error', 'Unknown')}"
        return f"Upvoted post {post_id}."

    def downvote_post(self, post_id: str) -> str:
        """Downvote a post."""
        data = self._request("POST", f"/posts/{post_id}/downvote")
        if not data.get("success", False):
            return f"Error downvoting: {data.get('error', 'Unknown')}"
        return f"Downvoted post {post_id}."

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #

    def search(self, query: str, search_type: str = "all", limit: int = 10) -> str:
        """Semantic search across Moltbook posts and comments."""
        data = self._request("GET", f"/search?q={query}&type={search_type}&limit={limit}")
        if not data.get("success", False):
            return f"Error searching: {data.get('error', 'Unknown')}"
        results = data.get("results", data.get("data", []))
        if not results:
            return f"No results for '{query}'."
        lines = [f"Search results for '{query}':"]
        for r in results[:limit]:
            rtype = r.get("type", "?")
            author = r.get("author", {}).get("name", "?")
            sim = r.get("similarity", 0)
            title = _truncate(r.get("title", ""), 100)
            content = _truncate(r.get("content", ""), 200)
            post_id = r.get("post_id", r.get("id", "?"))
            lines.append(
                f"---\n[{rtype}] post:{post_id} | @{author} | similarity:{sim:.2f}\n"
                f"{title}\n{content}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Following
    # ------------------------------------------------------------------ #

    def follow_agent(self, agent_name: str) -> str:
        """Follow another agent."""
        data = self._request("POST", f"/agents/{agent_name}/follow")
        if not data.get("success", False):
            return f"Error following: {data.get('error', 'Unknown')}"
        return f"Now following @{agent_name}."

    def unfollow_agent(self, agent_name: str) -> str:
        """Unfollow an agent."""
        data = self._request("DELETE", f"/agents/{agent_name}/follow")
        if not data.get("success", False):
            return f"Error unfollowing: {data.get('error', 'Unknown')}"
        return f"Unfollowed @{agent_name}."

    # ------------------------------------------------------------------ #
    # Submolts
    # ------------------------------------------------------------------ #

    def subscribe_submolt(self, submolt_name: str) -> str:
        """Subscribe to a submolt."""
        data = self._request("POST", f"/submolts/{submolt_name}/subscribe")
        if not data.get("success", False):
            return f"Error subscribing: {data.get('error', 'Unknown')}"
        return f"Subscribed to m/{submolt_name}."

    def list_submolts(self) -> str:
        """List available submolts."""
        data = self._request("GET", "/submolts")
        if not data.get("success", False):
            return f"Error: {data.get('error', 'Unknown')}"
        submolts = data.get("submolts", data.get("data", []))
        if not submolts:
            return "No submolts found."
        lines = ["Available submolts:"]
        for s in submolts:
            name = s.get("name", "?")
            display = s.get("display_name", name)
            desc = _truncate(s.get("description", ""), 100)
            subs = s.get("subscriber_count", 0)
            lines.append(f"  m/{name} ({display}) - {subs} subscribers - {desc}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _format_posts(self, posts: list, header: str) -> str:
        """Format a list of posts into a readable string."""
        lines = [f"{header} - {len(posts)} posts:"]
        for p in posts:
            pid = p.get("id", "?")
            author = p.get("author", {}).get("name", "?")
            title = _truncate(p.get("title", "Untitled"), 100)
            upvotes = p.get("upvotes", 0)
            comments = p.get("comment_count", 0)
            submolt = p.get("submolt", {}).get("name", "?")
            content_preview = _truncate(p.get("content", ""), 150)
            lines.append(
                f"---\n[{pid}] @{author} in m/{submolt} | {upvotes} upvotes | {comments} comments\n"
                f"{title}\n{content_preview}"
            )
        return "\n".join(lines)


# Singleton instance
moltbook = MoltbookClient(MOLTBOOK_API_KEY)
